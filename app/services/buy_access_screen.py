from __future__ import annotations

import logging

from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, FSInputFile, InputMediaPhoto

from app import texts
from app.keyboards.inline import (
    buy_access_keyboard,
    buy_promo_keyboard,
    buy_rub_payment_keyboard,
    buy_rub_tariffs_keyboard,
)
from app.paths import (
    BUY_ACCESS_IMAGE_PATH,
    BUY_PROMO_IMAGE_PATH,
    BUY_RUB_PAYMENT_IMAGE_PATH,
    BUY_RUB_TARIFFS_IMAGE_PATH,
)

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


async def apply_buy_rub_tariffs_screen(
    query: CallbackQuery,
    bot: Bot,
    *,
    back_to: str,
) -> None:
    """Экран выбора тарифа (рубли)."""
    msg = query.message
    if msg is None:
        return

    caption = texts.BUY_RUB_TARIFFS_CAPTION
    kb = buy_rub_tariffs_keyboard(back_to=back_to)
    path = BUY_RUB_TARIFFS_IMAGE_PATH if BUY_RUB_TARIFFS_IMAGE_PATH.is_file() else BUY_ACCESS_IMAGE_PATH

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
            logger.info("edit_media buy_rub_tariffs не удался (%s), отправляю новое", e)
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

    logger.warning("Файл buy_rub_tariffs не найден: %s", path)
    try:
        await msg.edit_text(caption, parse_mode=ParseMode.HTML, reply_markup=kb)
    except TelegramBadRequest:
        await bot.send_message(
            msg.chat.id,
            caption,
            parse_mode=ParseMode.HTML,
            reply_markup=kb,
        )


async def apply_buy_promo_screen(
    query: CallbackQuery,
    bot: Bot,
    *,
    months: int,
    back_to: str,
) -> None:
    """Экран ввода промокода (после выбора тарифа)."""
    msg = query.message
    if msg is None:
        return

    caption = texts.BUY_PROMO_CAPTION
    kb = buy_promo_keyboard(months=months, back_to=back_to)
    path = BUY_PROMO_IMAGE_PATH if BUY_PROMO_IMAGE_PATH.is_file() else BUY_RUB_TARIFFS_IMAGE_PATH
    if not path.is_file():
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
            logger.info("edit_media buy_promo не удался (%s), отправляю новое", e)
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

    logger.warning("Файл buy_promo не найден: %s", path)
    try:
        await msg.edit_text(caption, parse_mode=ParseMode.HTML, reply_markup=kb)
    except TelegramBadRequest:
        await bot.send_message(
            msg.chat.id,
            caption,
            parse_mode=ParseMode.HTML,
            reply_markup=kb,
        )


async def apply_buy_rub_payment_screen(
    query: CallbackQuery,
    bot: Bot,
    *,
    months: int,
    back_to: str,
    pay_url: str | None = None,
) -> None:
    """Экран оплаты рублями (после промокода / «Пропустить»)."""
    msg = query.message
    if msg is None:
        return

    amount = texts.rub_tariff_amount_rub(months)
    caption = texts.buy_rub_payment_caption(amount)
    kb = buy_rub_payment_keyboard(months=months, back_to=back_to, pay_url=pay_url)
    path = (
        BUY_RUB_PAYMENT_IMAGE_PATH
        if BUY_RUB_PAYMENT_IMAGE_PATH.is_file()
        else BUY_PROMO_IMAGE_PATH
    )
    if not path.is_file():
        path = BUY_RUB_TARIFFS_IMAGE_PATH if BUY_RUB_TARIFFS_IMAGE_PATH.is_file() else BUY_ACCESS_IMAGE_PATH

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
            logger.info("edit_media buy_rub_payment не удался (%s), отправляю новое", e)
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

    logger.warning("Файл buy_rub_payment не найден: %s", path)
    try:
        await msg.edit_text(caption, parse_mode=ParseMode.HTML, reply_markup=kb)
    except TelegramBadRequest:
        await bot.send_message(
            msg.chat.id,
            caption,
            parse_mode=ParseMode.HTML,
            reply_markup=kb,
        )
