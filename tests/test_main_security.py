import pytest

from app.main import mcp


@pytest.mark.asyncio
async def test_mcp_does_not_expose_arbitrary_sql_tools() -> None:
    disallowed_tool_names = {
        "run_sql",
        "execute_sql",
        "raw_query",
        "custom_query",
        "query_database",
        "execute_query",
    }
    exposed_tool_names = {tool.name for tool in await mcp.list_tools()}

    assert disallowed_tool_names.isdisjoint(exposed_tool_names)
