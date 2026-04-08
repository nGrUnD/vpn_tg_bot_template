"""Один процесс polling на машину (fcntl), чтобы не ловить TelegramConflictError."""

from __future__ import annotations

import atexit
import logging
import os
import sys

from app.paths import PROJECT_ROOT

logger = logging.getLogger(__name__)

_LOCK_PATH = PROJECT_ROOT / ".bot_poll.lock"
_lock_fp: object | None = None


def _poll_lock_disabled_via_env() -> bool:
    raw = (os.environ.get("BOT_POLL_LOCK_DISABLE") or "").strip().lower()
    return raw in ("1", "true", "yes", "on", "skip")


def _release_lock() -> None:
    global _lock_fp
    if _lock_fp is None or sys.platform == "win32":
        return
    import fcntl

    try:
        fcntl.flock(_lock_fp.fileno(), fcntl.LOCK_UN)
    except OSError:
        pass
    try:
        _lock_fp.close()
    except OSError:
        pass
    _lock_fp = None
    try:
        _LOCK_PATH.unlink(missing_ok=True)
    except OSError:
        pass


def acquire_polling_lock() -> None:
    """
    На Linux/macOS держим эксклюзивный lock на файл.
    Второй запуск (например ручной python при работающем systemd) завершится сразу с понятным текстом.

    Отключение (только если понимаете риск): BOT_POLL_LOCK_DISABLE=1 — например «залипший»
    lock после kill -9 или отладка; при реально втором polling Telegram отдаст конфликт.
    """
    global _lock_fp

    if sys.platform == "win32":
        return

    if _poll_lock_disabled_via_env():
        logger.warning(
            "Блокировка .bot_poll.lock отключена (BOT_POLL_LOCK_DISABLE). "
            "Убедитесь, что второй процесс с тем же BOT_TOKEN не делает getUpdates."
        )
        return

    import fcntl

    _lock_fp = open(_LOCK_PATH, "w", encoding="utf-8")
    try:
        fcntl.flock(_lock_fp.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        _lock_fp.close()
        _lock_fp = None
        raise SystemExit(
            "Уже запущен другой экземпляр бота на этом сервере (занята блокировка .bot_poll.lock).\n\n"
            "Telegram допускает только один polling на токен. Сделай одно из:\n"
            "• Останови сервис: sudo systemctl stop vpn-tg-bot.service\n"
            "• Или не запускай второй раз python main.py, пока сервис работает\n"
            "• Проверь процессы: ps aux | grep main.py\n"
            "• Если бот открыт на своём ПК — закрой его там тоже\n\n"
            "Только если уверены, что другого poller нет (или «залип» lock): "
            "BOT_POLL_LOCK_DISABLE=1 python main.py\n"
        ) from None

    _lock_fp.write(str(os.getpid()))
    _lock_fp.flush()
    atexit.register(_release_lock)
