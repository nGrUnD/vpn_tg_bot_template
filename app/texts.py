import html

from app.ru_plural import days_form

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
