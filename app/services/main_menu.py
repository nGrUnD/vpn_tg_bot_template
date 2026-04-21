from __future__ import annotations

import logging

from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, FSInputFile, InputMediaPhoto

from app import texts
from app.keyboards.inline import main_menu_keyboard
from app.paths import MAIN_MENU_IMAGE_PATH
from app.services.users import paid_still_active, should_show_trial_menu_button

logger = logging.getLogger(__name__)


async def apply_full_main_menu_to_message(query: CallbackQuery, bot: Bot) -> None:
    """Текущее сообщение (welcome) заменить на экран полного главного меню."""
    msg = query.message
    if msg is None:
        return

    uid = query.from_user.id if query.from_user else None
    show_trial = uid is None or await should_show_trial_menu_button(uid)
    buy_extend = bool(uid is not None and await paid_still_active(uid))
    kb = main_menu_keyboard(show_trial=show_trial, buy_extend=buy_extend)
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
