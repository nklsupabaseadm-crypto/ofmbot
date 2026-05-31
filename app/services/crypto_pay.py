"""
Wrapper around aiocryptopay.
All CryptoBot API calls go through this module.
"""
from aiocryptopay import AioCryptoPay, Networks

from app.core.config import settings

_network = Networks.MAIN_NET if settings.crypto_pay_network == "mainnet" else Networks.TEST_NET

# Single shared client instance
crypto_client = AioCryptoPay(token=settings.crypto_pay_token, network=_network)


async def create_invoice(amount: float, product_name: str) -> tuple[int, str]:
    """
    Create a USDT invoice in CryptoBot.
    Returns (invoice_id, pay_url).
    """
    invoice = await crypto_client.create_invoice(
        asset="USDT",
        amount=amount,
        description=f"AI OFM Store — {product_name}",
        expires_in=3600,  # 1 hour
    )
    return invoice.invoice_id, invoice.bot_invoice_url


async def check_invoice_status(invoice_id: int) -> str:
    """
    Fetch invoice status from CryptoBot.
    Returns one of: "active" | "paid" | "expired"
    """
    invoices = await crypto_client.get_invoices(invoice_ids=[invoice_id])
    if not invoices:
        return "expired"
    return invoices[0].status  # type: ignore[union-attr]


async def close() -> None:
    """Close the HTTP session — call on bot shutdown."""
    await crypto_client.close()
