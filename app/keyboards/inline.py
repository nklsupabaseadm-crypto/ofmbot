"""
All keyboards in one place.
Returns InlineKeyboardMarkup objects ready to pass to send_message/send_photo.
"""
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.database.models import Product
from app.locales.i18n import t


def start_keyboard(lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=t("btn_catalog", lang), callback_data="catalog")
    if lang == "ru":
        builder.button(text="🇬🇧 English", callback_data="set_lang:en")
    else:
        builder.button(text="🇷🇺 Русский", callback_data="set_lang:ru")
    builder.adjust(1)
    return builder.as_markup()


def catalog_keyboard(products: list[Product], lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for p in products:
        builder.button(
            text=f"📦 {p.name} — {p.price_usdt} USDT",
            callback_data=f"product:{p.id}",
        )
    builder.adjust(1)
    return builder.as_markup()


def product_keyboard(product: Product, lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text=t("btn_buy", lang, price=product.price_usdt),
        callback_data=f"buy:{product.id}",
    )
    builder.button(text=t("btn_back", lang), callback_data="catalog")
    builder.adjust(1)
    return builder.as_markup()


def payment_keyboard(pay_url: str, invoice_id: int, lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t("btn_pay", lang), url=pay_url)],
            [
                InlineKeyboardButton(
                    text=t("btn_check", lang),
                    callback_data=f"check_payment:{invoice_id}",
                )
            ],
            [InlineKeyboardButton(text=t("btn_cancel", lang), callback_data="catalog")],
        ]
    )


def admin_keyboard(lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=t("btn_add_product", lang), callback_data="admin:add_product")
    builder.button(text=t("btn_broadcast", lang), callback_data="admin:broadcast")
    builder.adjust(1)
    return builder.as_markup()


def confirm_broadcast_keyboard(lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=t("btn_confirm_broadcast", lang), callback_data="admin:broadcast_confirm")
    builder.button(text=t("btn_cancel", lang), callback_data="admin:broadcast_cancel")
    builder.adjust(2)
    return builder.as_markup()
