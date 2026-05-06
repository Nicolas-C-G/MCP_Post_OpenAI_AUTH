import re
from typing import Any

SENSITIVE_COLUMN_MARKERS = (
    "password",
    "password_hash",
    "token",
    "api_key",
    "secret",
    "credential",
    "cookie",
    "session",
    "refresh_token",
    "access_token",
    "private_key",
)

SAFE_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def is_safe_identifier(value: str) -> bool:
    return bool(SAFE_IDENTIFIER_RE.fullmatch(value))


def quote_identifier(value: str) -> str:
    if not is_safe_identifier(value):
        raise ValueError("Unsafe SQL identifier.")
    return f'"{value}"'


def clamp_limit(requested_limit: int | None, max_rows: int) -> int:
    if requested_limit is None:
        return max_rows
    return max(1, min(requested_limit, max_rows))


def is_sensitive_column(column_name: str) -> bool:
    lowered = column_name.lower()
    return any(marker in lowered for marker in SENSITIVE_COLUMN_MARKERS)


def filter_sensitive_columns(row: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in row.items() if not is_sensitive_column(key)}


def filter_sensitive_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [filter_sensitive_columns(row) for row in rows]


def client_error(message: str) -> dict[str, str]:
    return {"status": "error", "message": message}

