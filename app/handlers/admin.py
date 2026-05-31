"""
Admin panel handlers.
Protected by IsAdmin filter.
FSM for adding new products.
"""
import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Document, Message, Video
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import repo
from app.keyboards.inline import admin_keyboard
from app.locales.i18n import t
from app.middlewares.admin_filter import IsAdmin

logger = logging.getLogger(__name__)
router = Router(name="admin")

# Apply admin filter to ALL handlers in this router
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())


# ─── FSM States ──────────────────────────────────────────────────────────────

class AddProductStates(StatesGroup):
    waiting_name = State()
    waiting_description = State()
    waiting_price = State()
    waiting_file = State()


# ─── Admin panel entry ────────────────────────────────────────────────────────

@router.message(Command("admin"))
async def cmd_admin(message: Message, session: AsyncSession, lang: str) -> None:
    users = await repo.get_user_count(session)
    sales = await repo.get_paid_count(session)
    await message.answer(
        text=t("admin_panel", lang, users=users, sales=sales),
        parse_mode="HTML",
        reply_markup=admin_keyboard(lang),
    )


@router.callback_query(F.data == "admin:add_product")
async def cb_add_product(call: CallbackQuery, state: FSMContext, lang: str) -> None:
    await state.set_state(AddProductStates.waiting_name)
    await call.message.answer(t("admin_add_product_name", lang), parse_mode="HTML")  # type: ignore[union-attr]
    await call.answer()


# ─── FSM: Add product steps ───────────────────────────────────────────────────

@router.message(AddProductStates.waiting_name, F.text)
async def fsm_product_name(message: Message, state: FSMContext, lang: str) -> None:
    await state.update_data(name=message.text)
    await state.set_state(AddProductStates.waiting_description)
    await message.answer(t("admin_add_product_desc", lang), parse_mode="HTML")


@router.message(AddProductStates.waiting_description, F.text)
async def fsm_product_desc(message: Message, state: FSMContext, lang: str) -> None:
    await state.update_data(description=message.text)
    await state.set_state(AddProductStates.waiting_price)
    await message.answer(t("admin_add_product_price", lang), parse_mode="HTML")


@router.message(AddProductStates.waiting_price, F.text)
async def fsm_product_price(message: Message, state: FSMContext, lang: str) -> None:
    try:
        price = float(message.text.replace(",", "."))  # type: ignore[arg-type]
        if price <= 0:
            raise ValueError
    except (ValueError, TypeError):
        await message.answer(t("error_invalid_price", lang), parse_mode="HTML")
        return

    await state.update_data(price=price)
    await state.set_state(AddProductStates.waiting_file)
    await message.answer(t("admin_add_product_file", lang), parse_mode="HTML")


@router.message(AddProductStates.waiting_file, F.document | F.video)
async def fsm_product_file(
    message: Message, state: FSMContext, session: AsyncSession, lang: str
) -> None:
    # Extract file_id regardless of whether it's a Document or Video
    attachment: Document | Video | None = message.document or message.video
    if not attachment:
        await message.answer(t("error_file_required", lang), parse_mode="HTML")
        return

    file_id = attachment.file_id
    data = await state.get_data()
    await state.clear()

    product = await repo.create_product(
        session=session,
        name=data["name"],
        description=data["description"],
        price_usdt=data["price"],
        file_id=file_id,
    )
    await message.answer(
        t("admin_product_saved", lang, name=product.name),
        parse_mode="HTML",
    )


@router.message(AddProductStates.waiting_file)
async def fsm_product_file_wrong(message: Message, lang: str) -> None:
    """Catch non-file messages during file upload step."""
    await message.answer(t("error_file_required", lang), parse_mode="HTML")
