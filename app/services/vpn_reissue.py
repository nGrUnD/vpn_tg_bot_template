from __future__ import annotations

import logging
from datetime import datetime, timezone

from app.config import settings
from app.services.threexui_backends import (
    ThreexuiRuntime,
    pick_alternate_backend_key,
)
from app.services.users import get_trial_reissue_row, save_trial_access

logger = logging.getLogger(__name__)

_MIN_REMAINING_BYTES = 1024**3


def _expires_ms_from_row(expires_at: datetime) -> int:
    exp = expires_at
    if exp.tzinfo is None:
        exp = exp.replace(tzinfo=timezone.utc)
    return int(exp.timestamp() * 1000)


def _new_total_bytes_from_snapshot(
    snapshot: tuple[int, int, int] | None,
) -> int:
    """Остаток трафика для новой панели; безлимит как при trial (0)."""
    if snapshot is None:
        if settings.trial_traffic_gb <= 0:
            return 0
        return int(settings.trial_traffic_gb) * (1024**3)
    _exp_ms, limit_b, used_max = snapshot
    if limit_b <= 0:
        return 0
    rem = max(limit_b - used_max, 0)
    return rem if rem > 0 else _MIN_REMAINING_BYTES


async def reissue_trial_cross_panel(telegram_id: int, runtime: ThreexuiRuntime) -> tuple[bool, str]:
    """
    Создаёт клиента на другой панели с той же датой окончания и остатком трафика,
    удаляет старый UUID на текущей панели, обновляет БД.
    """
    if not runtime.has_backends:
        return False, "Панели VPN не настроены."

    row = await get_trial_reissue_row(telegram_id)
    if row is None:
        return False, "Нет активного пробного доступа."

    old_uuid = str(row["trial_client_uuid"]).strip()
    old_key = str(row["trial_backend_key"] or "").strip() or runtime.default_key
    expires_at: datetime = row["trial_expires_at"]
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    new_key = pick_alternate_backend_key(runtime, old_key)
    if not new_key:
        return False, "Для перевыпуска нужна вторая панель (сервер)."

    old_client = runtime.registry.get(old_key)
    new_client = runtime.registry.get(new_key)
    if old_client is None:
        return False, "Текущая панель VPN недоступна."
    if new_client is None:
        return False, "Запасная панель VPN недоступна."

    expiry_ts_ms = _expires_ms_from_row(expires_at)
    snapshot = await old_client.collect_client_quota_snapshot(old_uuid)
    total_bytes = _new_total_bytes_from_snapshot(snapshot)

    try:
        info = await new_client.create_client_all_inbounds(
            telegram_id,
            expiry_ts_ms=expiry_ts_ms,
            total_bytes=total_bytes,
        )
    except Exception as e:
        logger.exception("reissue: create on new panel failed user=%s", telegram_id)
        return False, str(e).strip() or "ошибка панели"

    await old_client.delete_client_uuid_from_all_inbounds(old_uuid)

    await save_trial_access(
        telegram_id,
        client_uuid=info.client_id,
        sub_id=info.sub_id or "",
        subscription_url=info.subscription_url,
        backend_key=new_key,
        expires_at=expires_at,
    )

    cfg = runtime.configs.get(new_key)
    title = (cfg.title if cfg else None) or new_key
    return True, title
