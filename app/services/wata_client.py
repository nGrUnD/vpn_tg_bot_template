from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

_http: httpx.AsyncClient | None = None
_public_key_lock = asyncio.Lock()
_cached_public_key_pem: str | None = None


class WataApiError(RuntimeError):
    def __init__(self, status_code: int, message: str, *, details: str | None = None) -> None:
        self.status_code = status_code
        self.details = details
        super().__init__(message)


def _api_root() -> str:
    return (settings.wata_api_base or "").strip().rstrip("/")


def _access_token() -> str:
    token = (settings.wata_access_token or "").strip()
    if not token:
        raise RuntimeError("WATA_ACCESS_TOKEN не задан")
    return token


def _auth_headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {_access_token()}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def _parse_wata_error_body(response: httpx.Response) -> str | None:
    try:
        data = response.json()
    except Exception:
        text = (response.text or "").strip()
        return text[:500] if text else None
    if not isinstance(data, dict):
        return None
    err = data.get("error")
    if not isinstance(err, dict):
        return None
    parts: list[str] = []
    for key in ("message", "details", "code"):
        value = err.get(key)
        if value not in (None, ""):
            parts.append(str(value))
    validation = err.get("validationErrors")
    if validation:
        parts.append(str(validation))
    return " — ".join(parts) if parts else None


def _wata_error_code(response: httpx.Response) -> str | None:
    try:
        data = response.json()
        if isinstance(data, dict):
            err = data.get("error")
            if isinstance(err, dict):
                code = err.get("code")
                if code not in (None, ""):
                    return str(code)
    except Exception:
        pass
    return None


_WATA_ERROR_HINTS: dict[str, str] = {
    "Payment:MER_1004": (
        "Аккаунт мерчанта заблокирован в WATA. "
        "Обратитесь в поддержку или к личному менеджеру WATA — смена токена не поможет."
    ),
}


def _raise_for_wata_response(response: httpx.Response, *, action: str) -> None:
    if response.status_code < 400:
        return
    details = _parse_wata_error_body(response)
    error_code = _wata_error_code(response)
    if error_code and error_code in _WATA_ERROR_HINTS:
        hint = _WATA_ERROR_HINTS[error_code]
    elif response.status_code == 401:
        hint = (
            "WATA access token недействителен или истёк. "
            "Перевыпустите токен в merchant.wata.pro → Терминалы → ваш терминал."
        )
    elif response.status_code == 403:
        hint = (
            "WATA access token не имеет доступа к этому методу API. "
            "Проверьте: в .env указан Access token (не Secret Key), "
            "WATA_API_BASE совпадает с окружением токена "
            "(боевой https://api.wata.pro/api/h2h или песочница https://api-sandbox.wata.pro/api/h2h), "
            "токен создан для терминала с продуктом Эквайринг/H2H."
        )
    else:
        hint = f"WATA {action} завершился с HTTP {response.status_code}"
    message = f"{hint} URL={response.request.url}"
    if details:
        message = f"{message}. Ответ: {details}"
    logger.error(message)
    raise WataApiError(response.status_code, message, details=details)


async def _client() -> httpx.AsyncClient:
    global _http
    if _http is None:
        _http = httpx.AsyncClient(timeout=60.0)
    return _http


async def aclose_wata_http() -> None:
    global _http
    if _http is not None:
        await _http.aclose()
        _http = None


async def get_cached_public_key_pem() -> str:
    global _cached_public_key_pem
    async with _public_key_lock:
        if not _cached_public_key_pem:
            _cached_public_key_pem = await fetch_public_key_pem()
        return _cached_public_key_pem


async def invalidate_public_key_cache() -> None:
    global _cached_public_key_pem
    async with _public_key_lock:
        _cached_public_key_pem = None


async def fetch_public_key_pem() -> str:
    root = _api_root()
    url = f"{root}/public-key"
    client = await _client()
    r = await client.get(url, headers={"Content-Type": "application/json", "Accept": "application/json"})
    r.raise_for_status()
    data = r.json()
    if not isinstance(data, dict):
        raise ValueError("public-key: ожидался объект JSON")
    value = data.get("value")
    if not isinstance(value, str) or not value.strip():
        raise ValueError("public-key: нет поля value")
    return value.strip()


async def probe_wata_api_access() -> None:
    """Проверка access token при старте (GET /links, без создания платежа)."""
    if not settings.wata_api_configured():
        return
    root = _api_root()
    url = f"{root}/links"
    client = await _client()
    try:
        r = await client.get(
            url,
            params={"maxResultCount": 1},
            headers=_auth_headers(),
        )
    except httpx.HTTPError:
        logger.exception("WATA: не удалось связаться с API (%s)", url)
        return
    if r.status_code < 400:
        logger.info("WATA API: access token принят (%s)", root)
        return
    try:
        _raise_for_wata_response(r, action="проверка access token")
    except WataApiError:
        return


async def create_payment_link(
    *,
    amount: float,
    currency: str,
    order_id: str,
    description: str | None = None,
    link_type: str = "OneTime",
) -> dict[str, Any]:
    root = _api_root()
    url = f"{root}/links"
    value = round(float(amount), 2)
    if currency.upper() == "RUB" and value < 10:
        raise WataApiError(
            400,
            "WATA: минимальная сумма платежа 10 RUB",
            details=f"amount={value}",
        )

    body: dict[str, Any] = {
        "type": link_type,
        "amount": value,
        "currency": currency.upper(),
        "orderId": order_id,
    }
    if description:
        body["description"] = description

    client = await _client()
    r = await client.post(url, headers=_auth_headers(), json=body)
    _raise_for_wata_response(r, action="создание платёжной ссылки")
    data = r.json()
    if not isinstance(data, dict):
        raise ValueError("create link: некорректный JSON")
    return data
