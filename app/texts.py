import html
from datetime import datetime, timezone

from app.ru_plural import days_form

_RU_MONTHS = (
    "",
    "января",
    "февраля",
    "марта",
    "апреля",
    "мая",
    "июня",
    "июля",
    "августа",
    "сентября",
    "октября",
    "ноября",
    "декабря",
)


def format_ru_date(dt: datetime) -> str:
    """Например: 27 марта 2026."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    local = dt.astimezone(timezone.utc)
    return f"{local.day} {_RU_MONTHS[local.month]} {local.year}"


def remaining_until_phrase(ends_at: datetime, *, now: datetime) -> str:
    """Текст «осталось N …» или «меньше суток»."""
    if ends_at.tzinfo is None:
        ends_at = ends_at.replace(tzinfo=timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    if ends_at <= now:
        return "—"
    delta = ends_at - now
    if delta.total_seconds() < 86400:
        return "меньше суток"
    d = int(delta.days)
    return f"{d} {days_form(d)}"

START_NEED_CHANNEL = (
    "Чтобы использовать RaccsterVPN, необходимо подписаться на наш канал."
)

WELCOME_CAPTION = (
    "Добро пожаловать в RaccsterVPN!👋\n\n"
    "Здесь ты можешь подключить VPN и вернуть себе полный доступ к любимым сервисам, "
    "играм и контенту.  Активируй 3 пробных дня, чтобы опробовать VPN и увидеть, "
    "насколько это быстро и стабильно.⚡️\n\n"
    "Твоя свобода в интернете — наша работа!💼"
)

MAIN_MENU_CAPTION = (
    "📌 Главное меню: Выберите нужное вам действие⬇️"
)

BUY_LEGAL_PRIVACY_URL = "https://telegra.ph/Politika-konfidencialnosti-04-13-22"
BUY_LEGAL_TERMS_URL = "https://telegra.ph/POLZOVATELSKOE-SOGLASHENIE-04-13-25"


def buy_legal_links_block() -> str:
    """Ссылки на политику и соглашение (как на экране «Купить доступ»)."""
    p = html.escape(BUY_LEGAL_PRIVACY_URL, quote=True)
    t = html.escape(BUY_LEGAL_TERMS_URL, quote=True)
    return (
        f'<a href="{p}">Политика конфиденциальности</a>\n'
        f'<a href="{t}">ПОЛЬЗОВАТЕЛЬСКОЕ СОГЛАШЕНИЕ</a>'
    )


BUY_ACCESS_CAPTION = (
    "👑<b>Полный доступ</b>\n\n"
    f"{buy_legal_links_block()}\n\n"
    "Выберите удобный вам способ оплаты⬇️:"
)

BUY_RUB_TARIFFS_CAPTION = (
    "👑 <b>Полный доступ</b>\n\n"
    "Выберите тариф⬇️:"
)

BUY_PROMO_CAPTION = (
    "👑 <b>Полный доступ</b>\n\n"
    "Введите промокод сообщением или нажмите «Пропустить»."
)


def rub_tariff_amount_rub(months: int) -> int:
    """Цена тарифа в рублях (экран тарифов)."""
    return {1: 299, 3: 779, 6: 1349, 12: 2499}.get(int(months), 299)


def buy_rub_payment_caption(amount_rub: int) -> str:
    n = int(amount_rub)
    legal = buy_legal_links_block()
    return (
        "<b>Оплата рублями</b>\n\n"
        f"Сумма к оплате: <b>{n}</b> ₽\n\n"
        "1. Нажмите кнопку «Оплатить» и завершите платеж на странице.\n"
        "2. После оплаты придёт уведомление; при необходимости нажмите «Проверить оплату».\n\n"
        f"{legal}"
    )


WATA_PAYMENT_SUCCESS_USER_MESSAGE = (
    "✅ <b>Оплата получена</b>\n\n"
    "Подписка создана. Откройте «⭐️ Мои подключения» в профиле."
)

WATA_PAYMENT_PROVISION_PENDING = (
    "Оплата получена, подписка ещё создаётся. Нажмите «Проверить оплату» через несколько секунд."
)

WATA_PAYMENT_PROVISION_FAILED = (
    "Оплата прошла, но создать VPN-подписку пока не удалось. Нажмите «Проверить оплату» ещё раз чуть позже."
)

WATA_CREATE_LINK_FAILED_ALERT = (
    "Не удалось создать ссылку на оплату. Попробуйте позже или напишите в поддержку."
)

RUB_VERIFY_NONE = "Платёж не найден. Откройте экран оплаты заново через «Купить доступ»."
RUB_VERIFY_PENDING = "Оплата ещё не подтверждена. Завершите оплату по ссылке и подождите немного."
RUB_VERIFY_PAID = "Оплата уже получена — открываю ваши подключения."
RUB_VERIFY_DECLINED = "По последнему заказу оплата не прошла. Выберите тариф снова и повторите попытку."
RUB_VERIFY_PROVISIONING = "Оплата есть, но подписка ещё создаётся. Попробуйте ещё раз через несколько секунд."
RUB_VERIFY_PROVISION_FAILED = "Оплата есть, но подписку пока не удалось создать. Попробую ещё раз."


NOT_SUBSCRIBED_ALERT = (
    "Сначала подпишитесь на канал, затем снова нажмите «Проверить»."
)

CHECK_SUBSCRIPTION_FAILED_ALERT = (
    "Не удалось проверить подписку. Убедитесь, что бот добавлен в канал как администратор."
)


def trial_connections_caption(days: int, subscription_url: str | None = None) -> str:
    d = days_form(days)
    return active_connections_caption(
        access_label="Пробный период",
        description=f"Доступ выдан на {days} {d}.",
        subscription_url=subscription_url,
    )


def active_connections_caption(
    *,
    access_label: str,
    description: str,
    subscription_url: str | None = None,
) -> str:
    base = (
        "⭐️ <b>Мои подключения</b>\n\n"
        f"Доступ: {access_label} ✅\n\n"
        f"{description}\n\n"
    )
    if subscription_url and subscription_url.strip():
        u = html.escape(subscription_url.strip(), quote=True)
        base += f'📎 <b>Подписка:</b> <a href="{u}">открыть</a>\n\n'
    base += (
        "Выберите устройство ниже, чтобы открыть страницу подключения. "
        "На странице будут кнопки для автоимпорта в приложение."
    )
    return base


def instructions_caption(subscription_url: str | None) -> str:
    """Экран «Инструкции по подключению» (ссылка как в «Мои подключения»)."""
    body = (
        "📝 <b>Инструкции по подключению</b>\n\n"
        "Подписка активирована ✅\n\n"
        "Откройте ссылку на страницу подключения ниже. На странице будут кнопки Happ и Hiddify "
        "для автоимпорта в приложение.\n\n"
    )
    if subscription_url and subscription_url.strip():
        u = html.escape(subscription_url.strip(), quote=True)
        body += f'<b>Ссылка на страницу подключения:</b> <a href="{u}">открыть</a>'
    else:
        body += (
            "<b>Ссылка на страницу подключения:</b> пока недоступна — активируйте доступ "
            "и откройте «⭐️ Мои подключения»."
        )
    return body


def connections_no_access_caption() -> str:
    return (
        "⭐️ <b>Мои подключения</b>\n\n"
        "Активного доступа к VPN сейчас нет.\n"
        "Получите пробный период или купите подписку через главное меню.\n\n"
        "Когда доступ будет активен, здесь появятся ссылки для устройств."
    )


def profile_caption(
    *,
    vpn_access_active: bool,
    access_label: str,
    until_text: str,
    remaining_text: str,
    bonus_days: int,
    bonus_balance_rub: int,
) -> str:
    """
    vpn_access_active — есть ли сейчас trial (или в будущем платный доступ).
    access_label — строка для блока «Доступ».
    """
    status_line = (
        "🟢 <b>Статус:</b> Активен" if vpn_access_active else "🔴 <b>Статус:</b> Неактивен"
    )
    level_line = "👑 <b>Уровень:</b> 🟢 Новый пользователь"
    return (
        "👤 <b>Мой профиль</b>\n\n"
        f"{status_line}\n"
        f"📦 <b>Доступ:</b> {access_label}\n"
        f"{level_line}\n"
        f"📅 <b>До:</b> {until_text}\n"
        f"⏳ <b>Осталось:</b> {remaining_text}\n\n"
        f"🎁 <b>Бонусные дни:</b> {int(bonus_days)}\n"
        f"💰 <b>Бонусный баланс:</b> {int(bonus_balance_rub)}₽\n\n"
        "Ниже откройте «⭐️ Мои подключения»."
    )


SUPPORT_HANDLE = "VPNRaccsterSupport"
SUPPORT_TELEGRAM_URL = "https://t.me/VPNRaccsterSupport"

WINDOWS_MAC_HAPP_DOWNLOAD_URL = (
    "https://github.com/Happ-proxy/happ-desktop/releases/latest/download/setup-Happ.x64.exe"
)
WINDOWS_MAC_HIDDIFY_DOWNLOAD_URL = (
    "https://github.com/hiddify/hiddify-app/releases/latest/download/Hiddify-Windows-Setup-x64.exe"
)

WINDOWS_MAC_INSTRUCTION_TELEGRAPH_URL = (
    "https://telegra.ph/Instrukciya-po-nastrojke-RaccsterVPN-na-WINDOWS-04-10"
)
WINDOWS_MAC_INSTRUCTION_HAPP_TELEGRAPH_URL = (
    "https://telegra.ph/Instrukciya-po-nastrojke-RaccsterVPN-na-WINDOWS-cherez-Happ-04-10"
)


def windows_mac_instructions_caption() -> str:
    """Экран «Инструкции» → Windows/Mac — ссылки на Telegraph."""
    u1 = html.escape(WINDOWS_MAC_INSTRUCTION_TELEGRAPH_URL, quote=True)
    u2 = html.escape(WINDOWS_MAC_INSTRUCTION_HAPP_TELEGRAPH_URL, quote=True)
    return (
        "📝 <b>Инструкции по подключению</b>\n"
        "💻 <b>Windows / Mac</b>\n\n"
        "Инструкция по настройке RaccsterVPN на Windows / Mac.\n\n"
        f'Инструкция по подключению ⬇️ <a href="{u1}">Windows / Mac</a>\n\n'
        f'Инструкция по подключению через hApp ⬇️ <a href="{u2}">Windows / Mac</a>'
    )


def windows_mac_guide_caption(subscription_url: str | None) -> str:
    """Инструкция Windows/Mac; ссылки приложений — текст «скачать»."""
    happ = html.escape(WINDOWS_MAC_HAPP_DOWNLOAD_URL, quote=True)
    hid = html.escape(WINDOWS_MAC_HIDDIFY_DOWNLOAD_URL, quote=True)
    body = (
        "🖥 <b>Подключение для Windows / Mac</b>\n\n"
        "1. Откройте ссылку для подключения в боте.\n"
        "2. Установите одно из приложений, если оно ещё не установлено:\n"
        f'— hApp — <a href="{happ}">скачать</a>\n'
        f'— Hiddify — <a href="{hid}">скачать</a>\n'
        "3. На странице подключения нажмите кнопку открытия в выбранном приложении.\n\n"
    )
    if subscription_url and subscription_url.strip():
        su = html.escape(subscription_url.strip(), quote=True)
        body += f'Ссылка на страницу подключения: <a href="{su}">открыть</a>'
    else:
        body += (
            "Ссылка на страницу подключения пока недоступна — активируйте доступ "
            "и откройте «⭐️ Мои подключения», там появится ссылка на подписку."
        )
    return body


IPHONE_HAPP_APP_STORE_URL = "https://apps.apple.com/app/id6504287215"
IPHONE_HIDDIFY_APP_STORE_URL = "https://apps.apple.com/app/id6596777532"
IPHONE_V2RAYTUN_APP_STORE_URL = "https://apps.apple.com/app/id6476628951"


def subscription_url_for_ios(subscription_url: str | None) -> str | None:
    """Добавляет platform=ios к URL подписки (как на странице подключения)."""
    if not subscription_url or not subscription_url.strip():
        return None
    u = subscription_url.strip()
    lower = u.lower()
    if "platform=ios" in lower:
        return u
    sep = "&" if "?" in u else "?"
    return f"{u}{sep}platform=ios"


def iphone_instructions_apps_caption() -> str:
    return (
        "📝 <b>Инструкции по подключению</b>\n"
        "🍏 <b>iPhone</b>\n\n"
        "Инструкция по настройке RaccsterVPN на iOS. Рекомендуем <b>Happ</b> для первого подключения. "
        "Если вы уже пользуетесь <b>Hiddify</b> или <b>V2RayTun</b>, их тоже можно оставить.\n\n"
        "Выберите приложение ниже — откроется пошаговая инструкция."
    )


def iphone_instr_happ_detail_caption() -> str:
    u = html.escape(IPHONE_HAPP_APP_STORE_URL, quote=True)
    return (
        "📝 <b>Инструкции по подключению</b>\n"
        "🍏 <b>iPhone</b> · <b>Happ</b>\n\n"
        "Приложение <b>Happ</b> рекомендуем для iPhone по умолчанию. "
        "Оно обычно проще для первого подключения.\n\n"
        f'<b>Скачать Happ ⬇️</b> <a href="{u}">Happ</a>\n\n'
        "<b>Как подключить Happ:</b>\n"
        "1. Установите Happ\n"
        "2. Откройте «⭐️ Мои подключения»\n"
        "3. Выберите iPhone\n"
        "4. Нажмите «Открыть в Happ» на странице подключения\n"
        "5. Подтвердите импорт и разрешите VPN"
    )


def iphone_instr_hiddify_detail_caption() -> str:
    u = html.escape(IPHONE_HIDDIFY_APP_STORE_URL, quote=True)
    return (
        "📝 <b>Инструкции по подключению</b>\n"
        "🍏 <b>iPhone</b> · <b>Hiddify</b>\n\n"
        "Приложение <b>Hiddify</b> оставили как второй вариант для iPhone. "
        "Если вы уже пользуетесь Hiddify, можно не переходить на Happ.\n\n"
        f'<b>Скачать Hiddify ⬇️</b> <a href="{u}">Hiddify</a>'
    )


def iphone_instr_v2raytun_detail_caption() -> str:
    u = html.escape(IPHONE_V2RAYTUN_APP_STORE_URL, quote=True)
    return (
        "📝 <b>Инструкции по подключению</b>\n"
        "🍏 <b>iPhone</b> · <b>V2RayTun</b>\n\n"
        "Приложение <b>V2RayTun</b> оставили как второй вариант для iPhone. "
        "Если вы уже пользуетесь V2RayTun, можно не переходить на Happ.\n\n"
        f'<b>Скачать V2RayTun ⬇️</b> <a href="{u}">V2RayTun</a>'
    )


def iphone_guide_caption(subscription_url: str | None) -> str:
    happ = html.escape(IPHONE_HAPP_APP_STORE_URL, quote=True)
    hid = html.escape(IPHONE_HIDDIFY_APP_STORE_URL, quote=True)
    v2 = html.escape(IPHONE_V2RAYTUN_APP_STORE_URL, quote=True)
    body = (
        "🍏 <b>Подключение для iPhone</b>\n\n"
        "Подписка активирована ✅\n\n"
        "Откройте ссылку на страницу подключения в боте.\n\n"
        "Установите одно из приложений, если оно ещё не установлено:\n"
        f'— hApp — <a href="{happ}">скачать</a>\n'
        f'— Hiddify — <a href="{hid}">скачать</a>\n'
        f'— v2RayTun — <a href="{v2}">скачать</a>\n\n'
        "На странице подключения нажмите кнопку открытия в выбранном приложении "
        "для автоимпорта.\n\n"
    )
    ios_link = subscription_url_for_ios(subscription_url)
    if ios_link:
        su = html.escape(ios_link, quote=True)
        body += f'Ссылка на страницу подключения: <a href="{su}">открыть</a>'
    else:
        body += (
            "Ссылка на страницу подключения пока недоступна — активируйте доступ "
            "и откройте «⭐️ Мои подключения»."
        )
    return body


ANDROID_HAPP_PLAY_URL = "https://play.google.com/store/apps/details?id=com.happproxy"
ANDROID_HIDDIFY_PLAY_URL = "https://play.google.com/store/apps/details?id=app.hiddify.com"
ANDROID_V2RAYTUN_PLAY_URL = "https://play.google.com/store/apps/details?id=com.v2raytun.android"


def subscription_url_for_android(subscription_url: str | None) -> str | None:
    if not subscription_url or not subscription_url.strip():
        return None
    u = subscription_url.strip()
    lower = u.lower()
    if "platform=android" in lower:
        return u
    sep = "&" if "?" in u else "?"
    return f"{u}{sep}platform=android"


def android_apps_instruction_caption() -> str:
    return (
        "📝 <b>Инструкции по подключению</b>\n"
        "📱 <b>Android</b>\n\n"
        "Для нашего VPN рекомендуем <b>Happ</b>.\n"
        "<b>Hiddify</b>, <b>V2RayTun</b> оставили ниже для тех, кто уже им пользуется."
    )


def android_trial_guide_caption(subscription_url: str | None) -> str:
    happ = html.escape(ANDROID_HAPP_PLAY_URL, quote=True)
    hid = html.escape(ANDROID_HIDDIFY_PLAY_URL, quote=True)
    v2 = html.escape(ANDROID_V2RAYTUN_PLAY_URL, quote=True)
    body = (
        "📱 <b>Подключение для Android</b>\n\n"
        "Подписка активирована ✅\n\n"
        "Откройте ссылку на страницу подключения в боте.\n\n"
        "Установите одно из приложений, если оно ещё не установлено:\n"
        f'— hApp — <a href="{happ}">скачать</a>\n'
        f'— Hiddify — <a href="{hid}">скачать</a>\n'
        f'— v2RayTun — <a href="{v2}">скачать</a>\n\n'
        "На странице подключения нажмите кнопку открытия в выбранном приложении "
        "для автоимпорта.\n\n"
    )
    and_link = subscription_url_for_android(subscription_url)
    if and_link:
        su = html.escape(and_link, quote=True)
        body += f'Ссылка на страницу подключения: <a href="{su}">открыть</a>'
    else:
        body += (
            "Ссылка на страницу подключения пока недоступна — активируйте доступ "
            "и откройте «⭐️ Мои подключения»."
        )
    return body


def android_happ_instruction_caption() -> str:
    play = html.escape(ANDROID_HAPP_PLAY_URL, quote=True)
    return (
        "📝 <b>Инструкции по подключению</b>\n"
        "📱 <b>Android</b> · <b>Happ</b>\n\n"
        "Приложение <b>Happ</b> рекомендуем для Android по умолчанию. "
        "Оно обычно проще для первого подключения.\n\n"
        f'<b>Скачать Happ ⬇️</b> <a href="{play}">Happ</a>\n\n'
        "<b>Как подключить Happ:</b>\n"
        "1. Установите Happ\n"
        "2. Откройте «⭐️ Мои подключения»\n"
        "3. Выберите Android\n"
        "4. Нажмите «Открыть в Happ» на странице подключения\n"
        "5. Подтвердите импорт и включите VPN"
    )


def android_hiddify_instruction_caption() -> str:
    hid = html.escape(ANDROID_HIDDIFY_PLAY_URL, quote=True)
    v2 = html.escape(ANDROID_V2RAYTUN_PLAY_URL, quote=True)
    return (
        "📝 <b>Инструкции по подключению</b>\n"
        "📱 <b>Android</b> · <b>Hiddify</b>\n\n"
        "Приложение <b>Hiddify</b> рекомендуем для Android. "
        "Если вам это не подходит, скачайте приложение <b>v2RayTun</b> из "
        f'<a href="{v2}">Play Маркет</a>.\n\n'
        f'<b>📲 Скачать Hiddify ⬇️</b> <a href="{hid}">Hiddify</a>\n\n'
        "<b>Как подключить Hiddify:</b>\n"
        "1. Установите Hiddify\n"
        "2. Откройте «⭐️ Мои подключения»\n"
        "3. Выберите Android\n"
        "4. Нажмите «Открыть в V2RayNG» на странице подключения\n"
        "5. Подтвердите импорт и включите VPN"
    )


def android_v2raytun_instruction_caption() -> str:
    v2 = html.escape(ANDROID_V2RAYTUN_PLAY_URL, quote=True)
    return (
        "📝 <b>Инструкции по подключению</b>\n"
        "📱 <b>Android</b> · <b>V2RayTun</b>\n\n"
        "Приложение <b>V2RayTun</b> рекомендуем для Android.\n\n"
        f'<b>Скачать V2RayTun ⬇️</b> <a href="{v2}">V2RayTun</a>\n\n'
        "<b>Как подключить V2RayTun:</b>\n"
        "1. Установите V2RayTun\n"
        "2. Откройте «⭐️ Мои подключения»\n"
        "3. Выберите Android\n"
        "4. Нажмите «Открыть в V2RayTun» на странице подключения\n"
        "5. Подтвердите импорт и включите VPN"
    )


VPN_TROUBLESHOOT_PROCESSING_CAPTION = (
    "🔎 <b>Не работает VPN?</b>\n\n"
    "Перевыпускаю подписку. Это может занять до минуты."
)


VPN_REISSUE_SUCCESS_CAPTION = (
    "🔎 <b>Не работает VPN?</b>\n\n"
    "Подписку перевыпустили ✅ Старую ссылку отключили.\n\n"
    "Теперь откройте «⭐️ Мои подключения», удалите старую подписку в приложении и подключите новую. "
    "Если после этого VPN всё равно не работает, напишите в поддержку."
)


def vpn_reissue_error_caption(detail: str) -> str:
    d = html.escape((detail or "").strip() or "неизвестная ошибка", quote=False)
    return (
        "🔎 <b>Не работает VPN?</b>\n\n"
        f"Не удалось перевыпустить подписку: {d}\n\n"
        "Попробуйте позже или напишите в поддержку."
    )


SUPPORT_CAPTION = (
    "🛠 <b>Поддержка</b>\n\n"
    "<b>Если VPN не работает:</b>\n"
    "1. Откройте «⭐️ Мои подключения»\n"
    "2. Нажмите «🔎 Не работает VPN?»\n\n"
    "Если не помогло, напишите сюда: "
    f'<a href="{SUPPORT_TELEGRAM_URL}">@{SUPPORT_HANDLE}</a>'
)
