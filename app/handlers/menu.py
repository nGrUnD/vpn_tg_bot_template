from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery, LabeledPrice, Message, PreCheckoutQuery

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
from app.services.buy_access_screen import (
    apply_buy_access_screen,
    apply_buy_promo_screen,
    apply_buy_rub_tariffs_screen,
    apply_buy_stars_promo_screen,
    apply_buy_stars_tariffs_screen,
)
from app.services.paid_access import ensure_paid_access_for_order
from app.services.rub_payment_flow import open_buy_rub_payment_after_promo
from app.services.stars_payment_flow import (
    open_buy_stars_payment_screen,
    parse_stars_invoice_payload,
    stars_invoice_payload,
)
from app.services import rub_orders
from app.services.users import (
    ensure_user,
    get_active_access,
    get_active_subscription_url,
)
from app.services.welcome import show_welcome_on_message

router = Router(name="menu")


async def _show_active_connections(
    query: CallbackQuery,
    bot: Bot,
    *,
    telegram_id: int,
    back_to: str,
) -> None:
    access = await get_active_access(telegram_id)
    if access is None:
        await apply_trial_connections_screen(
            query,
            bot,
            back_to=back_to,
            caption_html=texts.connections_no_access_caption(),
        )
        return
    description = f"Доступ активен до {texts.format_ru_date(access.expires_at)}."
    await apply_trial_connections_screen(
        query,
        bot,
        back_to=back_to,
        caption_html=texts.active_connections_caption(
            access_label=access.access_label,
            description=description,
            subscription_url=access.subscription_url,
        ),
    )


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
    sub = await get_active_subscription_url(query.from_user.id)
    await apply_windows_mac_guide_screen(query, bot, back_to=back_to, subscription_url=sub)


@router.callback_query(F.data.startswith("instructions_windows:"))
async def on_instructions_windows(query: CallbackQuery, bot: Bot) -> None:
    await safe_answer(query)
    back_to = (query.data or "").split(":", 1)[1]
    if query.from_user is None:
        return
    await ensure_user(query.from_user)
    await apply_windows_mac_guide_screen(
        query,
        bot,
        back_to=back_to or "main",
        subscription_url=None,
        from_instructions=True,
    )


