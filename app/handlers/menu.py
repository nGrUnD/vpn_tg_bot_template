from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery

from app import texts
from app.callback_safe import safe_answer
from app.services.main_menu import apply_full_main_menu_to_message
from app.services.profile_screen import apply_profile_screen
from app.services.threexui_backends import ThreexuiRuntime
from app.services.trial_activate import run_trial_activation_flow
from app.services.trial_connections import apply_trial_connections_screen
from app.services.users import ensure_user, get_trial_subscription_url, trial_still_active
from app.services.welcome import show_welcome_on_message

router = Router(name="menu")


@router.callback_query(F.data == "main_menu")
async def on_open_main_menu(query: CallbackQuery, bot: Bot) -> None:
    """Из welcome — полное главное меню (картинка + 6 кнопок)."""
    await safe_answer(query)
    await apply_full_main_menu_to_message(query, bot)


@router.callback_query(F.data == "trial_3d")
async def on_trial_3d_legacy(query: CallbackQuery, bot: Bot, threexui_runtime: ThreexuiRuntime) -> None:
    """Старые клавиатуры с callback trial_3d."""
    await run_trial_activation_flow(query, bot, back_to="welcome", threexui_runtime=threexui_runtime)


@router.callback_query(F.data.startswith("trial_start:"))
async def on_trial_start(query: CallbackQuery, bot: Bot, threexui_runtime: ThreexuiRuntime) -> None:
    origin = query.data.split(":", 1)[1]
    back_to = "welcome" if origin == "welcome" else "main"
    await run_trial_activation_flow(query, bot, back_to=back_to, threexui_runtime=threexui_runtime)


@router.callback_query(F.data.startswith("trial_back:"))
async def on_trial_back(query: CallbackQuery, bot: Bot) -> None:
    await safe_answer(query)
    dest = query.data.split(":", 1)[1]
    if dest == "welcome":
        await show_welcome_on_message(query, bot)
    elif dest == "profile":
        await apply_profile_screen(query, bot)
    else:
        await apply_full_main_menu_to_message(query, bot)


@router.callback_query(F.data == "conn_windows")
async def on_conn_windows(query: CallbackQuery) -> None:
    await safe_answer(
        query,
        "Страница подключения для Windows/Mac пока не настроена. "
        "Добавьте CONNECT_PAGE_WINDOWS_URL в .env",
        show_alert=True,
    )


@router.callback_query(F.data == "conn_iphone")
async def on_conn_iphone(query: CallbackQuery) -> None:
    await safe_answer(
        query,
        "Страница для iPhone пока не настроена. Добавьте CONNECT_PAGE_IPHONE_URL в .env",
        show_alert=True,
    )


@router.callback_query(F.data == "conn_android")
async def on_conn_android(query: CallbackQuery) -> None:
    await safe_answer(
        query,
        "Страница для Android пока не настроена. Добавьте CONNECT_PAGE_ANDROID_URL в .env",
        show_alert=True,
    )


@router.callback_query(F.data == "vpn_troubleshoot")
async def on_vpn_troubleshoot(query: CallbackQuery) -> None:
    await safe_answer(query, "Раздел «Не работает VPN» — в разработке.", show_alert=True)


@router.callback_query(F.data == "buy_access")
async def on_buy_access(query: CallbackQuery) -> None:
    await safe_answer(query, "Покупка доступа — в разработке.", show_alert=True)


@router.callback_query(F.data == "profile")
async def on_profile(query: CallbackQuery, bot: Bot) -> None:
    await safe_answer(query)
    if query.from_user is not None:
        await ensure_user(query.from_user)
    await apply_profile_screen(query, bot)


@router.callback_query(F.data == "profile_connections")
async def on_profile_connections(query: CallbackQuery, bot: Bot) -> None:
    await safe_answer(query)
    if query.from_user is None:
        return
    await ensure_user(query.from_user)
    tid = query.from_user.id
    if await trial_still_active(tid):
        sub = await get_trial_subscription_url(tid)
        await apply_trial_connections_screen(
            query,
            bot,
            back_to="profile",
            subscription_url=sub,
        )
    else:
        await apply_trial_connections_screen(
            query,
            bot,
            back_to="profile",
            caption_html=texts.connections_no_access_caption(),
        )


@router.callback_query(F.data == "profile_back_main")
async def on_profile_back_main(query: CallbackQuery, bot: Bot) -> None:
    await safe_answer(query)
    await apply_full_main_menu_to_message(query, bot)


@router.callback_query(F.data == "support")
async def on_support(query: CallbackQuery) -> None:
    await safe_answer(query, "Техподдержка — в разработке.", show_alert=True)


@router.callback_query(F.data == "referral")
async def on_referral(query: CallbackQuery) -> None:
    await safe_answer(query, "Реферальная программа — в разработке.", show_alert=True)


@router.callback_query(F.data == "instructions")
async def on_instructions(query: CallbackQuery) -> None:
    await safe_answer(query, "Инструкции по подключению — в разработке.", show_alert=True)
