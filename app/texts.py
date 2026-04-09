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

NOT_SUBSCRIBED_ALERT = (
    "Сначала подпишитесь на канал, затем снова нажмите «Проверить»."
)

CHECK_SUBSCRIPTION_FAILED_ALERT = (
    "Не удалось проверить подписку. Убедитесь, что бот добавлен в канал как администратор."
)


def trial_connections_caption(days: int, subscription_url: str | None = None) -> str:
    d = days_form(days)
    base = (
        "⭐️ <b>Мои подключения</b>\n\n"
        "Доступ: Пробный период ✅\n\n"
        f"Доступ выдан на {days} {d}.\n\n"
    )
    if subscription_url and subscription_url.strip():
        u = html.escape(subscription_url.strip(), quote=True)
        base += f'📎 <b>Подписка:</b> <a href="{u}">открыть</a>\n\n'
    base += (
        "Выберите устройство ниже, чтобы открыть страницу подключения. "
        "На странице будут кнопки для автоимпорта в приложение."
    )
    return base


def connections_no_access_caption() -> str:
    return (
        "⭐️ <b>Мои подключения</b>\n\n"
        "Активного доступа к VPN сейчас нет.\n"
        "Получите пробный период через главное меню.\n\n"
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

SUPPORT_CAPTION = (
    "🛠 <b>Поддержка</b>\n\n"
    "<b>Если VPN не работает:</b>\n"
    "1. Откройте «⭐️ Мои подключения»\n"
    "2. Нажмите «🔎 Не работает VPN?»\n\n"
    "Если не помогло, напишите сюда: "
    f'<a href="{SUPPORT_TELEGRAM_URL}">@{SUPPORT_HANDLE}</a>'
)
