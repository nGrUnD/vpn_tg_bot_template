from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery

from app.keyboards.inline import main_menu_keyboard

router = Router(name="menu")


@router.callback_query(F.data == "main_menu")
async def on_main_menu_legacy(query: CallbackQuery) -> None:
    """Старые сообщения с кнопкой «Главное меню» (callback main_menu)."""
    await query.answer()
    if query.message is None:
        return
    try:
        await query.message.edit_reply_markup(reply_markup=main_menu_keyboard())
    except TelegramBadRequest:
        pass


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
