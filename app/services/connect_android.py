from __future__ import annotations

import logging
from typing import Literal

from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, FSInputFile, InputMediaPhoto

from app import texts
from app.keyboards.inline import android_apps_choice_keyboard
from app.paths import ANDROID_GUIDE_IMAGE_PATH

logger = logging.getLogger(__name__)


async def apply_android_guide_screen(
    query: CallbackQuery,
    bot: Bot,
    *,
    back_to: str,
    back_navigation: Literal["trial", "instructions"] = "trial",
) -> None:
    msg = query.message
    if msg is None:
        return

    caption = texts.android_apps_instruction_caption()
    back_cb = (
        f"instructions:{back_to}"
        if back_navigation == "instructions"
        else f"trial_back:{back_to}"
    )
    kb = android_apps_choice_keyboard(back_callback_data=back_cb)
    path = ANDROID_GUIDE_IMAGE_PATH

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
            logger.info("edit_media android guide не удался (%s), отправляю новое", e)
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

    logger.warning("Файл инструкции Android не найден: %s", path)
    try:
        await msg.edit_text(caption, parse_mode=ParseMode.HTML, reply_markup=kb)
    except TelegramBadRequest:
        await bot.send_message(
            msg.chat.id,
            caption,
            parse_mode=ParseMode.HTML,
            reply_markup=kb,
        )
