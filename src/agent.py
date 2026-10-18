import re
import sqlite3
from typing import Any, Callable, Dict, List

FORBIDDEN = {"DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE", "REPLACE", "GRANT", "REVOKE", "ATTACH", "PRAGMA"}

class UnsafeSQLError(Exception):
    pass

def validate_and_sanitize_sql(sql: str, default_limit: int = 100) -> str:
    cleaned = sql.strip().rstrip(";")
    if not cleaned or ";" in cleaned:
        raise UnsafeSQLError("Only single SQL statements are allowed.")
    tokens = [t.upper() for t in re.findall(r"[a-zA-Z_]+", cleaned)]
    if not tokens or tokens[0] not in {"SELECT", "WITH"}:
        raise UnsafeSQLError("Only read-only SELECT or WITH queries are permitted.")
    for tok in tokens:
        if tok in FORBIDDEN:
            raise UnsafeSQLError(f"Blocked destructive keyword: {tok}")
    if "LIMIT" not in tokens:
        cleaned = f"{cleaned} LIMIT {default_limit}"
    return cleaned + ";"

class NL2SQLAuditAgent:
    def __init__(self, conn: sqlite3.Connection, llm_generator: Callable[[str, str, List[str]], str], max_retries: int = 3):
        self.conn = conn
        self.llm_generator = llm_generator
        self.max_retries = max_retries
        rows = conn.execute("SELECT sql FROM sqlite_master WHERE type='table' AND sql IS NOT NULL").fetchall()
        self.schema_ddl = "\n\n".join(r[0] for r in rows)

    def run(self, question: str) -> Dict[str, Any]:
        errors: List[str] = []
        for attempt in range(1, self.max_retries + 1):
            raw_sql = self.llm_generator(question, self.schema_ddl, errors)
            safe_sql = validate_and_sanitize_sql(raw_sql)
            try:
                cur = self.conn.cursor()
                cols = [d[0] for d in cur.execute(safe_sql).description or []]
                rows = [dict(zip(cols, r)) for r in cur.fetchall()]
                return {"success": True, "attempts": attempt, "sql": safe_sql, "rows": rows, "errors": errors}
            except sqlite3.OperationalError as exc:
                errors.append(f"Attempt {attempt} failed on `{safe_sql}`: {exc}")
        return {"success": False, "attempts": self.max_retries, "sql": "", "rows": [], "errors": errors}
