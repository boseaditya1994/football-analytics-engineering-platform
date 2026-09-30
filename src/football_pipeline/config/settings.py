"""Environment-driven configuration for the pipeline."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    football_data_api_key: str = Field(..., alias="FOOTBALL_DATA_API_KEY")
    football_data_base_url: str = Field(
        "https://api.football-data.org/v4", alias="FOOTBALL_DATA_BASE_URL"
    )

    snowflake_account: str = Field("", alias="SNOWFLAKE_ACCOUNT")
    snowflake_user: str = Field("", alias="SNOWFLAKE_USER")
    # Password auth triggers interactive MFA (Duo) on accounts that require it,
    # which blocks non-interactive callers (this API, CI). Prefer key-pair auth
    # (SNOWFLAKE_PRIVATE_KEY_PATH) - password stays supported as a local-dev
    # fallback for interactive use only.
    snowflake_password: str = Field("", alias="SNOWFLAKE_PASSWORD")
    snowflake_private_key_path: str = Field("", alias="SNOWFLAKE_PRIVATE_KEY_PATH")
    # Alternative to the path above for hosts with no writable/mountable
    # file for secrets (e.g. Render env vars): the PEM content itself,
    # pasted directly into an env var rather than referenced by path.
    snowflake_private_key: str = Field("", alias="SNOWFLAKE_PRIVATE_KEY")
    snowflake_private_key_passphrase: str = Field(
        "", alias="SNOWFLAKE_PRIVATE_KEY_PASSPHRASE"
    )
    snowflake_role: str = Field("FOOTBALL_ANALYTICS_ROLE", alias="SNOWFLAKE_ROLE")
    snowflake_warehouse: str = Field("FOOTBALL_ANALYTICS_WH", alias="SNOWFLAKE_WAREHOUSE")
    snowflake_database: str = Field("FOOTBALL_ANALYTICS", alias="SNOWFLAKE_DATABASE")
    snowflake_schema: str = Field("RAW", alias="SNOWFLAKE_SCHEMA")

    log_level: str = Field("INFO", alias="LOG_LEVEL")


@lru_cache
def get_settings() -> Settings:
    return Settings()
