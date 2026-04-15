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


def _api_root() -> str:
    return (settings.wata_api_base or "").strip().rstrip("/")


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
    r = await client.get(url, headers={"Content-Type": "application/json"})
    r.raise_for_status()
    data = r.json()
    if not isinstance(data, dict):
        raise ValueError("public-key: ожидался объект JSON")
    value = data.get("value")
    if not isinstance(value, str) or not value.strip():
        raise ValueError("public-key: нет поля value")
    return value.strip()


async def create_payment_link(
    *,
    amount: float,
    currency: str,
    order_id: str,
    description: str | None = None,
    link_type: str = "OneTime",
) -> dict[str, Any]:
    token = (settings.wata_access_token or "").strip()
    if not token:
        raise RuntimeError("WATA_ACCESS_TOKEN не задан")

    root = _api_root()
    url = f"{root}/links"
    body: dict[str, Any] = {
        "type": link_type,
        "amount": round(float(amount), 2),
        "currency": currency,
        "orderId": order_id,
    }
    if description:
        body["description"] = description

    client = await _client()
    r = await client.post(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json=body,
    )
    if r.status_code >= 400:
        logger.warning("WATA create link HTTP %s: %s", r.status_code, r.text[:500])
    r.raise_for_status()
    data = r.json()
    if not isinstance(data, dict):
        raise ValueError("create link: некорректный JSON")
    return data
