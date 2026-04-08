from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.config import settings


def welcome_keyboard() -> InlineKeyboardMarkup:
    """После проверки подписки: три кнопки."""
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


def main_menu_keyboard() -> InlineKeyboardMarkup:
    """Полное главное меню (после кнопки «Главное меню»)."""
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
                    text="👤 Мой профиль",
                    callback_data="profile",
                ),
                InlineKeyboardButton(
                    text="🛠 Тех поддержка",
                    callback_data="support",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🎁 Реферальная программа",
                    callback_data="referral",
                ),
                InlineKeyboardButton(
                    text="📝 Инструкции по подключению",
                    callback_data="instructions",
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
