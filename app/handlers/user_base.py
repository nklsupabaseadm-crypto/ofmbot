from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update

from app.core.config import settings
from app.database.models import User
from app.database.repo import get_or_create_user, get_user_by_telegram_id
from app.keyboards.inline import start_keyboard
from app.locales.i18n import t
import logging

logger = logging.getLogger(__name__)
router = Router(name="user_base")


@router.message(CommandStart())
async def cmd_start(message: Message, session: AsyncSession, lang: str) -> None:
    user = message.from_user
    if not user:
        return

    await get_or_create_user(
        session=session,
        telegram_id=user.id,
        username=user.username,
        full_name=user.full_name,
        language=lang,
    )

    if settings.lead_magnet_file_id:
        try:
            await message.answer_document(
                document=settings.lead_magnet_file_id,
                caption=t("welcome", lang, name=user.first_name),
                parse_mode="HTML",
                reply_markup=start_keyboard(lang),
            )
            return
        except Exception:
            logger.warning("Could not send lead magnet, falling back to text.")

    await message.answer(
        text=t("welcome", lang, name=user.first_name),
        parse_mode="HTML",
        reply_markup=start_keyboard(lang),
    )


# ── THIS WAS MISSING ──────────────────────────────────────────────────────────
@router.callback_query(F.data.startswith("set_lang:"))
async def change_language(call: CallbackQuery, session: AsyncSession) -> None:
    new_lang = call.data.split(":")[1]
    if new_lang not in ("en", "ru"):
        await call.answer()
        return

    # Persist language choice to DB
    await session.execute(
        update(User)
        .where(User.telegram_id == call.from_user.id)
        .values(language=new_lang)
    )
    await session.commit()

    await call.message.edit_text(
        text=t("welcome", new_lang, name=call.from_user.first_name),
        parse_mode="HTML",
        reply_markup=start_keyboard(new_lang),
    )
    await call.answer("✅")