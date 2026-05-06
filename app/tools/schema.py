from typing import Any

from app.config import Settings
from app.db.allowlist import TableAllowlist
from app.db.connection import Database
from app.security.query_guard import client_error, is_sensitive_column
from app.tools.health import safe_success


def list_allowed_tables(allowlist: TableAllowlist) -> dict[str, Any]:
    return safe_success({"tables": allowlist.list_tables()})


async def describe_table(
    table_name: str,
    db: Database,
    allowlist: TableAllowlist,
) -> dict[str, Any]:
    try:
        allowlist.require_allowed(table_name)
        rows = await db.fetch(
            """
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = $1
            ORDER BY ordinal_position
            """,
            table_name,
        )
    except ValueError:
        return client_error("Table is not allowed.")
    except Exception:
        return client_error("Could not describe table.")

    safe_columns = [
        {
            "name": row["column_name"],
            "data_type": row["data_type"],
            "is_nullable": row["is_nullable"],
        }
        for row in rows
        if not is_sensitive_column(row["column_name"])
    ]
    return safe_success({"table": table_name, "columns": safe_columns})


async def get_recent_records(
    table_name: str,
    db: Database,
    allowlist: TableAllowlist,
    settings: Settings,
    limit: int | None = None,
) -> dict[str, Any]:
    from app.security.query_guard import clamp_limit, filter_sensitive_rows, quote_identifier

    try:
        allowed_table = allowlist.require_allowed(table_name)
        safe_table = quote_identifier(allowed_table)
        row_limit = clamp_limit(limit, settings.max_rows)
        rows = await db.fetch(f"SELECT * FROM {safe_table} LIMIT $1", row_limit)
    except ValueError:
        return client_error("Table is not allowed.")
    except Exception:
        return client_error("Could not fetch records.")

    return safe_success(
        {"table": table_name, "limit": row_limit, "records": filter_sensitive_rows(rows)}
    )
