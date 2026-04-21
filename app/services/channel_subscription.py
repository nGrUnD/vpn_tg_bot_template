from __future__ import annotations

import logging

from aiogram import Bot
from aiogram.enums import ChatMemberStatus
from aiogram.exceptions import TelegramBadRequest

from app.config import settings

logger = logging.getLogger(__name__)

ALLOWED_CHANNEL_MEMBER_STATUSES = frozenset(
    {
        ChatMemberStatus.MEMBER,
        ChatMemberStatus.ADMINISTRATOR,
        ChatMemberStatus.CREATOR,
    }
)


async def is_user_subscribed_to_channel(bot: Bot, telegram_id: int) -> bool:
    try:
        member = await bot.get_chat_member(settings.channel_username, telegram_id)
    except TelegramBadRequest as e:
        logger.warning("get_chat_member failed: %s", e)
        raise
    return member.status in ALLOWED_CHANNEL_MEMBER_STATUSES
