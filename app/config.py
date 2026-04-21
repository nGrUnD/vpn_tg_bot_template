import json
from dataclasses import dataclass
from decimal import Decimal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


@dataclass(frozen=True)
class ThreeXUIConfig:
    """Одна панель 3x-ui (MHSanaei/3x-ui). Несколько панелей — через THREEXUI_BACKENDS_JSON."""

    key: str
    base_url: str
    username: str
    password: str
    vless_server: str | None = None
    vless_port: int | None = None
    inbound_id: int = 1
    weight: int = 1
    enabled: bool = True
    title: str | None = None


def _parse_bool(value: object, default: bool = True) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    normalized = str(value).strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    return default


def _backend_from_mapping(data: dict, fallback_key: str) -> ThreeXUIConfig:
    key = str(data.get("key") or fallback_key).strip() or fallback_key
    base_url = str(data.get("base_url") or data.get("baseUrl") or "").strip().rstrip("/")
    username = str(data.get("username") or "").strip()
    password = str(data.get("password") or "").strip()
    if not base_url or not username or not password:
        raise ValueError(f"ThreeXUI backend '{key}': нужны base_url, username, password")
    vless_server = str(data.get("vless_server") or data.get("vlessServer") or "").strip() or None
    vless_port_raw = data.get("vless_port", data.get("vlessPort"))
    try:
        vless_port = int(vless_port_raw) if vless_port_raw not in (None, "") else None
    except (TypeError, ValueError):
        vless_port = None
    inbound_raw = data.get("inbound_id", data.get("inboundId", 1))
    try:
        inbound_id = max(int(inbound_raw), 1)
    except (TypeError, ValueError):
        inbound_id = 1
    weight_raw = data.get("weight", 1)
    try:
        weight = max(int(weight_raw), 1)
    except (TypeError, ValueError):
        weight = 1
    return ThreeXUIConfig(
        key=key,
        title=str(data.get("title") or key).strip() or key,
        base_url=base_url,
        username=username,
        password=password,
        vless_server=vless_server,
        vless_port=vless_port,
        inbound_id=inbound_id,
        enabled=_parse_bool(data.get("enabled"), True),
        weight=weight,
    )


