from __future__ import annotations

import logging

from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, FSInputFile, InputMediaPhoto

from app import texts
from app.keyboards.inline import vpn_troubleshoot_actions_keyboard
from app.paths import VPN_TROUBLESHOOT_IMAGE_PATH, VPN_TROUBLESHOOT_SUCCESS_IMAGE_PATH
from app.services.threexui_backends import ThreexuiRuntime
from app.services.vpn_reissue import reissue_trial_cross_panel

logger = logging.getLogger(__name__)


async def run_vpn_troubleshoot_reissue(
    query: CallbackQuery,
    bot: Bot,
    telegram_id: int,
    *,
    back_to: str,
    runtime: ThreexuiRuntime,
) -> None:
    msg = query.message
    if msg is None:
        return

    kb = vpn_troubleshoot_actions_keyboard(back_to=back_to)
    caption = texts.VPN_TROUBLESHOOT_PROCESSING_CAPTION
    path = VPN_TROUBLESHOOT_IMAGE_PATH

    if path.is_file():
        media = InputMediaPhoto(
            media=FSInputFile(path),
            caption=caption,
            parse_mode=ParseMode.HTML,
        )
        try:
            await msg.edit_media(media=media, reply_markup=kb)
        except TelegramBadRequest as e:
            logger.info("edit_media vpn_troubleshoot не удался (%s), отправляю новое", e)
            try:
                await msg.delete()
            except TelegramBadRequest:
                pass
            sent = await bot.send_photo(
                chat_id=msg.chat.id,
                photo=FSInputFile(path),
                caption=caption,
                parse_mode=ParseMode.HTML,
                reply_markup=kb,
            )
            msg = sent
    else:
        logger.warning("Файл vpn_troubleshoot не найден: %s", path)
        try:
            await msg.edit_text(
                caption,
                parse_mode=ParseMode.HTML,
                reply_markup=kb,
            )
        except TelegramBadRequest:
            sent = await bot.send_message(
                chat_id=msg.chat.id,
                text=caption,
                parse_mode=ParseMode.HTML,
                reply_markup=kb,
            )
            msg = sent

    ok, detail = await reissue_trial_cross_panel(telegram_id, runtime)
    final_caption = texts.VPN_REISSUE_SUCCESS_CAPTION if ok else texts.vpn_reissue_error_caption(detail)
    success_path = VPN_TROUBLESHOOT_SUCCESS_IMAGE_PATH

    try:
        if ok and success_path.is_file():
            smedia = InputMediaPhoto(
                media=FSInputFile(success_path),
                caption=final_caption,
                parse_mode=ParseMode.HTML,
            )
            if msg.photo:
                await msg.edit_media(media=smedia, reply_markup=kb)
            else:
                try:
                    await msg.delete()
                except TelegramBadRequest:
                    pass
                await bot.send_photo(
                    chat_id=msg.chat.id,
                    photo=FSInputFile(success_path),
                    caption=final_caption,
                    parse_mode=ParseMode.HTML,
                    reply_markup=kb,
                )
        elif path.is_file() and msg.photo:
            await msg.edit_caption(
                final_caption,
                parse_mode=ParseMode.HTML,
                reply_markup=kb,
            )
        else:
            await msg.edit_text(
                final_caption,
                parse_mode=ParseMode.HTML,
                reply_markup=kb,
            )
    except TelegramBadRequest as e:
        logger.warning("vpn_troubleshoot result edit failed: %s", e)
