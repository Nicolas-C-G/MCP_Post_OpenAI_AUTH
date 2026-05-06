from app.config import Settings
from app.security.query_guard import is_safe_identifier


class TableAllowlist:
    def __init__(self, settings: Settings) -> None:
        self._tables = frozenset(
            table_name for table_name in settings.allowed_tables if is_safe_identifier(table_name)
        )

    def list_tables(self) -> list[str]:
        return sorted(self._tables)

    def is_allowed(self, table_name: str) -> bool:
        return table_name in self._tables and is_safe_identifier(table_name)

    def require_allowed(self, table_name: str) -> str:
        if not self.is_allowed(table_name):
            raise ValueError("Table is not allowed.")
        return table_name
