"""
Retention handler: admin broadcast via FSM.
Admin sends a message (text + optional photo) → preview → confirm → send.
"""
import logging

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message, PhotoSize
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import repo
from app.keyboards.inline import confirm_broadcast_keyboard
from app.locales.i18n import t
from app.middlewares.admin_filter import IsAdmin
from app.services.broadcast import broadcast_message

logger = logging.getLogger(__name__)
router = Router(name="retention")

router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())


class BroadcastStates(StatesGroup):
    waiting_content = State()
    confirming = State()


# ─── Entry point from admin keyboard ─────────────────────────────────────────

@router.callback_query(F.data == "admin:broadcast")
async def cb_start_broadcast(call: CallbackQuery, state: FSMContext, lang: str) -> None:
    await state.set_state(BroadcastStates.waiting_content)
    await call.message.answer(t("admin_broadcast_prompt", lang), parse_mode="HTML")  # type: ignore[union-attr]
    await call.answer()


# ─── Receive broadcast content (text only or photo + caption) ────────────────

@router.message(BroadcastStates.waiting_content)
async def receive_broadcast_content(
    message: Message, state: FSMContext, session: AsyncSession, lang: str
) -> None:
    text = message.caption or message.text or ""
    photo_file_id: str | None = None

    if message.photo:
        # Take the largest photo variant
        best: PhotoSize = max(message.photo, key=lambda p: p.file_size or 0)
        photo_file_id = best.file_id

    if not text:
        await message.answer("⚠️ Message text is required.", parse_mode="HTML")
        return

    user_count = await repo.get_user_count(session)
    await state.update_data(text=text, photo_file_id=photo_file_id)
    await state.set_state(BroadcastStates.confirming)

    preview = t("admin_broadcast_preview", lang, text=text, count=user_count)

    if photo_file_id:
        await message.answer_photo(
            photo=photo_file_id,
            caption=preview,
            parse_mode="HTML",
            reply_markup=confirm_broadcast_keyboard(lang),
        )
    else:
        await message.answer(
            text=preview,
            parse_mode="HTML",
            reply_markup=confirm_broadcast_keyboard(lang),
        )


# ─── Confirmation ─────────────────────────────────────────────────────────────

@router.callback_query(F.data == "admin:broadcast_confirm", BroadcastStates.confirming)
async def confirm_broadcast(
    call: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
    bot: Bot,
    lang: str,
) -> None:
    data = await state.get_data()
    await state.clear()

    await call.message.edit_reply_markup(reply_markup=None)  # type: ignore[union-attr]
    await call.message.answer("⏳ Sending broadcast...")  # type: ignore[union-attr]

    user_ids = await repo.get_all_user_telegram_ids(session)
    result = await broadcast_message(
        bot=bot,
        user_ids=user_ids,
        text=data["text"],
        photo_file_id=data.get("photo_file_id"),
    )

    await call.message.answer(  # type: ignore[union-attr]
        t("admin_broadcast_done", lang, sent=result.sent, failed=result.failed),
        parse_mode="HTML",
    )
    await call.answer()


@router.callback_query(F.data == "admin:broadcast_cancel")
async def cancel_broadcast(call: CallbackQuery, state: FSMContext, lang: str) -> None:
    await state.clear()
    await call.message.edit_reply_markup(reply_markup=None)  # type: ignore[union-attr]
    await call.answer("Broadcast cancelled.")
