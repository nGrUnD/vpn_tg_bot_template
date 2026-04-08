from __future__ import annotations

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware

from app.threexui_client import ThreeXUIClient


class ThreexuiMiddleware(BaseMiddleware):
    def __init__(self, client: ThreeXUIClient | None) -> None:
        self._client = client

    async def __call__(
        self,
        handler: Callable[[Any, dict[str, Any]], Awaitable[Any]],
        event: Any,
        data: dict[str, Any],
    ) -> Any:
        data["threexui"] = self._client
        return await handler(event, data)
