from typing import Any

from app.config import Settings
from app.db.allowlist import TableAllowlist
from app.db.connection import Database
from app.security.query_guard import (
    clamp_limit,
    client_error,
    filter_sensitive_columns,
    filter_sensitive_rows,
)
from app.tools.health import safe_success

PROSPECTS_TABLE = "prospects"


async def search_prospects(
    search: str,
    db: Database,
    allowlist: TableAllowlist,
    settings: Settings,
    limit: int | None = None,
) -> dict[str, Any]:
    try:
        allowlist.require_allowed(PROSPECTS_TABLE)
        row_limit = clamp_limit(limit, settings.max_rows)
        pattern = f"%{search}%"
        rows = await db.fetch(
            """
            SELECT *
            FROM prospects
            WHERE first_name ILIKE $1
               OR last_name ILIKE $1
               OR email ILIKE $1
               OR company ILIKE $1
            ORDER BY created_at DESC NULLS LAST
            LIMIT $2
            """,
            pattern,
            row_limit,
        )
    except ValueError:
        return client_error("Table is not allowed.")
    except Exception:
        return client_error("Could not search prospects.")

    return safe_success({"limit": row_limit, "records": filter_sensitive_rows(rows)})


async def get_prospect_by_id(
    prospect_id: int,
    db: Database,
    allowlist: TableAllowlist,
) -> dict[str, Any]:
    try:
        allowlist.require_allowed(PROSPECTS_TABLE)
        row = await db.fetchrow(
            """
            SELECT *
            FROM prospects
            WHERE id = $1
            LIMIT 1
            """,
            prospect_id,
        )
    except ValueError:
        return client_error("Table is not allowed.")
    except Exception:
        return client_error("Could not fetch prospect.")

    return safe_success({"record": filter_sensitive_columns(row) if row else None})

