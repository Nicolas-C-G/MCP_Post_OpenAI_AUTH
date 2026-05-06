from app.auth.bearer import validate_authorization_header


def test_bearer_token_validation() -> None:
    assert validate_authorization_header("Bearer expected-token", "expected-token")


def test_missing_token_rejection() -> None:
    assert not validate_authorization_header(None, "expected-token")


def test_invalid_token_rejection() -> None:
    assert not validate_authorization_header("Bearer wrong-token", "expected-token")


def test_malformed_token_rejection() -> None:
    assert not validate_authorization_header("Basic expected-token", "expected-token")
    assert not validate_authorization_header("Bearer", "expected-token")
    assert not validate_authorization_header("Bearer  expected-token", "expected-token")
    assert not validate_authorization_header("Bearer expected-token extra", "expected-token")