@router.callback_query(F.data.startswith("trial_devices:"))
async def on_trial_devices(query: CallbackQuery, bot: Bot) -> None:
    await safe_answer(query)
    back_to = (query.data or "").split(":", 1)[1]
    if query.from_user is None:
        return
    await ensure_user(query.from_user)
    await _show_active_connections(
        query,
        bot,
        telegram_id=query.from_user.id,
        back_to=back_to,
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
    sub = await get_active_subscription_url(query.from_user.id)
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
    sub = await get_active_subscription_url(query.from_user.id)
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


@router.callback_query(
    lambda q: (q.data or "") == "buy_access" or (q.data or "").startswith("buy_access:")
)
async def on_buy_access(query: CallbackQuery, bot: Bot) -> None:
    await safe_answer(query)
    raw = query.data or ""
    back_to = raw.split(":", 1)[1] if raw.startswith("buy_access:") else "main"
    await apply_buy_access_screen(query, bot, back_to=back_to or "main")


@router.callback_query(F.data.startswith("buy_access_back:"))
async def on_buy_access_back(query: CallbackQuery, bot: Bot) -> None:
    await safe_answer(query)
    dest = (query.data or "").split(":", 1)[1]
    if dest == "welcome":
        await show_welcome_on_message(query, bot)
    elif dest == "profile":
        if query.from_user is not None:
            await ensure_user(query.from_user)
        await apply_profile_screen(query, bot)
    else:
        await apply_full_main_menu_to_message(query, bot)


@router.callback_query(
    lambda q: (q.data or "") == "buy_pay_rub" or (q.data or "").startswith("buy_pay_rub:")
)
async def on_buy_pay_rub(query: CallbackQuery, bot: Bot) -> None:
    await safe_answer(query)
    raw = query.data or ""
    back_to = raw.split(":", 1)[1] if raw.startswith("buy_pay_rub:") else "main"
    await apply_buy_rub_tariffs_screen(query, bot, back_to=back_to or "main")


@router.callback_query(
    lambda q: (q.data or "") == "buy_pay_stars" or (q.data or "").startswith("buy_pay_stars:")
)
async def on_buy_pay_stars(query: CallbackQuery, bot: Bot) -> None:
    await safe_answer(query)
    raw = query.data or ""
    back_to = raw.split(":", 1)[1] if raw.startswith("buy_pay_stars:") else "main"
    await apply_buy_stars_tariffs_screen(query, bot, back_to=back_to or "main")


@router.callback_query(
    lambda q: (q.data or "") == "buy_pay_crypto" or (q.data or "").startswith("buy_pay_crypto:")
)
async def on_buy_pay_crypto(query: CallbackQuery) -> None:
    await safe_answer(query, "Оплата криптовалютой — в разработке.", show_alert=True)


@router.callback_query(
    lambda q: (q.data or "") == "buy_pay_bonus" or (q.data or "").startswith("buy_pay_bonus:")
)
async def on_buy_pay_bonus(query: CallbackQuery) -> None:
    await safe_answer(query, "Оплата с бонусного баланса — в разработке.", show_alert=True)


@router.callback_query(F.data.startswith("buy_tariff:"))
async def on_buy_tariff(query: CallbackQuery, bot: Bot) -> None:
    await safe_answer(query)
    raw = (query.data or "").strip()
    parts = raw.split(":")
    if len(parts) < 3 or parts[0] != "buy_tariff":
        return
    try:
        months = int(parts[1])
    except ValueError:
        return
    back_to = parts[2] or "main"
    await apply_buy_promo_screen(query, bot, months=months, back_to=back_to)


@router.callback_query(F.data.startswith("buy_stars_tariff:"))
async def on_buy_stars_tariff(query: CallbackQuery, bot: Bot) -> None:
    raw = (query.data or "").strip()
    parts = raw.split(":")
    if len(parts) < 3 or parts[0] != "buy_stars_tariff":
        await safe_answer(query)
        return
    try:
        months = int(parts[1])
    except ValueError:
        await safe_answer(query)
        return
    back_to = parts[2] or "main"
    await apply_buy_stars_promo_screen(query, bot, months=months, back_to=back_to)
    await safe_answer(query)


@router.callback_query(F.data.startswith("buy_promo_back:"))
async def on_buy_promo_back(query: CallbackQuery, bot: Bot) -> None:
    await safe_answer(query)
    back_to = (query.data or "").split(":", 1)[1] or "main"
    await apply_buy_rub_tariffs_screen(query, bot, back_to=back_to)


@router.callback_query(F.data.startswith("buy_stars_promo_back:"))
async def on_buy_stars_promo_back(query: CallbackQuery, bot: Bot) -> None:
    await safe_answer(query)
    back_to = (query.data or "").split(":", 1)[1] or "main"
    await apply_buy_stars_tariffs_screen(query, bot, back_to=back_to)


@router.callback_query(F.data.startswith("buy_promo_skip:"))
async def on_buy_promo_skip(query: CallbackQuery, bot: Bot) -> None:
    raw = (query.data or "").strip()
    parts = raw.split(":")
    if len(parts) < 3 or parts[0] != "buy_promo_skip":
        await safe_answer(query)
        return
    try:
        months = int(parts[1])
    except ValueError:
        await safe_answer(query)
        return
    back_to = parts[2] or "main"
    alert = await open_buy_rub_payment_after_promo(
        query, bot, months=months, back_to=back_to
    )
    if alert:
        await safe_answer(query, alert, show_alert=True)
    else:
        await safe_answer(query)


@router.callback_query(F.data.startswith("buy_stars_promo_skip:"))
async def on_buy_stars_promo_skip(query: CallbackQuery, bot: Bot) -> None:
    raw = (query.data or "").strip()
    parts = raw.split(":")
    if len(parts) < 3 or parts[0] != "buy_stars_promo_skip":
        await safe_answer(query)
        return
    try:
        months = int(parts[1])
    except ValueError:
        await safe_answer(query)
        return
    back_to = parts[2] or "main"
    await open_buy_stars_payment_screen(query, bot, months=months, back_to=back_to)
    await safe_answer(query)


@router.callback_query(F.data.startswith("buy_promo_open:"))
async def on_buy_promo_open(query: CallbackQuery, bot: Bot) -> None:
    """С экрана оплаты — назад к промокоду."""
    await safe_answer(query)
    raw = (query.data or "").strip()
    parts = raw.split(":")
    if len(parts) < 3 or parts[0] != "buy_promo_open":
        return
    try:
        months = int(parts[1])
    except ValueError:
        return
    back_to = parts[2] or "main"
    await apply_buy_promo_screen(query, bot, months=months, back_to=back_to)


@router.callback_query(F.data.startswith("buy_stars_promo_open:"))
async def on_buy_stars_promo_open(query: CallbackQuery, bot: Bot) -> None:
    await safe_answer(query)
    raw = (query.data or "").strip()
    parts = raw.split(":")
    if len(parts) < 3 or parts[0] != "buy_stars_promo_open":
        return
    try:
        months = int(parts[1])
    except ValueError:
        return
    back_to = parts[2] or "main"
    await apply_buy_stars_promo_screen(query, bot, months=months, back_to=back_to)


@router.callback_query(F.data.startswith("buy_rub_verify:"))
async def on_buy_rub_verify(
    query: CallbackQuery,
    bot: Bot,
    threexui_runtime: ThreexuiRuntime,
) -> None:
    if query.from_user is None:
        await safe_answer(query)
        return
    raw = (query.data or "").strip()
    parts = raw.split(":")
    if len(parts) < 3 or parts[0] != "buy_rub_verify":
        await safe_answer(query)
        return
    try:
        months = int(parts[1])
    except ValueError:
        await safe_answer(query)
        return
    row = await rub_orders.get_latest_order_for_user_tariff(
        telegram_id=query.from_user.id,
        months=months,
    )
    if row is None:
        await safe_answer(query, texts.RUB_VERIFY_NONE, show_alert=True)
        return
    st = str(row["status"])
    if st == "paid":
        prov = str(row["provisioning_status"] or "").strip()
        if row["provisioned_at"] is not None:
            await safe_answer(query, texts.RUB_VERIFY_PAID, show_alert=False)
            await _show_active_connections(
                query,
                bot=bot,
                telegram_id=query.from_user.id,
                back_to="profile",
            )
            return
        if prov == "provisioning":
            await safe_answer(query, texts.RUB_VERIFY_PROVISIONING, show_alert=True)
            return
        result = await ensure_paid_access_for_order(
            row["order_id"],
            runtime=threexui_runtime,
        )
        if result.status == "provisioned":
            await safe_answer(query, texts.RUB_VERIFY_PAID, show_alert=False)
            await _show_active_connections(
                query,
                bot=bot,
                telegram_id=query.from_user.id,
                back_to="profile",
            )
            return
        if result.status == "in_progress":
            await safe_answer(query, texts.RUB_VERIFY_PROVISIONING, show_alert=True)
            return
        await safe_answer(
            query,
            result.error_text or texts.WATA_PAYMENT_PROVISION_FAILED,
            show_alert=True,
        )
    elif st == "declined":
        await safe_answer(query, texts.RUB_VERIFY_DECLINED, show_alert=True)
    else:
        await safe_answer(query, texts.RUB_VERIFY_PENDING, show_alert=True)


@router.callback_query(F.data.startswith("buy_stars_pay:"))
async def on_buy_stars_pay(query: CallbackQuery, bot: Bot) -> None:
    if query.from_user is None:
        await safe_answer(query)
        return
    raw = (query.data or "").strip()
    parts = raw.split(":")
    if len(parts) < 4 or parts[0] != "buy_stars_pay":
        await safe_answer(query)
        return
    order_id = parts[1].strip()
    try:
        months = int(parts[2])
    except ValueError:
        await safe_answer(query)
        return

    amount = texts.stars_tariff_amount(months)
    await bot.send_invoice(
        chat_id=query.from_user.id,
        title="Raccster VPN",
        description=f"Подписка VPN на {months} мес.",
        payload=stars_invoice_payload(order_id),
        currency="XTR",
        prices=[LabeledPrice(label=f"VPN {months} мес.", amount=amount)],
    )
    await safe_answer(query, "Инвойс отправлен в чат.", show_alert=False)


@router.callback_query(F.data.startswith("buy_stars_verify:"))
async def on_buy_stars_verify(
    query: CallbackQuery,
    bot: Bot,
    threexui_runtime: ThreexuiRuntime,
) -> None:
    if query.from_user is None:
        await safe_answer(query)
        return
    raw = (query.data or "").strip()
    parts = raw.split(":")
    if len(parts) < 3 or parts[0] != "buy_stars_verify":
        await safe_answer(query)
        return
    try:
        months = int(parts[1])
    except ValueError:
        await safe_answer(query)
        return
    row = await rub_orders.get_latest_order_for_user_tariff(
        telegram_id=query.from_user.id,
        months=months,
        payment_method="stars",
    )
    if row is None:
        await safe_answer(query, texts.STARS_VERIFY_NONE, show_alert=True)
        return
    st = str(row["status"])
    if st == "paid":
        prov = str(row["provisioning_status"] or "").strip()
        if row["provisioned_at"] is not None:
            await safe_answer(query, texts.STARS_VERIFY_PAID, show_alert=False)
            await _show_active_connections(
                query,
                bot=bot,
                telegram_id=query.from_user.id,
                back_to="profile",
            )
            return
        if prov == "provisioning":
            await safe_answer(query, texts.STARS_VERIFY_PROVISIONING, show_alert=True)
            return
        result = await ensure_paid_access_for_order(
            row["order_id"],
            runtime=threexui_runtime,
        )
        if result.status == "provisioned":
            await safe_answer(query, texts.STARS_VERIFY_PAID, show_alert=False)
            await _show_active_connections(
                query,
                bot=bot,
                telegram_id=query.from_user.id,
                back_to="profile",
            )
            return
        if result.status == "in_progress":
            await safe_answer(query, texts.STARS_VERIFY_PROVISIONING, show_alert=True)
            return
        await safe_answer(
            query,
            result.error_text or texts.STARS_VERIFY_PROVISION_FAILED,
            show_alert=True,
        )
    else:
        await safe_answer(query, texts.STARS_VERIFY_PENDING, show_alert=True)


@router.pre_checkout_query()
async def on_pre_checkout_query(pre_checkout_query: PreCheckoutQuery) -> None:
    payload = parse_stars_invoice_payload(pre_checkout_query.invoice_payload)
    if payload is None:
        await pre_checkout_query.answer(ok=False, error_message="Неверный payload оплаты.")
        return
    row = await rub_orders.get_order(payload)
    if (
        row is None
        or str(row["status"] or "").strip() != "pending"
        or str(row["payment_method"] or "").strip() != "stars"
    ):
        await pre_checkout_query.answer(
            ok=False,
            error_message="Счёт больше недействителен. Откройте оплату заново.",
        )
        return
    await pre_checkout_query.answer(ok=True)


@router.message(F.successful_payment)
async def on_successful_payment(
    message: Message,
    bot: Bot,
    threexui_runtime: ThreexuiRuntime,
) -> None:
    if message.from_user is None or message.successful_payment is None:
        return
    order_id = parse_stars_invoice_payload(message.successful_payment.invoice_payload)
    if order_id is None:
        return
    await rub_orders.mark_paid_from_stars(
        order_id=order_id,
        telegram_payment_charge_id=message.successful_payment.telegram_payment_charge_id,
        provider_payment_charge_id=message.successful_payment.provider_payment_charge_id,
    )
    result = await ensure_paid_access_for_order(order_id, runtime=threexui_runtime)
    if result.status == "provisioned":
        await message.answer(texts.WATA_PAYMENT_SUCCESS_USER_MESSAGE)
        return
    if result.status == "in_progress":
        await message.answer(texts.WATA_PAYMENT_PROVISION_PENDING)
        return
    await message.answer(result.error_text or texts.STARS_VERIFY_PROVISION_FAILED)


@router.callback_query(F.data.startswith("buy_rub_pay_stub:"))
async def on_buy_rub_pay_stub(query: CallbackQuery) -> None:
    await safe_answer(query, "В разработке.", show_alert=True)


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
    await _show_active_connections(
        query,
        bot,
        telegram_id=query.from_user.id,
        back_to="profile",
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
    sub = await get_active_subscription_url(query.from_user.id)
    await apply_instructions_screen(
        query,
        bot,
        back_to=back_to or "main",
        subscription_url=sub,
    )
