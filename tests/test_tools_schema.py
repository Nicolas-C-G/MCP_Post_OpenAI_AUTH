import pytest

from app.config import Settings
from app.db.allowlist import TableAllowlist
from app.tools.schema import describe_table, get_recent_records, list_allowed_tables


class MockDb:
    def __init__(self, rows=None, fail: bool = False) -> None:
        self.rows = rows or []
        self.fail = fail
        self.calls = []

    async def fetch(self, query: str, *args):
        self.calls.append((query, args))
        if self.fail:
            raise RuntimeError("raw error")
        return self.rows


def test_list_allowed_tables() -> None:
    allowlist = TableAllowlist(Settings(ALLOWED_TABLES="prospects,campaign_metrics"))
    assert list_allowed_tables(allowlist) == {
        "status": "ok",
        "data": {"tables": ["campaign_metrics", "prospects"]},
    }


@pytest.mark.asyncio
async def test_describe_table_filters_sensitive_columns() -> None:
    db = MockDb(
        [
            {"column_name": "id", "data_type": "integer", "is_nullable": "NO"},
            {"column_name": "access_token", "data_type": "text", "is_nullable": "YES"},
        ]
    )
    allowlist = TableAllowlist(Settings(ALLOWED_TABLES="prospects"))

    result = await describe_table("prospects", db, allowlist)

    assert result["status"] == "ok"
    assert result["data"]["columns"] == [
        {"name": "id", "data_type": "integer", "is_nullable": "NO"}
    ]


@pytest.mark.asyncio
async def test_get_recent_records_enforces_limit_and_filters_sensitive_data() -> None:
    db = MockDb([{"id": 1, "email": "a@example.com", "password": "hidden"}])
    settings = Settings(ALLOWED_TABLES="prospects", MAX_ROWS=10)
    allowlist = TableAllowlist(settings)

    result = await get_recent_records("prospects", db, allowlist, settings, limit=500)

    assert db.calls[0][1] == (10,)
    assert result["data"]["limit"] == 10
    assert result["data"]["records"] == [{"id": 1, "email": "a@example.com"}]


@pytest.mark.asyncio
async def test_schema_tool_safe_error_response() -> None:
    db = MockDb(fail=True)
    allowlist = TableAllowlist(Settings(ALLOWED_TABLES="prospects"))

    assert await describe_table("prospects", db, allowlist) == {
        "status": "error",
        "message": "Could not describe table.",
    }
