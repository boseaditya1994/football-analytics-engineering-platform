"""One-time/idempotent Snowflake object setup, run from version-controlled SQL.

Reads connection details from environment variables (via .env). Never prints
credential values - only statement progress and object names.

Usage:
    python snowflake/run_setup.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

SQL_FILES = [
    "setup/01_database_and_warehouse.sql",
    "setup/02_schemas.sql",
    "setup/03_roles_and_grants.sql",
    "objects/01_audit_tables.sql",
    "objects/02_raw_tables.sql",
]


def _require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        print(f"Missing required env var: {name}. Fill it in .env first.", file=sys.stderr)
        sys.exit(1)
    return value


def _split_statements(sql_text: str) -> list[str]:
    # Drop full-line comments before splitting, so a commented-out statement
    # (e.g. the manual GRANT ROLE ... TO USER line) is never executed.
    active_lines = [
        line for line in sql_text.splitlines() if not line.strip().startswith("--")
    ]
    statements = []
    for raw_statement in "\n".join(active_lines).split(";"):
        statement = raw_statement.strip()
        if statement:
            statements.append(statement)
    return statements


def main() -> None:
    load_dotenv()
    import snowflake.connector

    account = _require_env("SNOWFLAKE_ACCOUNT")
    user = _require_env("SNOWFLAKE_USER")
    password = _require_env("SNOWFLAKE_PASSWORD")
    role = os.environ.get("SNOWFLAKE_ROLE", "ACCOUNTADMIN")
    warehouse = os.environ.get("SNOWFLAKE_WAREHOUSE")

    print(f"Connecting to Snowflake account (user={user}, role={role})...")
    conn = snowflake.connector.connect(
        account=account,
        user=user,
        password=password,
        role=role,
        warehouse=warehouse,
    )

    base_dir = Path(__file__).parent
    try:
        cursor = conn.cursor()
        for relative_path in SQL_FILES:
            sql_path = base_dir / relative_path
            print(f"\n--- Running {relative_path} ---")
            statements = _split_statements(sql_path.read_text(encoding="utf-8"))
            for statement in statements:
                first_line = statement.splitlines()[0][:80]
                print(f"  > {first_line}")
                cursor.execute(statement)
        print("\nSnowflake setup complete.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
