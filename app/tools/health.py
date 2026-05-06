from typing import Any

from app.db.connection import Database
from app.security.query_guard import client_error


async def health_check() -> dict[str, str]:
    return {"status": "ok", "message": "MCP server is healthy."}


async def db_connection_check(db: Database) -> dict[str, str]:
    try:
        is_connected = await db.execute_check()
    except Exception:
        return client_error("Database connection failed.")

    if not is_connected:
        return client_error("Database connection failed.")
    return {"status": "ok", "message": "Database connection succeeded."}


def safe_success(data: Any) -> dict[str, Any]:
    return {"status": "ok", "data": data}

