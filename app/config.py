from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    bot_token: str = Field(..., validation_alias="BOT_TOKEN")
    database_url: str = Field(..., validation_alias="DATABASE_URL")

    channel_username: str = Field(
        default="@raccsterVPN",
        validation_alias="CHANNEL_USERNAME",
    )
    channel_url: str = Field(
        default="https://t.me/raccsterVPN",
        validation_alias="CHANNEL_URL",
    )

    # Только для серверов с обязательным TLS: DATABASE_SSL=require
    database_ssl_require: bool = Field(default=False, validation_alias="DATABASE_SSL")

    @field_validator("database_ssl_require", mode="before")
    @classmethod
    def coerce_database_ssl_require(cls, v: object) -> bool:
        if v is None or v == "":
            return False
        if isinstance(v, bool):
            return v
        s = str(v).strip().lower()
        return s in ("1", "true", "yes", "require", "on")

    @field_validator("database_url")
    @classmethod
    def normalize_postgres_url(cls, v: str) -> str:
        if v.startswith("postgresql+asyncpg://"):
            return v.replace("postgresql+asyncpg://", "postgresql://", 1)
        return v


settings = Settings()
