from __future__ import annotations

import logging
from dataclasses import dataclass

from app.config import ThreeXUIConfig
from app.db import get_pool
from app.threexui_client import ThreeXUIClient

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ThreexuiRuntime:
    """Все включённые панели 3x-ui и ключ по умолчанию (как в vpn_template)."""

    registry: dict[str, ThreeXUIClient]
    configs: dict[str, ThreeXUIConfig]
    default_key: str

    @property
    def has_backends(self) -> bool:
        return bool(self.registry)


def build_threexui_registry(configs: dict[str, ThreeXUIConfig]) -> dict[str, ThreeXUIClient]:
    return {
        key: ThreeXUIClient(cfg)
        for key, cfg in configs.items()
        if cfg.enabled
    }


async def close_threexui_registry(registry: dict[str, ThreeXUIClient]) -> None:
    for client in registry.values():
        await client.close()


def pick_alternate_backend_key(runtime: ThreexuiRuntime, current_key: str) -> str | None:
    """Другая включённая панель (например Стокгольм вместо Германии)."""
    cur = (current_key or "").strip()
    for k in sorted(runtime.registry.keys()):
        if k != cur:
            return k
    return None


def threexui_client_for_backend(
    runtime: ThreexuiRuntime,
    backend_key: str | None,
) -> ThreeXUIClient | None:
    """HTTP-клиент панели по ключу из БД; иначе default, иначе любой из registry."""
    key = (backend_key or "").strip()
    if key and key in runtime.registry:
        return runtime.registry[key]
    if runtime.default_key in runtime.registry:
        return runtime.registry[runtime.default_key]
    if runtime.registry:
        return next(iter(runtime.registry.values()))
    return None


async def pick_backend_for_new_trial(
    *,
    registry: dict[str, ThreeXUIClient],
    configs: dict[str, ThreeXUIConfig],
    default_key: str,
) -> ThreeXUIConfig:
    """
    Равномерная загрузка: минимум (активных_trial / weight), как pick_backend_for_new_subscription
    в vpn_template (там считаются подписки; здесь — активные trial в users).
    """
    enabled = [
        cfg
        for key, cfg in configs.items()
        if cfg.enabled and key in registry
    ]
    if not enabled:
        raise RuntimeError("Нет ни одной включённой панели 3x-ui в конфиге")

    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT
                COALESCE(NULLIF(TRIM(trial_backend_key), ''), $1) AS bk,
                COUNT(*)::int AS total
            FROM users
            WHERE trial_expires_at IS NOT NULL AND trial_expires_at > NOW()
            GROUP BY COALESCE(NULLIF(TRIM(trial_backend_key), ''), $1)
            """,
            default_key,
        )
    counts = {str(r["bk"]): int(r["total"] or 0) for r in rows}

    def sort_key(cfg: ThreeXUIConfig) -> tuple[float, int, int, str]:
        active = counts.get(cfg.key, 0)
        weighted_score = active / max(cfg.weight, 1)
        is_not_default = 0 if cfg.key == default_key else 1
        return (weighted_score, active, is_not_default, cfg.key)

    chosen = min(enabled, key=sort_key)
    logger.info(
        "3x-ui: новый trial на панель key=%s (weighted_load=%.3f, active_trials=%s)",
        chosen.key,
        counts.get(chosen.key, 0) / max(chosen.weight, 1),
        counts.get(chosen.key, 0),
    )
    return chosen
