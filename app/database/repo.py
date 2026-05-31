"""
Repository layer — all database queries live here.
Handlers call these functions; they never import SQLAlchemy directly.
"""
from typing import Optional

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Product, Purchase, User


# ─── Users ────────────────────────────────────────────────────────────────────

async def get_or_create_user(
    session: AsyncSession,
    telegram_id: int,
    username: Optional[str],
    full_name: str,
    language: str,
) -> tuple[User, bool]:
    """Return (user, created). Creates row if not exists."""
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()
    if user:
        return user, False
    user = User(
        telegram_id=telegram_id,
        username=username,
        full_name=full_name,
        language=language,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user, True


async def get_user_by_telegram_id(session: AsyncSession, telegram_id: int) -> Optional[User]:
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    return result.scalar_one_or_none()


async def get_all_user_telegram_ids(session: AsyncSession) -> list[int]:
    result = await session.execute(select(User.telegram_id))
    return list(result.scalars().all())


async def get_user_count(session: AsyncSession) -> int:
    result = await session.execute(select(func.count()).select_from(User))
    return result.scalar_one()


# ─── Products ─────────────────────────────────────────────────────────────────

async def get_active_products(session: AsyncSession) -> list[Product]:
    result = await session.execute(
        select(Product).where(Product.is_active == True).order_by(Product.id)  # noqa: E712
    )
    return list(result.scalars().all())


async def get_product_by_id(session: AsyncSession, product_id: int) -> Optional[Product]:
    result = await session.execute(select(Product).where(Product.id == product_id))
    return result.scalar_one_or_none()


async def create_product(
    session: AsyncSession,
    name: str,
    description: str,
    price_usdt: float,
    file_id: str,
) -> Product:
    product = Product(name=name, description=description, price_usdt=price_usdt, file_id=file_id)
    session.add(product)
    await session.commit()
    await session.refresh(product)
    return product


async def toggle_product_active(session: AsyncSession, product_id: int) -> bool:
    """Toggle is_active. Returns the new state."""
    product = await get_product_by_id(session, product_id)
    if not product:
        return False
    new_state = not product.is_active
    await session.execute(
        update(Product).where(Product.id == product_id).values(is_active=new_state)
    )
    await session.commit()
    return new_state


# ─── Purchases ────────────────────────────────────────────────────────────────

async def create_purchase(
    session: AsyncSession,
    user_id: int,
    product_id: int,
    invoice_id: int,
) -> Purchase:
    purchase = Purchase(user_id=user_id, product_id=product_id, invoice_id=invoice_id)
    session.add(purchase)
    await session.commit()
    await session.refresh(purchase)
    return purchase


async def get_purchase_by_invoice(
    session: AsyncSession, invoice_id: int
) -> Optional[Purchase]:
    result = await session.execute(
        select(Purchase).where(Purchase.invoice_id == invoice_id)
    )
    return result.scalar_one_or_none()


async def mark_purchase_paid(session: AsyncSession, invoice_id: int) -> Optional[Purchase]:
    await session.execute(
        update(Purchase).where(Purchase.invoice_id == invoice_id).values(status="paid")
    )
    await session.commit()
    return await get_purchase_by_invoice(session, invoice_id)


async def get_paid_count(session: AsyncSession) -> int:
    result = await session.execute(
        select(func.count()).select_from(Purchase).where(Purchase.status == "paid")
    )
    return result.scalar_one()


async def user_already_bought(
    session: AsyncSession, user_id: int, product_id: int
) -> bool:
    result = await session.execute(
        select(Purchase).where(
            Purchase.user_id == user_id,
            Purchase.product_id == product_id,
            Purchase.status == "paid",
        )
    )
    return result.scalar_one_or_none() is not None
