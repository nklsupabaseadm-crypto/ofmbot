from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery

from app.core.config import settings


class IsAdmin(BaseFilter):
    """Passes only if the sender's Telegram ID is in ADMIN_IDS."""

    async def __call__(self, event: Message | CallbackQuery) -> bool:  # type: ignore[override]
        user = event.from_user
        if user is None:
            return False
        return user.id in settings.admin_ids
