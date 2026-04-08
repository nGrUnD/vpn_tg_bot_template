from __future__ import annotations

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware

from app.services.threexui_backends import ThreexuiRuntime


class ThreexuiMiddleware(BaseMiddleware):
    def __init__(self, runtime: ThreexuiRuntime) -> None:
        self._runtime = runtime

    async def __call__(
        self,
        handler: Callable[[Any, dict[str, Any]], Awaitable[Any]],
        event: Any,
        data: dict[str, Any],
    ) -> Any:
        data["threexui_runtime"] = self._runtime
        return await handler(event, data)
