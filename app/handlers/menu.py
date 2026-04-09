from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery

from app import texts
from app.callback_safe import safe_answer
from app.services.main_menu import apply_full_main_menu_to_message
from app.services.profile_screen import apply_profile_screen
from app.services.support_screen import apply_support_screen
from app.services.threexui_backends import ThreexuiRuntime
from app.services.trial_activate import run_trial_activation_flow
from app.services.connect_android import (
    apply_android_happ_detail_screen,
    apply_android_hiddify_detail_screen,
    apply_android_instructions_apps_screen,
    apply_android_trial_guide_screen,
    apply_android_v2raytun_detail_screen,
)
from app.services.connect_iphone import (
    apply_iphone_guide_screen,
    apply_iphone_instructions_apps_screen,
    apply_iphone_instr_happ_detail_screen,
    apply_iphone_instr_hiddify_detail_screen,
    apply_iphone_instr_v2raytun_detail_screen,
    parse_iphone_instr_cb,
)
from app.services.connect_windows_mac import apply_windows_mac_guide_screen
from app.services.trial_connections import apply_trial_connections_screen
from app.services.instructions_screen import apply_instructions_screen
from app.services.vpn_troubleshoot_screen import run_vpn_troubleshoot_reissue
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


@router.callback_query(
    lambda q: (q.data or "") == "conn_windows" or (q.data or "").startswith("conn_windows:")
)
async def on_conn_windows(query: CallbackQuery, bot: Bot) -> None:
    await safe_answer(query)
    raw = query.data or ""
    back_to = raw.split(":", 1)[1] if raw.startswith("conn_windows:") else "main"
    if query.from_user is None:
        return
    await ensure_user(query.from_user)
    tid = query.from_user.id
    sub: str | None = None
    if await trial_still_active(tid):
        sub = await get_trial_subscription_url(tid)
    await apply_windows_mac_guide_screen(query, bot, back_to=back_to, subscription_url=sub)


@router.callback_query(F.data.startswith("instructions_windows:"))
async def on_instructions_windows(query: CallbackQuery, bot: Bot) -> None:
    await safe_answer(query)
    back_to = (query.data or "").split(":", 1)[1]
    if query.from_user is None:
        return
    await ensure_user(query.from_user)
    tid = query.from_user.id
    sub: str | None = None
    if await trial_still_active(tid):
        sub = await get_trial_subscription_url(tid)
    await apply_windows_mac_guide_screen(
        query,
        bot,
        back_to=back_to or "main",
        subscription_url=sub,
        back_callback_data=f"instructions:{back_to or 'main'}",
    )


@router.callback_query(F.data.startswith("trial_devices:"))
async def on_trial_devices(query: CallbackQuery, bot: Bot) -> None:
    await safe_answer(query)
    back_to = (query.data or "").split(":", 1)[1]
    if query.from_user is None:
        return
    await ensure_user(query.from_user)
    tid = query.from_user.id
    if await trial_still_active(tid):
        sub = await get_trial_subscription_url(tid)
        await apply_trial_connections_screen(
            query,
            bot,
            back_to=back_to,
            subscription_url=sub,
        )
    else:
        await apply_trial_connections_screen(
            query,
            bot,
            back_to=back_to,
            caption_html=texts.connections_no_access_caption(),
        )


@router.callback_query(
    lambda q: (q.data or "") == "conn_iphone" or (q.data or "").startswith("conn_iphone:")
)
async def on_conn_iphone(query: CallbackQuery, bot: Bot) -> None:
    await safe_answer(query)
    raw = query.data or ""
    back_to = raw.split(":", 1)[1] if raw.startswith("conn_iphone:") else "main"
    if query.from_user is None:
        return
    await ensure_user(query.from_user)
    tid = query.from_user.id
    sub: str | None = None
    if await trial_still_active(tid):
        sub = await get_trial_subscription_url(tid)
    await apply_iphone_guide_screen(query, bot, back_to=back_to, subscription_url=sub)


@router.callback_query(F.data.startswith("iphone_instr_hub:"))
async def on_iphone_instr_hub(query: CallbackQuery, bot: Bot) -> None:
    await safe_answer(query)
    raw = query.data or ""
    parsed = parse_iphone_instr_cb(raw, "iphone_instr_hub:")
    if parsed is None or query.from_user is None:
        return
    await ensure_user(query.from_user)
    parent, bt = parsed
    await apply_iphone_instructions_apps_screen(
        query,
        bot,
        back_to=bt,
        parent=parent,
    )


@router.callback_query(F.data.startswith("iphone_instr_happ:"))
async def on_iphone_instr_happ(query: CallbackQuery, bot: Bot) -> None:
    await safe_answer(query)
    raw = query.data or ""
    parsed = parse_iphone_instr_cb(raw, "iphone_instr_happ:")
    if parsed is None or query.from_user is None:
        return
    await ensure_user(query.from_user)
    parent, bt = parsed
    await apply_iphone_instr_happ_detail_screen(
        query,
        bot,
        parent=parent,
        back_to=bt,
    )


@router.callback_query(F.data.startswith("iphone_instr_hiddify:"))
async def on_iphone_instr_hiddify(query: CallbackQuery, bot: Bot) -> None:
    await safe_answer(query)
    raw = query.data or ""
    parsed = parse_iphone_instr_cb(raw, "iphone_instr_hiddify:")
    if parsed is None or query.from_user is None:
        return
    await ensure_user(query.from_user)
    parent, bt = parsed
    await apply_iphone_instr_hiddify_detail_screen(
        query,
        bot,
        parent=parent,
        back_to=bt,
    )


