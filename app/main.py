import contextlib

import uvicorn
from mcp.server.fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.routing import Mount

from app.auth.bearer import BearerAuthMiddleware
from app.config import Settings, get_settings
from app.db.allowlist import TableAllowlist
from app.db.connection import Database
from app.tools.analytics import get_campaign_metrics as get_campaign_metrics_impl
from app.tools.health import db_connection_check as db_connection_check_impl
from app.tools.health import health_check as health_check_impl
from app.tools.prospects import get_prospect_by_id as get_prospect_by_id_impl
from app.tools.prospects import search_prospects as search_prospects_impl
from app.tools.schema import describe_table as describe_table_impl
from app.tools.schema import get_recent_records as get_recent_records_impl
from app.tools.schema import list_allowed_tables as list_allowed_tables_impl

settings = get_settings()
database = Database(settings)
allowlist = TableAllowlist(settings)
mcp = FastMCP(settings.mcp_server_name, stateless_http=True, json_response=True)


@mcp.tool()
async def health_check() -> dict[str, str]:
    """Return MCP server health status."""
    return await health_check_impl()


@mcp.tool()
async def db_connection_check() -> dict[str, str]:
    """Check whether the server can reach PostgreSQL."""
    return await db_connection_check_impl(database)


@mcp.tool()
def list_allowed_tables() -> dict:
    """List database tables this server is allowed to inspect or read."""
    return list_allowed_tables_impl(allowlist)


@mcp.tool()
async def describe_table(table_name: str) -> dict:
    """Describe non-sensitive columns for one allowed table."""
    return await describe_table_impl(table_name, database, allowlist)


@mcp.tool()
async def get_recent_records(table_name: str, limit: int | None = None) -> dict:
    """Return recent rows from an allowed table, capped by MAX_ROWS."""
    return await get_recent_records_impl(table_name, database, allowlist, settings, limit)


@mcp.tool()
async def search_prospects(search: str, limit: int | None = None) -> dict:
    """Search prospects by name, email, or company."""
    return await search_prospects_impl(search, database, allowlist, settings, limit)


@mcp.tool()
async def get_prospect_by_id(prospect_id: int) -> dict:
    """Fetch one prospect by numeric ID."""
    return await get_prospect_by_id_impl(prospect_id, database, allowlist)


@mcp.tool()
async def get_campaign_metrics(campaign_id: int | None = None, limit: int | None = None) -> dict:
    """Fetch campaign metrics, optionally filtered by campaign ID."""
    return await get_campaign_metrics_impl(database, allowlist, settings, campaign_id, limit)


@contextlib.asynccontextmanager
async def lifespan(app: Starlette):  # type: ignore[no-untyped-def]
    async with mcp.session_manager.run():
        yield
    await database.close()


def create_app(app_settings: Settings | None = None) -> Starlette:
    active_settings = app_settings or settings
    return Starlette(
        routes=[Mount("/", app=mcp.streamable_http_app())],
        middleware=[Middleware(BearerAuthMiddleware, settings=active_settings)],
        lifespan=lifespan,
    )


app = create_app(settings)


def main() -> None:
    uvicorn.run("app.main:app", host=settings.host, port=settings.port)


if __name__ == "__main__":
    main()

