from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.config import settings


def subscription_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Подписаться",
                    url=settings.channel_url,
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Проверить",
                    callback_data="check_sub",
                ),
            ],
        ],
    )
