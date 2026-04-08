from aiogram import F, Router
from aiogram.types import CallbackQuery

router = Router(name="menu")


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
