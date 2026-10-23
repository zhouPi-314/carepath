from functools import lru_cache

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "医疗健康协同体平台 API"
    app_env: str = Field(default="development", alias="APP_ENV")
    database_url: str = Field(
        default="sqlite+aiosqlite:///./carepath.db",
        alias="DATABASE_URL",
    )
    secret_key: str = Field(
        default="development-only-secret-key-change-before-deployment",
        alias="SECRET_KEY",
    )
    access_token_minutes: int = 15
    refresh_token_days: int = 14
    cookie_secure: bool = False
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    auto_create_schema: bool = True

    @model_validator(mode="after")
    def validate_production_security(self) -> "Settings":
        if self.app_env == "production":
            if not self.database_url.startswith(("postgresql+asyncpg://", "postgresql://")):
                raise ValueError("Production DATABASE_URL must use PostgreSQL")
            if self.secret_key.startswith("development-"):
                raise ValueError("Production SECRET_KEY must be explicitly configured")
            if not self.cookie_secure:
                raise ValueError("Production cookies must be secure")
        return self

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
