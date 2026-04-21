from __future__ import annotations

import logging
from pathlib import Path

from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, FSInputFile, InputMediaPhoto, InlineKeyboardMarkup

from app import texts
from app.services.users import get_active_access
from app.keyboards.inline import (
    android_apps_choice_keyboard,
    android_instructions_android_sub_keyboard,
    android_trial_guide_keyboard,
)
from app.paths import (
    ANDROID_INSTRUCTIONS_APPS_IMAGE_PATH,
    ANDROID_INSTRUCTIONS_HAPP_IMAGE_PATH,
    ANDROID_INSTRUCTIONS_HIDDIFY_IMAGE_PATH,
    ANDROID_INSTRUCTIONS_V2RAYTUN_IMAGE_PATH,
    ANDROID_TRIAL_GUIDE_IMAGE_PATH,
)

logger = logging.getLogger(__name__)


async def _apply_photo_screen(
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


async def apply_android_trial_guide_screen(
    query: CallbackQuery,
    bot: Bot,
    *,
    back_to: str,
    subscription_url: str | None,
) -> None:
    tid = query.from_user.id if query.from_user else 0
    has_active = (await get_active_access(tid)) is not None if tid else False
    await _apply_photo_screen(
        query,
        bot,
        caption=texts.android_trial_guide_caption(
            subscription_url,
            has_active_access=has_active,
        ),
        kb=android_trial_guide_keyboard(back_to=back_to),
        path=ANDROID_TRIAL_GUIDE_IMAGE_PATH,
        log_label="android trial",
    )


async def apply_android_instructions_apps_screen(
    query: CallbackQuery,
    bot: Bot,
    *,
    back_to: str,
) -> None:
    kb = android_apps_choice_keyboard(
        back_callback_data=f"instructions:{back_to}",
        happ_callback_data=f"instructions_android_happ:{back_to}",
        hiddify_callback_data=f"instructions_android_hiddify:{back_to}",
        v2raytun_callback_data=f"instructions_android_v2raytun:{back_to}",
    )
    await _apply_photo_screen(
        query,
        bot,
        caption=texts.android_apps_instruction_caption(),
        kb=kb,
        path=ANDROID_INSTRUCTIONS_APPS_IMAGE_PATH,
        log_label="android instructions apps",
    )


async def apply_android_happ_detail_screen(
    query: CallbackQuery,
    bot: Bot,
    *,
    back_to: str,
) -> None:
    await _apply_photo_screen(
        query,
        bot,
        caption=texts.android_happ_instruction_caption(),
        kb=android_instructions_android_sub_keyboard(back_to=back_to),
        path=ANDROID_INSTRUCTIONS_HAPP_IMAGE_PATH,
        log_label="android happ detail",
    )


async def apply_android_hiddify_detail_screen(
    query: CallbackQuery,
    bot: Bot,
    *,
    back_to: str,
) -> None:
    await _apply_photo_screen(
        query,
        bot,
        caption=texts.android_hiddify_instruction_caption(),
        kb=android_instructions_android_sub_keyboard(back_to=back_to),
        path=ANDROID_INSTRUCTIONS_HIDDIFY_IMAGE_PATH,
        log_label="android hiddify detail",
    )


async def apply_android_v2raytun_detail_screen(
    query: CallbackQuery,
    bot: Bot,
    *,
    back_to: str,
) -> None:
    await _apply_photo_screen(
        query,
        bot,
        caption=texts.android_v2raytun_instruction_caption(),
        kb=android_instructions_android_sub_keyboard(back_to=back_to),
        path=ANDROID_INSTRUCTIONS_V2RAYTUN_IMAGE_PATH,
        log_label="android v2raytun detail",
    )
