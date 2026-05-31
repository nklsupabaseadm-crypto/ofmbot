from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import User


class LocaleMiddleware(BaseMiddleware):
    SUPPORTED = {"ru", "en"}
    DEFAULT = "en"   # ← English is always the fallback

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        lang = self.DEFAULT
        telegram_id: int | None = None

        if isinstance(event, Update):
            user = None
            if event.message:
                user = event.message.from_user
            elif event.callback_query:
                user = event.callback_query.from_user

            if user:
                telegram_id = user.id
                # Detect from device only as initial fallback
                raw = (user.language_code or "en").lower()[:2]
                lang = raw if raw in self.SUPPORTED else self.DEFAULT

        # ── Override with saved DB preference ────────────────────────────────
        session: AsyncSession | None = data.get("session")
        if session and telegram_id:
            result = await session.execute(
                select(User.language).where(User.telegram_id == telegram_id)
            )
            saved = result.scalar_one_or_none()
            if saved and saved in self.SUPPORTED:
                lang = saved   # DB preference always wins

        data["lang"] = lang
        return await handler(event, data)