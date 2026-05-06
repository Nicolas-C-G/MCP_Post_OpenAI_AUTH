import pytest

from app.tools.health import db_connection_check, health_check


@pytest.mark.asyncio
async def test_health_check() -> None:
    assert await health_check() == {"status": "ok", "message": "MCP server is healthy."}


@pytest.mark.asyncio
async def test_db_connection_check_safe_error() -> None:
    class FailingDb:
        async def execute_check(self) -> bool:
            raise RuntimeError("connection details should not leak")

    assert await db_connection_check(FailingDb()) == {
        "status": "error",
        "message": "Database connection failed.",
    }

