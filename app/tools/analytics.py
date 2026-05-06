from typing import Any

from app.config import Settings
from app.db.allowlist import TableAllowlist
from app.db.connection import Database
from app.security.query_guard import clamp_limit, client_error, filter_sensitive_rows
from app.tools.health import safe_success

CAMPAIGN_METRICS_TABLE = "campaign_metrics"


async def get_campaign_metrics(
    db: Database,
    allowlist: TableAllowlist,
    settings: Settings,
    campaign_id: int | None = None,
    limit: int | None = None,
) -> dict[str, Any]:
    try:
        allowlist.require_allowed(CAMPAIGN_METRICS_TABLE)
        row_limit = clamp_limit(limit, settings.max_rows)
        if campaign_id is None:
            rows = await db.fetch(
                """
                SELECT *
                FROM campaign_metrics
                ORDER BY metric_date DESC NULLS LAST
                LIMIT $1
                """,
                row_limit,
            )
        else:
            rows = await db.fetch(
                """
                SELECT *
                FROM campaign_metrics
                WHERE campaign_id = $1
                ORDER BY metric_date DESC NULLS LAST
                LIMIT $2
                """,
                campaign_id,
                row_limit,
            )
    except ValueError:
        return client_error("Table is not allowed.")
    except Exception:
        return client_error("Could not fetch campaign metrics.")

    return safe_success({"limit": row_limit, "records": filter_sensitive_rows(rows)})

