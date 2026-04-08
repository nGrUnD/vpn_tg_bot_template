"""Ответ на callback: устаревшие query после рестарта бота дают TelegramBadRequest."""

from __future__ import annotations

import logging
from typing import Any

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery

logger = logging.getLogger(__name__)


async def safe_answer(query: CallbackQuery, *args: Any, **kwargs: Any) -> None:
    try:
        await query.answer(*args, **kwargs)
    except TelegramBadRequest as e:
        err = str(e).lower()
        if (
            "query is too old" in err
            or "response timeout expired" in err
            or "query id is invalid" in err
        ):
            logger.debug("Устаревший callback, answer пропущен: %s", e)
            return
        raise
