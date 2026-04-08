from aiogram import F, Router
from aiogram.types import CallbackQuery

router = Router(name="menu")


@router.callback_query(F.data == "trial_3d")
async def on_trial_3d(query: CallbackQuery) -> None:
    await query.answer("Пробные 3 дня — скоро здесь.", show_alert=True)


@router.callback_query(F.data == "buy_access")
async def on_buy_access(query: CallbackQuery) -> None:
    await query.answer("Покупка доступа — в разработке.", show_alert=True)


@router.callback_query(F.data == "main_menu")
async def on_main_menu(query: CallbackQuery) -> None:
    await query.answer("Это главное меню. Выберите действие ниже.")
