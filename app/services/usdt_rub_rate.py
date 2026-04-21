from __future__ import annotations

import logging
import time
from decimal import Decimal

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

_HTTP_TIMEOUT = 15.0
_COINGECKO_URL = "https://api.coingecko.com/api/v3/simple/price"
_CACHE_TTL_SEC = 3600.0

_cached_rub_per_usdt: Decimal | None = None
_cache_mono: float = 0.0


async def _fetch_coingecko_tether_rub() -> Decimal:
    async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT) as client:
        r = await client.get(
            _COINGECKO_URL,
            params={"ids": "tether", "vs_currencies": "rub"},
            headers={"Accept": "application/json", "User-Agent": "raccster-vpn-bot/1.0"},
        )
        r.raise_for_status()
        data = r.json()
    tether = data.get("tether")
    if not isinstance(tether, dict):
        raise ValueError("CoinGecko: нет tether в ответе")
    rub = tether.get("rub")
    if rub is None:
        raise ValueError("CoinGecko: нет tether.rub")
    d = Decimal(str(rub))
    if d <= 0:
        raise ValueError("CoinGecko: неположительный курс")
    return d


async def get_rub_per_usdt() -> Decimal:
    """
    Сколько ₽ за 1 USDT (для пересчёта тарифа: rub_tariff / kurs).
    Кэш ~1 ч; при ошибке API — последний удачный курс или CRYPTOPAY_RUB_PER_USDT из .env.
    """
    global _cached_rub_per_usdt, _cache_mono

    now = time.monotonic()
    if _cached_rub_per_usdt is not None and (now - _cache_mono) < _CACHE_TTL_SEC:
        return _cached_rub_per_usdt

    try:
        d = await _fetch_coingecko_tether_rub()
        _cached_rub_per_usdt = d
        _cache_mono = now
        logger.info("Курс USDT/RUB (CoinGecko): 1 USDT ≈ %s ₽", d)
        return d
    except Exception:
        logger.exception("Не удалось получить курс USDT/RUB с CoinGecko")
        if _cached_rub_per_usdt is not None:
            logger.info("Использую последний закэшированный курс: %s", _cached_rub_per_usdt)
            return _cached_rub_per_usdt
        fb = settings.cryptopay_rub_per_usdt
        logger.warning("Беру курс из CRYPTOPAY_RUB_PER_USDT: %s", fb)
        return fb
