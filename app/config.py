from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    mcp_server_name: str = Field(default="postgres-readonly-mcp", alias="MCP_SERVER_NAME")
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")
    max_rows: int = Field(default=100, alias="MAX_ROWS", ge=1, le=1000)
    allowed_tables: tuple[str, ...] = Field(
        default=("prospects", "campaign_metrics"),
        alias="ALLOWED_TABLES",
    )
    mcp_bearer_token: str = Field(default="", alias="MCP_BEARER_TOKEN")

    postgres_host: str = Field(default="localhost", alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, alias="POSTGRES_PORT")
    postgres_db: str = Field(default="app", alias="POSTGRES_DB")
    postgres_user: str = Field(default="mcp_readonly", alias="POSTGRES_USER")
    postgres_password: str = Field(default="", alias="POSTGRES_PASSWORD")

    @field_validator("allowed_tables", mode="before")
    @classmethod
    def parse_allowed_tables(cls, value: str | list[str] | tuple[str, ...]) -> tuple[str, ...]:
        if isinstance(value, str):
            return tuple(table.strip() for table in value.split(",") if table.strip())
        return tuple(value)

@lru_cache
def get_settings() -> Settings:
    return Settings()
