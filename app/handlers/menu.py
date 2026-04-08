from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery

from app.services.main_menu import apply_full_main_menu_to_message
from app.services.trial_connections import apply_trial_connections_screen
from app.services.welcome import show_welcome_on_message

router = Router(name="menu")


@router.callback_query(F.data == "main_menu")
async def on_open_main_menu(query: CallbackQuery, bot: Bot) -> None:
    """Из welcome — полное главное меню (картинка + 6 кнопок)."""
    await query.answer()
    await apply_full_main_menu_to_message(query, bot)


@router.callback_query(F.data == "trial_3d")
async def on_trial_3d_legacy(query: CallbackQuery, bot: Bot) -> None:
    """Старые клавиатуры с callback trial_3d."""
    await query.answer()
    await apply_trial_connections_screen(query, bot, back_to="welcome")


@router.callback_query(F.data.startswith("trial_start:"))
async def on_trial_start(query: CallbackQuery, bot: Bot) -> None:
    await query.answer()
    origin = query.data.split(":", 1)[1]
    back_to = "welcome" if origin == "welcome" else "main"
    await apply_trial_connections_screen(query, bot, back_to=back_to)


@router.callback_query(F.data.startswith("trial_back:"))
async def on_trial_back(query: CallbackQuery, bot: Bot) -> None:
    await query.answer()
    dest = query.data.split(":", 1)[1]
    if dest == "welcome":
        await show_welcome_on_message(query, bot)
    else:
        await apply_full_main_menu_to_message(query, bot)


@router.callback_query(F.data == "conn_windows")
async def on_conn_windows(query: CallbackQuery) -> None:
    await query.answer(
        "Страница подключения для Windows/Mac пока не настроена. "
        "Добавьте CONNECT_PAGE_WINDOWS_URL в .env",
        show_alert=True,
    )


@router.callback_query(F.data == "conn_iphone")
async def on_conn_iphone(query: CallbackQuery) -> None:
    await query.answer(
        "Страница для iPhone пока не настроена. Добавьте CONNECT_PAGE_IPHONE_URL в .env",
        show_alert=True,
    )


@router.callback_query(F.data == "conn_android")
async def on_conn_android(query: CallbackQuery) -> None:
    await query.answer(
        "Страница для Android пока не настроена. Добавьте CONNECT_PAGE_ANDROID_URL в .env",
        show_alert=True,
    )


@router.callback_query(F.data == "vpn_troubleshoot")
async def on_vpn_troubleshoot(query: CallbackQuery) -> None:
    await query.answer("Раздел «Не работает VPN» — в разработке.", show_alert=True)


@router.callback_query(F.data == "buy_access")
async def on_buy_access(query: CallbackQuery) -> None:
    await query.answer("Покупка доступа — в разработке.", show_alert=True)


@router.callback_query(F.data == "profile")
async def on_profile(query: CallbackQuery) -> None:
    await query.answer("Мой профиль — в разработке.", show_alert=True)


@router.callback_query(F.data == "support")
async def on_support(query: CallbackQuery) -> None:
    await query.answer("Техподдержка — в разработке.", show_alert=True)


@router.callback_query(F.data == "referral")
async def on_referral(query: CallbackQuery) -> None:
    await query.answer("Реферальная программа — в разработке.", show_alert=True)


@router.callback_query(F.data == "instructions")
async def on_instructions(query: CallbackQuery) -> None:
    await query.answer("Инструкции по подключению — в разработке.", show_alert=True)
