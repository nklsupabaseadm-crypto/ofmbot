from datetime import datetime
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Shared declarative base for all models."""


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    username: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    full_name: Mapped[str] = mapped_column(String(256), nullable=False, default="")
    language: Mapped[str] = mapped_column(String(8), nullable=False, default="en")
    registration_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    purchases: Mapped[list["Purchase"]] = relationship(back_populates="user", lazy="select")

    def __repr__(self) -> str:
        return f"<User tg_id={self.telegram_id} lang={self.language}>"


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    price_usdt: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    # Telegram file_id — stored once, reused forever (no re-uploads)
    file_id: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    purchases: Mapped[list["Purchase"]] = relationship(back_populates="product", lazy="select")

    def __repr__(self) -> str:
        return f"<Product id={self.id} name={self.name!r} price={self.price_usdt}>"


class Purchase(Base):
    __tablename__ = "purchases"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("products.id", ondelete="SET NULL"), nullable=True, index=True
    )
    # Invoice ID from CryptoBot
    invoice_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, unique=True)
    # "pending" | "paid" | "expired"
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="purchases")
    product: Mapped[Optional["Product"]] = relationship(back_populates="purchases")

    def __repr__(self) -> str:
        return f"<Purchase id={self.id} user={self.user_id} status={self.status}>"
