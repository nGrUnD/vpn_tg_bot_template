import logging

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, Message

from app import texts
from app.callback_safe import safe_answer
from app.keyboards.inline import subscription_keyboard
from app.services.channel_subscription import is_user_subscribed_to_channel
from app.services.users import clear_channel_verified, ensure_user, mark_channel_verified
from app.services.welcome import replace_subscription_with_welcome, send_welcome

logger = logging.getLogger(__name__)

router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(message: Message, bot: Bot) -> None:
    if message.from_user is None:
        return

    await ensure_user(message.from_user)
    try:
        subscribed = await is_user_subscribed_to_channel(bot, message.from_user.id)
    except TelegramBadRequest as e:
        logger.warning("get_chat_member failed on /start: %s", e)
        await message.answer(texts.CHECK_SUBSCRIPTION_FAILED_ALERT)
        return

    if subscribed:
        await mark_channel_verified(message.from_user.id)
        await send_welcome(message)
        return

    await clear_channel_verified(message.from_user.id)
    await message.answer(
        texts.START_NEED_CHANNEL,
        reply_markup=subscription_keyboard(),
    )


@router.callback_query(F.data == "check_sub")
async def on_check_subscription(
    query: CallbackQuery,
    bot: Bot,
) -> None:
    if query.from_user is None or query.message is None:
        return

    await ensure_user(query.from_user)

    try:
        subscribed = await is_user_subscribed_to_channel(bot, query.from_user.id)
    except TelegramBadRequest as e:
        logger.warning("get_chat_member failed: %s", e)
        await safe_answer(query, texts.CHECK_SUBSCRIPTION_FAILED_ALERT, show_alert=True)
        return

    if not subscribed:
        await clear_channel_verified(query.from_user.id)
        await safe_answer(query, texts.NOT_SUBSCRIBED_ALERT, show_alert=True)
        return

    await mark_channel_verified(query.from_user.id)
    await safe_answer(query)
    await replace_subscription_with_welcome(query, bot)