def _parse_threexui_backends_json(raw_json: str) -> dict[str, ThreeXUIConfig]:
    try:
        parsed = json.loads(raw_json)
    except json.JSONDecodeError as exc:
        raise ValueError("THREEXUI_BACKENDS_JSON: невалидный JSON") from exc
    if isinstance(parsed, dict):
        items: list[dict] = []
        for k, value in parsed.items():
            if not isinstance(value, dict):
                raise ValueError("THREEXUI_BACKENDS_JSON: каждый бэкенд должен быть объектом")
            merged = dict(value)
            merged.setdefault("key", k)
            items.append(merged)
    elif isinstance(parsed, list):
        items = parsed
    else:
        raise ValueError("THREEXUI_BACKENDS_JSON: ожидается массив или объект")
    backends: dict[str, ThreeXUIConfig] = {}
    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            raise ValueError("THREEXUI_BACKENDS_JSON: каждый элемент должен быть объектом")
        backend = _backend_from_mapping(item, fallback_key=f"backend_{index}")
        backends[backend.key] = backend
    if not backends:
        raise ValueError("THREEXUI_BACKENDS_JSON: нужен хотя бы один бэкенд")
    return backends


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

    database_ssl_require: bool = Field(default=False, validation_alias="DATABASE_SSL")

    trial_days: int = Field(default=3, ge=1, le=365, validation_alias="TRIAL_DAYS")
    trial_traffic_gb: int = Field(default=0, ge=0, validation_alias="TRIAL_TRAFFIC_GB")

    threexui_backends_json: str | None = Field(default=None, validation_alias="THREEXUI_BACKENDS_JSON")
    threexui_default_key: str | None = Field(default=None, validation_alias="THREEXUI_DEFAULT_KEY")

    threexui_base_url: str | None = Field(default=None, validation_alias="THREEXUI_BASE_URL")
    threexui_username: str | None = Field(default=None, validation_alias="THREEXUI_USERNAME")
    threexui_password: str | None = Field(default=None, validation_alias="THREEXUI_PASSWORD")
    threexui_vless_server: str | None = Field(default=None, validation_alias="THREEXUI_VLESS_SERVER")
    threexui_vless_port: int | None = Field(default=None, validation_alias="THREEXUI_VLESS_PORT")
    threexui_inbound_id: int = Field(default=1, ge=1, validation_alias="THREEXUI_INBOUND_ID")

    connect_page_windows_url: str | None = Field(default=None, validation_alias="CONNECT_PAGE_WINDOWS_URL")
    connect_page_iphone_url: str | None = Field(default=None, validation_alias="CONNECT_PAGE_IPHONE_URL")
    connect_page_android_url: str | None = Field(default=None, validation_alias="CONNECT_PAGE_ANDROID_URL")
    iphone_instruction_url: str | None = Field(default=None, validation_alias="IPHONE_INSTRUCTION_URL")
    android_instruction_url: str | None = Field(default=None, validation_alias="ANDROID_INSTRUCTION_URL")

    # Статическая ссылка на оплату (если нет WATA API — как раньше; при настроенном WATA токене не используется)
    payment_rub_checkout_url: str | None = Field(default=None, validation_alias="PAYMENT_RUB_CHECKOUT_URL")

    # WATA H2H: https://wata.pro/api — платёжные ссылки + webhook
    wata_access_token: str | None = Field(default=None, validation_alias="WATA_ACCESS_TOKEN")
    wata_api_base: str = Field(
        default="https://api.wata.pro/api/h2h",
        validation_alias="WATA_API_BASE",
    )
    wata_webhook_path: str = Field(default="/webhooks/wata", validation_alias="WATA_WEBHOOK_PATH")
    wata_webhook_verify_signature: bool = Field(default=True, validation_alias="WATA_WEBHOOK_VERIFY_SIGNATURE")
    http_webhook_host: str = Field(default="0.0.0.0", validation_alias="HTTP_WEBHOOK_HOST")
    http_webhook_port: int = Field(default=0, ge=0, le=65535, validation_alias="HTTP_WEBHOOK_PORT")

    # Crypto Pay (@CryptoBot): https://help.send.tg/en/articles/10279948-crypto-pay-api
    cryptopay_api_token: str | None = Field(default=None, validation_alias="CRYPTOPAY_API_TOKEN")
    cryptopay_testnet: bool = Field(default=False, validation_alias="CRYPTOPAY_TESTNET")
    cryptopay_api_base: str | None = Field(default=None, validation_alias="CRYPTOPAY_API_BASE")
    cryptopay_webhook_path: str = Field(default="/webhooks/cryptobot", validation_alias="CRYPTOPAY_WEBHOOK_PATH")
    cryptopay_webhook_verify_signature: bool = Field(default=True, validation_alias="CRYPTOPAY_WEBHOOK_VERIFY_SIGNATURE")
    cryptopay_webhook_public_url: str | None = Field(default=None, validation_alias="CRYPTOPAY_WEBHOOK_PUBLIC_URL")
    # Сколько ₽ за 1 USDT — цена USDT в тарифах = rub_tariff_amount_rub / CRYPTOPAY_RUB_PER_USDT
    cryptopay_rub_per_usdt: Decimal = Field(
        default=Decimal("83"),
        ge=Decimal("0.01"),
        validation_alias="CRYPTOPAY_RUB_PER_USDT",
    )

    @field_validator("cryptopay_rub_per_usdt", mode="before")
    @classmethod
    def parse_cryptopay_rub_per_usdt(cls, v: object) -> Decimal:
        if v is None or v == "":
            return Decimal("83")
        if isinstance(v, Decimal):
            return v
        return Decimal(str(v).strip().replace(",", "."))

    @field_validator("wata_webhook_verify_signature", mode="before")
    @classmethod
    def coerce_wata_webhook_verify_signature(cls, v: object) -> bool:
        return _parse_bool(v, default=True)

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
        "iphone_instruction_url",
        "android_instruction_url",
        "payment_rub_checkout_url",
        "wata_access_token",
        "cryptopay_api_token",
        "cryptopay_api_base",
        "cryptopay_webhook_public_url",
        mode="before",
    )
    @classmethod
    def empty_url_to_none(cls, v: object) -> str | None:
        if v is None:
            return None
        s = str(v).strip()
        return s if s else None

    @field_validator("wata_api_base", mode="before")
    @classmethod
    def normalize_wata_api_base(cls, v: object) -> str:
        s = (str(v).strip() if v is not None else "").strip().rstrip("/")
        return s or "https://api.wata.pro/api/h2h"

    @field_validator("wata_webhook_path", mode="before")
    @classmethod
    def normalize_webhook_path(cls, v: object) -> str:
        s = (str(v) if v is not None else "").strip() or "/webhooks/wata"
        return s if s.startswith("/") else f"/{s}"

    @field_validator("cryptopay_webhook_path", mode="before")
    @classmethod
    def normalize_cryptopay_webhook_path(cls, v: object) -> str:
        s = (str(v) if v is not None else "").strip() or "/webhooks/cryptobot"
        return s if s.startswith("/") else f"/{s}"

    @field_validator("cryptopay_webhook_verify_signature", mode="before")
    @classmethod
    def coerce_cryptopay_webhook_verify(cls, v: object) -> bool:
        return _parse_bool(v, default=True)

    def wata_api_configured(self) -> bool:
        return bool((self.wata_access_token or "").strip())

    def cryptopay_api_configured(self) -> bool:
        return bool((self.cryptopay_api_token or "").strip())

    def cryptopay_api_root(self) -> str:
        if self.cryptopay_testnet:
            return "https://testnet-pay.crypt.bot"
        s = (self.cryptopay_api_base or "").strip().rstrip("/")
        return s or "https://pay.crypt.bot"

    def wata_webhook_server_enabled(self) -> bool:
        return self.wata_api_configured() and int(self.http_webhook_port) > 0

    def payment_webhook_server_enabled(self) -> bool:
        """HTTP-сервер для приёма webhook (WATA и/или Crypto Pay)."""
        return int(self.http_webhook_port) > 0 and (
            self.wata_api_configured() or self.cryptopay_api_configured()
        )

    def threexui_backend_configs(self) -> dict[str, ThreeXUIConfig]:
        raw_json = (self.threexui_backends_json or "").strip()
        if raw_json:
            return _parse_threexui_backends_json(raw_json)
        base = (self.threexui_base_url or "").strip().rstrip("/")
        if not base:
            return {}
        user = (self.threexui_username or "").strip()
        pwd = (self.threexui_password or "").strip()
        if not user or not pwd:
            return {}
        vs = (self.threexui_vless_server or "").strip() or None
        cfg = ThreeXUIConfig(
            key="default",
            title="default",
            base_url=base,
            username=user,
            password=pwd,
            vless_server=vs,
            vless_port=self.threexui_vless_port,
            inbound_id=int(self.threexui_inbound_id),
            weight=1,
            enabled=True,
        )
        return {"default": cfg}

    def threexui_default_backend_key(self) -> str:
        configs = self.threexui_backend_configs()
        if not configs:
            return "default"
        explicit = (self.threexui_default_key or "").strip()
        if explicit:
            if explicit not in configs:
                raise ValueError(
                    f"THREEXUI_DEFAULT_KEY='{explicit}' отсутствует в списке панелей "
                    f"({', '.join(sorted(configs.keys()))})"
                )
            return explicit
        return sorted(configs.keys())[0]


settings = Settings()
