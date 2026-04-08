from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.config import settings


def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🩵 Получить 3 дня",
                    callback_data="trial_3d",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🛒 Купить доступ",
                    callback_data="buy_access",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="📌 Главное меню",
                    callback_data="main_menu",
                ),
            ],
        ],
    )


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
