from __future__ import annotations

import logging

from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, FSInputFile, InputMediaPhoto, Message

from app import texts
from app.keyboards.inline import welcome_keyboard
from app.paths import WELCOME_IMAGE_PATH

logger = logging.getLogger(__name__)


async def send_welcome(message: Message) -> None:
    """Приветствие после подписки или /start у подтверждённого пользователя."""
    kb = welcome_keyboard()
    path = WELCOME_IMAGE_PATH
    if path.is_file():
        await message.answer_photo(
            photo=FSInputFile(path),
            caption=texts.WELCOME_CAPTION,
            parse_mode=ParseMode.HTML,
            reply_markup=kb,
        )
    else:
        logger.warning("Файл приветствия не найден: %s", path)
        await message.answer(
            texts.WELCOME_CAPTION,
            parse_mode=ParseMode.HTML,
            reply_markup=kb,
        )


async def replace_subscription_with_welcome(query: CallbackQuery, bot: Bot) -> None:
    """Сообщение «Проверить» заменить на welcome-картинку и текст."""
    msg = query.message
    if msg is None:
        return

    kb = welcome_keyboard()
    path = WELCOME_IMAGE_PATH

    if path.is_file():
        media = InputMediaPhoto(
            media=FSInputFile(path),
            caption=texts.WELCOME_CAPTION,
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
                caption=texts.WELCOME_CAPTION,
                parse_mode=ParseMode.HTML,
                reply_markup=kb,
            )
            return

    logger.warning("Файл приветствия не найден: %s", path)
    await msg.edit_text(
        texts.WELCOME_CAPTION,
        parse_mode=ParseMode.HTML,
        reply_markup=kb,
    )
