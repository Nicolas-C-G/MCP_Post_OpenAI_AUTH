from app.security.query_guard import clamp_limit, filter_sensitive_columns, is_sensitive_column


def test_row_limit_enforcement() -> None:
    assert clamp_limit(500, 100) == 100
    assert clamp_limit(None, 25) == 25
    assert clamp_limit(0, 25) == 1


def test_sensitive_column_filtering() -> None:
    row = {
        "id": 1,
        "email": "person@example.com",
        "password_hash": "hidden",
        "api_key_value": "hidden",
        "session_id": "hidden",
    }
    assert filter_sensitive_columns(row) == {"id": 1, "email": "person@example.com"}
    assert is_sensitive_column("private_key_pem")

