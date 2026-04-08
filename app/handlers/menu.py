from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery

from app.services.main_menu import apply_full_main_menu_to_message

router = Router(name="menu")


@router.callback_query(F.data == "main_menu")
async def on_open_main_menu(query: CallbackQuery, bot: Bot) -> None:
    """Из welcome — полное главное меню (картинка + 6 кнопок)."""
    await query.answer()
    await apply_full_main_menu_to_message(query, bot)


@router.callback_query(F.data == "trial_3d")
async def on_trial_3d(query: CallbackQuery) -> None:
    await query.answer("Пробные 3 дня — скоро здесь.", show_alert=True)


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
