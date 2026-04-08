from __future__ import annotations

import logging

from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, FSInputFile, InputMediaPhoto

from app import texts
from app.keyboards.inline import main_menu_keyboard
from app.paths import MAIN_MENU_IMAGE_PATH

logger = logging.getLogger(__name__)


async def apply_full_main_menu_to_message(query: CallbackQuery, bot: Bot) -> None:
    """Текущее сообщение (welcome) заменить на экран полного главного меню."""
    msg = query.message
    if msg is None:
        return

    kb = main_menu_keyboard()
    path = MAIN_MENU_IMAGE_PATH

    if path.is_file():
        media = InputMediaPhoto(
            media=FSInputFile(path),
            caption=texts.MAIN_MENU_CAPTION,
            parse_mode=ParseMode.HTML,
        )
        try:
            await msg.edit_media(media=media, reply_markup=kb)
            return
        except TelegramBadRequest as e:
            logger.info("edit_media не удался (%s), отправляю новое сообщение", e)
            try:
                await msg.delete()
            except TelegramBadRequest:
                pass
            await bot.send_photo(
                chat_id=msg.chat.id,
                photo=FSInputFile(path),
                caption=texts.MAIN_MENU_CAPTION,
                parse_mode=ParseMode.HTML,
                reply_markup=kb,
            )
            return

    logger.warning("Файл главного меню не найден: %s", path)
    await msg.edit_text(
        texts.MAIN_MENU_CAPTION,
        parse_mode=ParseMode.HTML,
        reply_markup=kb,
    )
