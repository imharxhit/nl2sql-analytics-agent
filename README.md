# NL2SQL Data Audit & Analytics Agent

An autonomous Text-to-SQL agent built with **Python**, **LangGraph**, and **SQLite / PostgreSQL** that translates natural-language finance and operations questions into verified read-only SQL queries, self-corrects execution errors using schema feedback, and flags billing/cost anomalies.

## Background & Motivation
During my internship auditing infrastructure project metrics and WIP billing logs with SQL, I noticed how much time engineers and analysts spent writing repetitive multi-table joins and variance checks. I built this agent so non-technical stakeholders can ask questions in plain English while enforcing strict read-only SQL guardrails and automated retry logic on syntax or column errors.

## How AI & Agentic Workflows Are Used
- **Schema-Aware Tool Calling**: Injects compact DDL table schemas and foreign-key relationships into the system prompt so the LLM generates dialect-accurate SQL (CTEs, window functions, aggregations).
- **Read-Only AST Security Guardrail**: Parses generated SQL before execution to block destructive statements (`DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`, `PRAGMA`) and automatically appends a safety `LIMIT`.
- **Self-Correction Loop (LangGraph State Machine)**: If `sqlite3` raises an `OperationalError` (such as an invalid column name or ambiguous join), the agent captures the traceback, feeds it back to the LLM reflection node, and repairs the query (up to 3 retries).

## Running Tests
```bash
pip install -r requirements.txt
pytest -v
```
