"""
Handlers: catalog, product detail, buy, check_payment
Full purchase funnel lives here.
"""
import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import repo
from app.keyboards.inline import catalog_keyboard, payment_keyboard, product_keyboard
from app.locales.i18n import t
from app.services import crypto_pay

logger = logging.getLogger(__name__)
router = Router(name="catalog")


# ─── Catalog list ─────────────────────────────────────────────────────────────

@router.callback_query(F.data == "catalog")
async def show_catalog(call: CallbackQuery, session: AsyncSession, lang: str) -> None:
    products = await repo.get_active_products(session)
    if not products:
        await call.answer("No products available yet.", show_alert=True)
        return

    await call.message.edit_text(  # type: ignore[union-attr]
        text=t("catalog_title", lang),
        parse_mode="HTML",
        reply_markup=catalog_keyboard(products, lang),
    )
    await call.answer()


# ─── Product card ─────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("product:"))
async def show_product(call: CallbackQuery, session: AsyncSession, lang: str) -> None:
    product_id = int(call.data.split(":")[1])  # type: ignore[union-attr]
    product = await repo.get_product_by_id(session, product_id)

    if not product or not product.is_active:
        await call.answer("Product not found.", show_alert=True)
        return

    await call.message.edit_text(  # type: ignore[union-attr]
        text=t("product_card", lang, name=product.name,
               description=product.description, price=product.price_usdt),
        parse_mode="HTML",
        reply_markup=product_keyboard(product, lang),
    )
    await call.answer()


# ─── Buy button ───────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("buy:"))
async def buy_product(call: CallbackQuery, session: AsyncSession, lang: str) -> None:
    product_id = int(call.data.split(":")[1])  # type: ignore[union-attr]
    product = await repo.get_product_by_id(session, product_id)

    if not product or not product.is_active:
        await call.answer("Product not found.", show_alert=True)
        return

    user = call.from_user
    db_user = await repo.get_user_by_telegram_id(session, user.id)
    if not db_user:
        await call.answer("Please use /start first.", show_alert=True)
        return

    # Check if already purchased
    if await repo.user_already_bought(session, db_user.id, product_id):
        await call.answer(t("already_bought", lang), show_alert=True)
        return

    # Create CryptoBot invoice
    try:
        invoice_id, pay_url = await crypto_pay.create_invoice(
            amount=float(product.price_usdt),
            product_name=product.name,
        )
    except Exception as exc:
        logger.error("CryptoBot error: %s", exc)
        await call.answer("Payment system error. Try again later.", show_alert=True)
        return

    # Persist pending purchase
    await repo.create_purchase(session, db_user.id, product_id, invoice_id)

    await call.message.edit_text(  # type: ignore[union-attr]
        text=t("invoice_created", lang),
        parse_mode="HTML",
        reply_markup=payment_keyboard(pay_url, invoice_id, lang),
    )
    await call.answer()


# ─── Check payment ────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("check_payment:"))
async def check_payment(call: CallbackQuery, session: AsyncSession, lang: str) -> None:
    invoice_id = int(call.data.split(":")[1])  # type: ignore[union-attr]
    purchase = await repo.get_purchase_by_invoice(session, invoice_id)

    if not purchase:
        await call.answer("Purchase not found.", show_alert=True)
        return

    # Already confirmed before
    if purchase.status == "paid":
        await _deliver_product(call, session, purchase.product_id, lang)
        return

    # Ask CryptoBot
    try:
        status = await crypto_pay.check_invoice_status(invoice_id)
    except Exception as exc:
        logger.error("CryptoBot check error: %s", exc)
        await call.answer("Could not check status. Try again.", show_alert=True)
        return

    if status == "paid":
        await repo.mark_purchase_paid(session, invoice_id)
        await _deliver_product(call, session, purchase.product_id, lang)
    elif status == "expired":
        await call.message.edit_text(t("payment_expired", lang), parse_mode="HTML")  # type: ignore[union-attr]
        await call.answer()
    else:
        await call.answer(t("payment_pending", lang), show_alert=True)


async def _deliver_product(
    call: CallbackQuery, session: AsyncSession, product_id: int | None, lang: str
) -> None:
    """Send the purchased file to the user."""
    if not product_id:
        return
    product = await repo.get_product_by_id(session, product_id)
    if not product or not product.file_id:
        await call.answer("File not available. Contact support.", show_alert=True)
        return

    await call.message.answer_document(  # type: ignore[union-attr]
        document=product.file_id,
        caption=t("payment_success", lang),
        parse_mode="HTML",
    )
    await call.answer("✅ Payment confirmed!")
