import secrets
import string

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.config import Settings

AUTH_ERROR = {"status": "error", "message": "Unauthorized."}


def validate_authorization_header(header_value: str | None, expected_token: str) -> bool:
    """Validate an HTTP Authorization header without exposing token material."""
    if not header_value or not expected_token:
        return False

    scheme, separator, token = header_value.partition(" ")
    if (
        separator != " "
        or scheme.lower() != "bearer"
        or not token
        or token != token.strip()
        or any(character in string.whitespace for character in token)
    ):
        return False

    return secrets.compare_digest(token, expected_token)


class BearerAuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, settings: Settings) -> None:  # type: ignore[no-untyped-def]
        super().__init__(app)
        self.settings = settings

    async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[no-untyped-def]
        if not validate_authorization_header(
            request.headers.get("authorization"),
            self.settings.mcp_bearer_token,
        ):
            return JSONResponse(AUTH_ERROR, status_code=401)
        return await call_next(request)
