from __future__ import annotations

import logging

from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, FSInputFile, InputMediaPhoto

from app import texts
from app.config import settings
from app.keyboards.inline import trial_connections_keyboard
from app.paths import MY_CONNECTIONS_IMAGE_PATH

logger = logging.getLogger(__name__)


async def apply_trial_connections_screen(query: CallbackQuery, bot: Bot, *, back_to: str) -> None:
    """Экран «Мои подключения» после активации пробного периода."""
    msg = query.message
    if msg is None:
        return

    days = settings.trial_days
    caption = texts.trial_connections_caption(days)
    kb = trial_connections_keyboard(back_to=back_to)
    path = MY_CONNECTIONS_IMAGE_PATH

    if path.is_file():
        media = InputMediaPhoto(
            media=FSInputFile(path),
            caption=caption,
            parse_mode=ParseMode.HTML,
        )
        try:
            await msg.edit_media(media=media, reply_markup=kb)
            return
        except TelegramBadRequest as e:
            logger.info("edit_media trial_connections не удался (%s), отправляю новое", e)
            try:
                await msg.delete()
            except TelegramBadRequest:
                pass
            await bot.send_photo(
                chat_id=msg.chat.id,
                photo=FSInputFile(path),
                caption=caption,
                parse_mode=ParseMode.HTML,
                reply_markup=kb,
            )
            return

    logger.warning("Файл my_connections не найден: %s", path)
    await msg.edit_text(
        caption,
        parse_mode=ParseMode.HTML,
        reply_markup=kb,
    )
