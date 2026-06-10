from __future__ import annotations

import logging
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

_http: httpx.AsyncClient | None = None


async def _client() -> httpx.AsyncClient:
    global _http
    if _http is None:
        _http = httpx.AsyncClient(timeout=60.0)
    return _http


async def aclose_cryptopay_http() -> None:
    global _http
    if _http is not None:
        await _http.aclose()
        _http = None


def _api_url(method: str) -> str:
    root = settings.cryptopay_api_root()
    return f"{root}/api/{method}"


def _headers() -> dict[str, str]:
    token = (settings.cryptopay_api_token or "").strip()
    return {
        "Content-Type": "application/json",
        "Crypto-Pay-API-Token": token,
    }


async def cryptopay_api_post(method: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
    token = (settings.cryptopay_api_token or "").strip()
    if not token:
        raise RuntimeError("CRYPTOPAY_API_TOKEN не задан")
    url = _api_url(method)
    client = await _client()
    r = await client.post(url, json=body or {}, headers=_headers())
    r.raise_for_status()
    data = r.json()
    if not isinstance(data, dict):
        raise ValueError("Crypto Pay: некорректный JSON")
    if not data.get("ok"):
        err = data.get("error") or data
        raise RuntimeError(f"Crypto Pay API: {err}")
    res = data.get("result")
    if not isinstance(res, dict):
        raise ValueError("Crypto Pay: в ответе нет result")
    return res


async def create_invoice(
    *,
    amount_usdt: str,
    description: str,
    payload: str,
) -> dict[str, Any]:
    """createInvoice — payload до ~4KB, приходит в webhook как invoice.payload."""
    return await cryptopay_api_post(
        "createInvoice",
        {
            "currency_type": "crypto",
            "asset": "USDT",
            "amount": amount_usdt,
            "description": description,
            "payload": payload,
            "allow_comments": False,
        },
    )


def invoice_payment_url(inv: dict[str, Any]) -> str | None:
    for key in ("mini_app_invoice_url", "web_app_invoice_url", "bot_invoice_url", "pay_url"):
        u = inv.get(key)
        if isinstance(u, str) and u.strip():
            return u.strip()
    return None


async def sync_cryptopay_webhook_from_env() -> None:
    """При старте HTTP: напомнить URL для ручной настройки в @CryptoBot (API setWebhook нет)."""
    if not settings.cryptopay_api_configured():
        return
    url = (settings.cryptopay_webhook_public_url or "").strip()
    path = settings.cryptopay_webhook_path
    if url:
        logger.info(
            "Crypto Pay: в @CryptoBot → Crypto Pay → приложение → Webhooks укажите URL: %s",
            url,
        )
    else:
        logger.warning(
            "Crypto Pay: задан CRYPTOPAY_API_TOKEN, но CRYPTOPAY_WEBHOOK_PUBLIC_URL пуст — "
            "в @CryptoBot → Webhooks укажите публичный HTTPS URL (путь %s)",
            path,
        )

