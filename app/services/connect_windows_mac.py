from __future__ import annotations

import logging

from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, FSInputFile, InputMediaPhoto

from app import texts
from app.keyboards.inline import windows_mac_guide_keyboard, windows_mac_instructions_keyboard
from app.paths import INSTRUCTIONS_WINDOWS_MAC_IMAGE_PATH, WINDOWS_MAC_GUIDE_IMAGE_PATH

logger = logging.getLogger(__name__)


async def apply_windows_mac_guide_screen(
    query: CallbackQuery,
    bot: Bot,
    *,
    back_to: str,
    subscription_url: str | None,
    back_callback_data: str | None = None,
    from_instructions: bool = False,
) -> None:
    msg = query.message
    if msg is None:
        return

    if from_instructions:
        caption = texts.windows_mac_instructions_caption()
        kb = windows_mac_instructions_keyboard(back_to=back_to)
        path = (
            INSTRUCTIONS_WINDOWS_MAC_IMAGE_PATH
            if INSTRUCTIONS_WINDOWS_MAC_IMAGE_PATH.is_file()
            else WINDOWS_MAC_GUIDE_IMAGE_PATH
        )
    else:
        caption = texts.windows_mac_guide_caption(subscription_url)
        kb = windows_mac_guide_keyboard(back_to=back_to, back_callback_data=back_callback_data)
        path = WINDOWS_MAC_GUIDE_IMAGE_PATH

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
            logger.info("edit_media windows_mac guide не удался (%s), отправляю новое", e)
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

    logger.warning("Файл инструкции Windows/Mac не найден: %s", path)
    try:
        await msg.edit_text(caption, parse_mode=ParseMode.HTML, reply_markup=kb)
    except TelegramBadRequest:
        await bot.send_message(
            msg.chat.id,
            caption,
            parse_mode=ParseMode.HTML,
            reply_markup=kb,
        )
