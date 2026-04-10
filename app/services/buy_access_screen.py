from __future__ import annotations

import logging

from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, FSInputFile, InputMediaPhoto

from app import texts
from app.keyboards.inline import buy_access_keyboard
from app.paths import BUY_ACCESS_IMAGE_PATH

logger = logging.getLogger(__name__)


async def apply_buy_access_screen(
    query: CallbackQuery,
    bot: Bot,
    *,
    back_to: str,
) -> None:
    msg = query.message
    if msg is None:
        return

    caption = texts.BUY_ACCESS_CAPTION
    kb = buy_access_keyboard(back_to=back_to)
    path = BUY_ACCESS_IMAGE_PATH

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
            logger.info("edit_media buy_access не удался (%s), отправляю новое", e)
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

    logger.warning("Файл buy_access не найден: %s", path)
    try:
        await msg.edit_text(caption, parse_mode=ParseMode.HTML, reply_markup=kb)
    except TelegramBadRequest:
        await bot.send_message(
            msg.chat.id,
            caption,
            parse_mode=ParseMode.HTML,
            reply_markup=kb,
        )
