import logging

from aiogram import Bot, F, Router
from aiogram.enums import ChatMemberStatus
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, Message

from app import texts
from app.callback_safe import safe_answer
from app.config import settings
from app.keyboards.inline import subscription_keyboard
from app.services.users import ensure_user, mark_channel_verified
from app.services.welcome import replace_subscription_with_welcome, send_welcome

logger = logging.getLogger(__name__)

router = Router(name="start")

_ALLOWED_STATUSES = frozenset(
    {
        ChatMemberStatus.MEMBER,
        ChatMemberStatus.ADMINISTRATOR,
        ChatMemberStatus.CREATOR,
    }
)


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    if message.from_user is None:
        return

    user = await ensure_user(message.from_user)

    if user["channel_verified_at"] is not None:
        await send_welcome(message)
        return

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
        member = await bot.get_chat_member(
            settings.channel_username,
            query.from_user.id,
        )
    except TelegramBadRequest as e:
        logger.warning("get_chat_member failed: %s", e)
        await safe_answer(query, texts.CHECK_SUBSCRIPTION_FAILED_ALERT, show_alert=True)
        return

    if member.status not in _ALLOWED_STATUSES:
        await safe_answer(query, texts.NOT_SUBSCRIBED_ALERT, show_alert=True)
        return

    await mark_channel_verified(query.from_user.id)
    await safe_answer(query)
    await replace_subscription_with_welcome(query, bot)
