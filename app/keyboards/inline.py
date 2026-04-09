from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.config import settings
from app.ru_plural import trial_button_caption


def _device_button(text: str, url: str | None, callback_data: str) -> InlineKeyboardButton:
    if url:
        return InlineKeyboardButton(text=text, url=url)
    return InlineKeyboardButton(text=text, callback_data=callback_data)


def welcome_keyboard() -> InlineKeyboardMarkup:
    """После проверки подписки: три кнопки."""
    days = settings.trial_days
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=trial_button_caption(days),
                    callback_data="trial_start:welcome",
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
    days = settings.trial_days
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=trial_button_caption(days),
                    callback_data="trial_start:main",
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


def trial_connections_keyboard(*, back_to: str) -> InlineKeyboardMarkup:
    """
    back_to: «welcome», «main» или «profile» — куда ведёт «Назад».
    """
    s = settings
    rows: list[list[InlineKeyboardButton]] = [
        [
            InlineKeyboardButton(
                text="Windows/Mac 💻",
                callback_data=f"conn_windows:{back_to}",
            ),
        ],
        [
            _device_button(
                "iPhone 🍏",
                s.connect_page_iphone_url,
                "conn_iphone",
            ),
        ],
        [
            _device_button(
                "Android 📱",
                s.connect_page_android_url,
                "conn_android",
            ),
        ],
        [
            InlineKeyboardButton(
                text="🔎 Не работает VPN?",
                callback_data="vpn_troubleshoot",
            ),
        ],
        [
            InlineKeyboardButton(
                text="📝 Инструкции по подключению",
                callback_data="instructions",
            ),
        ],
        [
            InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data=f"trial_back:{back_to}",
            ),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def profile_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⭐️ Мои подключения",
                    callback_data="profile_connections",
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
                    text="🎁 Реферальная программа",
                    callback_data="referral",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data="profile_back_main",
                ),
            ],
        ],
    )


def windows_mac_guide_keyboard(*, back_to: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Подключить другое устройство",
                    callback_data=f"trial_devices:{back_to}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data=f"trial_back:{back_to}",
                ),
            ],
        ],
    )


def support_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⬅️ Назад",
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
