from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.config import settings
from app.ru_plural import trial_button_caption


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
                    callback_data="instructions:main",
                ),
            ],
        ],
    )


def instructions_keyboard(*, back_to: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Android 📱",
                    callback_data=f"instructions_android:{back_to}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="iPhone 🍏",
                    callback_data=f"iphone_instr_hub:i:{back_to}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Windows/Mac 💻",
                    callback_data=f"instructions_windows:{back_to}",
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


def trial_connections_keyboard(*, back_to: str) -> InlineKeyboardMarkup:
    """
    back_to: «welcome», «main» или «profile» — куда ведёт «Назад».
    """
    rows: list[list[InlineKeyboardButton]] = [
        [
            InlineKeyboardButton(
                text="Windows/Mac 💻",
                callback_data=f"conn_windows:{back_to}",
            ),
        ],
        [
            InlineKeyboardButton(
                text="iPhone 🍏",
                callback_data=f"conn_iphone:{back_to}",
            ),
        ],
        [
            InlineKeyboardButton(
                text="Android 📱",
                callback_data=f"conn_android:{back_to}",
            ),
        ],
        [
            InlineKeyboardButton(
                text="🔎 Не работает VPN?",
                callback_data=f"vpn_troubleshoot:{back_to}",
            ),
        ],
        [
            InlineKeyboardButton(
                text="📝 Инструкции по подключению",
                callback_data=f"instructions:{back_to}",
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


def android_trial_guide_keyboard(*, back_to: str) -> InlineKeyboardMarkup:
    inst = settings.android_instruction_url
    inst_row = (
        [InlineKeyboardButton(text="Инструкция для Android", url=inst)]
        if inst
        else [
            InlineKeyboardButton(
                text="Инструкция для Android",
                callback_data="android_instruction",
            ),
        ]
    )
    return InlineKeyboardMarkup(
        inline_keyboard=[
            inst_row,
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


def android_apps_choice_keyboard(
    *,
    back_callback_data: str,
    happ_callback_data: str,
    hiddify_callback_data: str,
    v2raytun_callback_data: str,
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⭐️ Рекомендуем Happ",
                    callback_data=happ_callback_data,
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Hiddify",
                    callback_data=hiddify_callback_data,
                ),
            ],
            [
                InlineKeyboardButton(
                    text="V2RayTun",
                    callback_data=v2raytun_callback_data,
                ),
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data=back_callback_data,
                ),
            ],
        ],
    )


def android_instructions_android_sub_keyboard(*, back_to: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data=f"instructions_android:{back_to}",
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


def iphone_instructions_apps_keyboard(*, back_to: str, parent: str) -> InlineKeyboardMarkup:
    """parent: «i» — из меню инструкций, «t» — с экрана «Мои подключения» → iPhone."""
    hub_back = f"instructions:{back_to}" if parent == "i" else f"conn_iphone:{back_to}"
    p = parent
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⭐️ Рекомендуем Happ",
                    callback_data=f"iphone_instr_happ:{p}:{back_to}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Hiddify",
                    callback_data=f"iphone_instr_hiddify:{p}:{back_to}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="V2RayTun",
                    callback_data=f"iphone_instr_v2raytun:{p}:{back_to}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data=hub_back,
                ),
            ],
        ],
    )


def iphone_instructions_ios_detail_keyboard(*, parent: str, back_to: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data=f"iphone_instr_hub:{parent}:{back_to}",
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


def iphone_guide_keyboard(
    *,
    back_to: str,
    back_callback_data: str | None = None,
) -> InlineKeyboardMarkup:
    back_row = back_callback_data if back_callback_data is not None else f"trial_back:{back_to}"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📝 Инструкции по подключению",
                    callback_data=f"iphone_instr_hub:t:{back_to}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Подключить другое устройство",
                    callback_data=f"trial_devices:{back_to}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data=back_row,
                ),
            ],
        ],
    )


def windows_mac_guide_keyboard(
    *,
    back_to: str,
    back_callback_data: str | None = None,
) -> InlineKeyboardMarkup:
    back_row = back_callback_data if back_callback_data is not None else f"trial_back:{back_to}"
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
                    callback_data=back_row,
                ),
            ],
        ],
    )


def windows_mac_instructions_keyboard(*, back_to: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data=f"instructions:{back_to}",
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


def vpn_troubleshoot_actions_keyboard(*, back_to: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⭐️ Мои подключения",
                    callback_data=f"trial_devices:{back_to}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🛠 Тех поддержка",
                    callback_data="support",
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
