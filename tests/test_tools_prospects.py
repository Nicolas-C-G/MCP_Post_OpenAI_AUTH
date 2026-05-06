import pytest

from app.config import Settings
from app.db.allowlist import TableAllowlist
from app.tools.prospects import get_prospect_by_id, search_prospects


class MockDb:
    def __init__(self, rows=None, row=None, fail: bool = False) -> None:
        self.rows = rows or []
        self.row = row
        self.fail = fail
        self.fetch_calls = []
        self.fetchrow_calls = []

    async def fetch(self, query: str, *args):
        self.fetch_calls.append((query, args))
        if self.fail:
            raise RuntimeError("raw database error")
        return self.rows

    async def fetchrow(self, query: str, *args):
        self.fetchrow_calls.append((query, args))
        if self.fail:
            raise RuntimeError("raw database error")
        return self.row


@pytest.mark.asyncio
async def test_search_prospects_with_mocked_database_response() -> None:
    settings = Settings(ALLOWED_TABLES="prospects", MAX_ROWS=5)
    allowlist = TableAllowlist(settings)
    db = MockDb([{"id": 1, "first_name": "Ada", "token": "hidden"}])

    result = await search_prospects("Ada", db, allowlist, settings, limit=50)

    assert db.fetch_calls[0][1] == ("%Ada%", 5)
    assert result == {
        "status": "ok",
        "data": {"limit": 5, "records": [{"id": 1, "first_name": "Ada"}]},
    }


@pytest.mark.asyncio
async def test_get_prospect_by_id_with_mocked_database_response() -> None:
    settings = Settings(ALLOWED_TABLES="prospects")
    allowlist = TableAllowlist(settings)
    db = MockDb(row={"id": 7, "email": "ada@example.com", "secret_note": "hidden"})

    result = await get_prospect_by_id(7, db, allowlist)

    assert db.fetchrow_calls[0][1] == (7,)
    assert result == {
        "status": "ok",
        "data": {"record": {"id": 7, "email": "ada@example.com"}},
    }


@pytest.mark.asyncio
async def test_prospect_tools_safe_error_response() -> None:
    settings = Settings(ALLOWED_TABLES="prospects")
    allowlist = TableAllowlist(settings)
    db = MockDb(fail=True)

    assert await search_prospects("Ada", db, allowlist, settings) == {
        "status": "error",
        "message": "Could not search prospects.",
    }


@pytest.mark.asyncio
async def test_prospect_table_must_be_allowed() -> None:
    settings = Settings(ALLOWED_TABLES="campaign_metrics")
    allowlist = TableAllowlist(settings)
    db = MockDb()

    assert await get_prospect_by_id(1, db, allowlist) == {
        "status": "error",
        "message": "Table is not allowed.",
    }

