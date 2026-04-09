from __future__ import annotations

import logging

from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, FSInputFile, InputMediaPhoto

from app import texts
from app.keyboards.inline import iphone_guide_keyboard
from app.paths import IPHONE_GUIDE_IMAGE_PATH

logger = logging.getLogger(__name__)


async def apply_iphone_guide_screen(
    query: CallbackQuery,
    bot: Bot,
    *,
    back_to: str,
    subscription_url: str | None,
    back_callback_data: str | None = None,
) -> None:
    msg = query.message
    if msg is None:
        return

    caption = texts.iphone_guide_caption(subscription_url)
    kb = iphone_guide_keyboard(back_to=back_to, back_callback_data=back_callback_data)
    path = IPHONE_GUIDE_IMAGE_PATH

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
            logger.info("edit_media iphone guide не удался (%s), отправляю новое", e)
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

    logger.warning("Файл инструкции iPhone не найден: %s", path)
    try:
        await msg.edit_text(caption, parse_mode=ParseMode.HTML, reply_markup=kb)
    except TelegramBadRequest:
        await bot.send_message(
            msg.chat.id,
            caption,
            parse_mode=ParseMode.HTML,
            reply_markup=kb,
        )
