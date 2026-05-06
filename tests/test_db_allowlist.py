import pytest

from app.config import Settings
from app.db.allowlist import TableAllowlist


def test_allowed_table_validation() -> None:
    allowlist = TableAllowlist(Settings(ALLOWED_TABLES="prospects,campaign_metrics"))
    assert allowlist.is_allowed("prospects")


def test_blocked_table_validation() -> None:
    allowlist = TableAllowlist(Settings(ALLOWED_TABLES="prospects"))
    assert not allowlist.is_allowed("users")
    with pytest.raises(ValueError):
        allowlist.require_allowed("users")


def test_unsafe_identifier_is_blocked() -> None:
    allowlist = TableAllowlist(Settings(ALLOWED_TABLES="prospects;drop"))
    assert not allowlist.is_allowed("prospects;drop")
    assert allowlist.list_tables() == []
