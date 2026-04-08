from dataclasses import dataclass

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


@dataclass(frozen=True)
class ThreeXUIConfig:
    """Параметры одной панели 3x-ui (MHSanaei/3x-ui)."""

    base_url: str
    username: str
    password: str
    vless_server: str | None = None
    vless_port: int | None = None
    inbound_id: int = 1


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

    trial_days: int = Field(default=3, ge=1, le=365, validation_alias="TRIAL_DAYS")
    trial_traffic_gb: int = Field(default=0, ge=0, validation_alias="TRIAL_TRAFFIC_GB")

    threexui_base_url: str | None = Field(default=None, validation_alias="THREEXUI_BASE_URL")
    threexui_username: str | None = Field(default=None, validation_alias="THREEXUI_USERNAME")
    threexui_password: str | None = Field(default=None, validation_alias="THREEXUI_PASSWORD")
    threexui_vless_server: str | None = Field(default=None, validation_alias="THREEXUI_VLESS_SERVER")
    threexui_vless_port: int | None = Field(default=None, validation_alias="THREEXUI_VLESS_PORT")
    threexui_inbound_id: int = Field(default=1, ge=1, validation_alias="THREEXUI_INBOUND_ID")

    connect_page_windows_url: str | None = Field(default=None, validation_alias="CONNECT_PAGE_WINDOWS_URL")
    connect_page_iphone_url: str | None = Field(default=None, validation_alias="CONNECT_PAGE_IPHONE_URL")
    connect_page_android_url: str | None = Field(default=None, validation_alias="CONNECT_PAGE_ANDROID_URL")

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

    @field_validator(
        "connect_page_windows_url",
        "connect_page_iphone_url",
        "connect_page_android_url",
        mode="before",
    )
    @classmethod
    def empty_url_to_none(cls, v: object) -> str | None:
        if v is None:
            return None
        s = str(v).strip()
        return s if s else None

    def threexui_config(self) -> ThreeXUIConfig | None:
        base = (self.threexui_base_url or "").strip().rstrip("/")
        if not base:
            return None
        user = (self.threexui_username or "").strip()
        pwd = (self.threexui_password or "").strip()
        if not user or not pwd:
            return None
        vs = (self.threexui_vless_server or "").strip() or None
        return ThreeXUIConfig(
            base_url=base,
            username=user,
            password=pwd,
            vless_server=vs,
            vless_port=self.threexui_vless_port,
            inbound_id=int(self.threexui_inbound_id),
        )


settings = Settings()
