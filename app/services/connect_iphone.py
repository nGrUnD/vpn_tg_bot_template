from __future__ import annotations

import logging
from pathlib import Path

from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, FSInputFile, InputMediaPhoto, InlineKeyboardMarkup

from app import texts
from app.keyboards.inline import iphone_guide_keyboard, iphone_instructions_apps_keyboard
from app.paths import INSTRUCTIONS_IOS_APPS_IMAGE_PATH, IPHONE_GUIDE_IMAGE_PATH

logger = logging.getLogger(__name__)


async def _apply_iphone_visual_screen(
    query: CallbackQuery,
    bot: Bot,
    *,
    caption: str,
    kb: InlineKeyboardMarkup,
    path: Path,
    log_label: str,
) -> None:
    msg = query.message
    if msg is None:
        return

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
            logger.info("edit_media %s не удался (%s), отправляю новое", log_label, e)
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

    logger.warning("Файл не найден (%s): %s", log_label, path)
    try:
        await msg.edit_text(caption, parse_mode=ParseMode.HTML, reply_markup=kb)
    except TelegramBadRequest:
        await bot.send_message(
            msg.chat.id,
            caption,
            parse_mode=ParseMode.HTML,
            reply_markup=kb,
        )


async def apply_iphone_instructions_apps_screen(
    query: CallbackQuery,
    bot: Bot,
    *,
    back_to: str,
) -> None:
    await _apply_iphone_visual_screen(
        query,
        bot,
        caption=texts.iphone_instructions_apps_caption(),
        kb=iphone_instructions_apps_keyboard(back_to=back_to),
        path=INSTRUCTIONS_IOS_APPS_IMAGE_PATH,
        log_label="iphone instructions apps",
    )


async def apply_iphone_guide_screen(
    query: CallbackQuery,
    bot: Bot,
    *,
    back_to: str,
    subscription_url: str | None,
    back_callback_data: str | None = None,
) -> None:
    await _apply_iphone_visual_screen(
        query,
        bot,
        caption=texts.iphone_guide_caption(subscription_url),
        kb=iphone_guide_keyboard(back_to=back_to, back_callback_data=back_callback_data),
        path=IPHONE_GUIDE_IMAGE_PATH,
        log_label="iphone guide",
    )
