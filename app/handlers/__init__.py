from aiogram import Router

from app.handlers.menu import router as menu_router
from app.handlers.start import router as start_router

root_router = Router()
root_router.include_router(start_router)
root_router.include_router(menu_router)

__all__ = ("root_router",)