@router.callback_query(F.data.startswith("iphone_instr_v2raytun:"))
async def on_iphone_instr_v2raytun(query: CallbackQuery, bot: Bot) -> None:
    await safe_answer(query)
    raw = query.data or ""
    parsed = parse_iphone_instr_cb(raw, "iphone_instr_v2raytun:")
    if parsed is None or query.from_user is None:
        return
    await ensure_user(query.from_user)
    parent, bt = parsed
    await apply_iphone_instr_v2raytun_detail_screen(
        query,
        bot,
        parent=parent,
        back_to=bt,
    )


@router.callback_query(F.data.startswith("instructions_iphone:"))
async def on_instructions_iphone_legacy(query: CallbackQuery, bot: Bot) -> None:
    """Старые клавиатуры с callback instructions_iphone:…"""
    await safe_answer(query)
    back_to = (query.data or "").split(":", 1)[1]
    if query.from_user is None:
        return
    await ensure_user(query.from_user)
    bt = back_to or "main"
    await apply_iphone_instructions_apps_screen(
        query,
        bot,
        back_to=bt,
        parent="i",
    )


@router.callback_query(F.data == "iphone_instruction")
async def on_iphone_instruction(query: CallbackQuery) -> None:
    await safe_answer(
        query,
        "Добавьте ссылку на инструкцию в .env: IPHONE_INSTRUCTION_URL=https://…",
        show_alert=True,
    )


@router.callback_query(
    lambda q: (q.data or "") == "conn_android" or (q.data or "").startswith("conn_android:")
)
async def on_conn_android(query: CallbackQuery, bot: Bot) -> None:
    await safe_answer(query)
    raw = query.data or ""
    back_to = raw.split(":", 1)[1] if raw.startswith("conn_android:") else "main"
    if query.from_user is None:
        return
    await ensure_user(query.from_user)
    tid = query.from_user.id
    sub: str | None = None
    if await trial_still_active(tid):
        sub = await get_trial_subscription_url(tid)
    await apply_android_trial_guide_screen(
        query,
        bot,
        back_to=back_to,
        subscription_url=sub,
    )


@router.callback_query(F.data.startswith("instructions_android_hiddify:"))
async def on_instructions_android_hiddify(query: CallbackQuery, bot: Bot) -> None:
    await safe_answer(query)
    back_to = (query.data or "").split(":", 1)[1]
    if query.from_user is None:
        return
    await ensure_user(query.from_user)
    await apply_android_hiddify_detail_screen(
        query,
        bot,
        back_to=back_to or "main",
    )


@router.callback_query(F.data.startswith("instructions_android_v2raytun:"))
async def on_instructions_android_v2raytun(query: CallbackQuery, bot: Bot) -> None:
    await safe_answer(query)
    back_to = (query.data or "").split(":", 1)[1]
    if query.from_user is None:
        return
    await ensure_user(query.from_user)
    await apply_android_v2raytun_detail_screen(
        query,
        bot,
        back_to=back_to or "main",
    )


@router.callback_query(F.data.startswith("instructions_android_happ:"))
async def on_instructions_android_happ(query: CallbackQuery, bot: Bot) -> None:
    await safe_answer(query)
    back_to = (query.data or "").split(":", 1)[1]
    if query.from_user is None:
        return
    await ensure_user(query.from_user)
    await apply_android_happ_detail_screen(
        query,
        bot,
        back_to=back_to or "main",
    )


@router.callback_query(F.data.startswith("instructions_android:"))
async def on_instructions_android(query: CallbackQuery, bot: Bot) -> None:
    await safe_answer(query)
    back_to = (query.data or "").split(":", 1)[1]
    if query.from_user is None:
        return
    await ensure_user(query.from_user)
    await apply_android_instructions_apps_screen(
        query,
        bot,
        back_to=back_to or "main",
    )


@router.callback_query(F.data == "android_instruction")
async def on_android_instruction(query: CallbackQuery) -> None:
    await safe_answer(
        query,
        "Добавьте ссылку на инструкцию в .env: ANDROID_INSTRUCTION_URL=https://…",
        show_alert=True,
    )


@router.callback_query(
    lambda q: (q.data or "") == "vpn_troubleshoot"
    or (q.data or "").startswith("vpn_troubleshoot:")
)
async def on_vpn_troubleshoot(
    query: CallbackQuery,
    bot: Bot,
    threexui_runtime: ThreexuiRuntime,
) -> None:
    await safe_answer(query)
    raw = query.data or ""
    back_to = raw.split(":", 1)[1] if raw.startswith("vpn_troubleshoot:") else "main"
    if query.from_user is None:
        return
    await ensure_user(query.from_user)
    await run_vpn_troubleshoot_reissue(
        query,
        bot,
        query.from_user.id,
        back_to=back_to or "main",
        runtime=threexui_runtime,
    )


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
async def on_support(query: CallbackQuery, bot: Bot) -> None:
    await safe_answer(query)
    await apply_support_screen(query, bot)


@router.callback_query(F.data == "referral")
async def on_referral(query: CallbackQuery) -> None:
    await safe_answer(query, "Реферальная программа — в разработке.", show_alert=True)


@router.callback_query(
    lambda q: (q.data or "") == "instructions" or (q.data or "").startswith("instructions:")
)
async def on_instructions(query: CallbackQuery, bot: Bot) -> None:
    await safe_answer(query)
    raw = query.data or ""
    back_to = raw.split(":", 1)[1] if raw.startswith("instructions:") else "main"
    if query.from_user is None:
        return
    await ensure_user(query.from_user)
    tid = query.from_user.id
    sub: str | None = None
    if await trial_still_active(tid):
        sub = await get_trial_subscription_url(tid)
    await apply_instructions_screen(
        query,
        bot,
        back_to=back_to or "main",
        subscription_url=sub,
    )
