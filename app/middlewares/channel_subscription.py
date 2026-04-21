from __future__ import annotations

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware, Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, Message

from app import texts
from app.callback_safe import safe_answer
from app.keyboards.inline import subscription_keyboard
from app.services.channel_subscription import is_user_subscribed_to_channel
from app.services.users import clear_channel_verified, ensure_user, mark_channel_verified


class ChannelSubscriptionMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Any, dict[str, Any]], Awaitable[Any]],
        event: Any,
        data: dict[str, Any],
    ) -> Any:
        bot = data.get("bot")
        if not isinstance(bot, Bot):
            return await handler(event, data)

        if isinstance(event, Message):
            return await self._handle_message(handler, event, data, bot)
        if isinstance(event, CallbackQuery):
            return await self._handle_callback(handler, event, data, bot)
        return await handler(event, data)

    async def _handle_message(
        self,
        handler: Callable[[Any, dict[str, Any]], Awaitable[Any]],
        message: Message,
        data: dict[str, Any],
        bot: Bot,
    ) -> Any:
        if message.from_user is None:
            return await handler(message, data)

        text = (message.text or "").strip()
        if text.startswith("/start"):
            return await handler(message, data)

        await ensure_user(message.from_user)
        allowed = await self._is_subscribed(bot, message.from_user.id)
        if allowed is None:
            await message.answer(texts.CHECK_SUBSCRIPTION_FAILED_ALERT)
            return None
        if allowed:
            await mark_channel_verified(message.from_user.id)
            return await handler(message, data)

        await clear_channel_verified(message.from_user.id)
        await message.answer(
            texts.START_NEED_CHANNEL,
            reply_markup=subscription_keyboard(),
        )
        return None

    async def _handle_callback(
        self,
        handler: Callable[[Any, dict[str, Any]], Awaitable[Any]],
        query: CallbackQuery,
        data: dict[str, Any],
        bot: Bot,
    ) -> Any:
        if query.from_user is None:
            return await handler(query, data)
        if (query.data or "") == "check_sub":
            return await handler(query, data)

        await ensure_user(query.from_user)
        allowed = await self._is_subscribed(bot, query.from_user.id)
        if allowed is None:
            await safe_answer(query, texts.CHECK_SUBSCRIPTION_FAILED_ALERT, show_alert=True)
            return None
        if allowed:
            await mark_channel_verified(query.from_user.id)
            return await handler(query, data)

        await clear_channel_verified(query.from_user.id)
        await safe_answer(query, texts.NOT_SUBSCRIBED_ALERT, show_alert=True)
        if query.message is not None:
            try:
                await query.message.answer(
                    texts.START_NEED_CHANNEL,
                    reply_markup=subscription_keyboard(),
                )
            except TelegramBadRequest:
                pass
        return None

    async def _is_subscribed(self, bot: Bot, telegram_id: int) -> bool | None:
        try:
            return await is_user_subscribed_to_channel(bot, telegram_id)
        except TelegramBadRequest:
            return None
