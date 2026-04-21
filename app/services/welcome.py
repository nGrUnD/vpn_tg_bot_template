from __future__ import annotations

import logging

from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, FSInputFile, InputMediaPhoto, Message

from app import texts
from app.keyboards.inline import welcome_keyboard
from app.paths import WELCOME_IMAGE_PATH
from app.services.users import should_show_trial_menu_button

logger = logging.getLogger(__name__)


async def apply_welcome_screen_to_message(msg: Message, bot: Bot) -> None:
    """Показать welcome (фото + текст + клавиатура) вместо текущего сообщения."""
    uid = msg.from_user.id if msg.from_user else None
    show_trial = uid is None or await should_show_trial_menu_button(uid)
    kb = welcome_keyboard(show_trial=show_trial)
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
            logger.info("edit_media welcome не удался (%s), отправляю новое сообщение", e)
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


async def send_welcome(message: Message) -> None:
    """Приветствие после подписки или /start у подтверждённого пользователя."""
    show_trial = await should_show_trial_menu_button(message.from_user.id)
    kb = welcome_keyboard(show_trial=show_trial)
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
    await apply_welcome_screen_to_message(msg, bot)


async def show_welcome_on_message(query: CallbackQuery, bot: Bot) -> None:
    """Вернуться с экрана «Мои подключения» на welcome."""
    msg = query.message
    if msg is None:
        return
    await apply_welcome_screen_to_message(msg, bot)
