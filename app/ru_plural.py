def days_form(n: int) -> str:
    """Склонение: 1 день, 2 дня, 5 дней."""
    n = abs(int(n))
    if n % 100 in (11, 12, 13, 14):
        return "дней"
    if n % 10 == 1:
        return "день"
    if n % 10 in (2, 3, 4):
        return "дня"
    return "дней"


def trial_button_caption(days: int) -> str:
    """Текст кнопки «Получить N …»."""
    return f"🩵 Получить {days} {days_form(days)}"
