"""
app/main.py — entry point.
Creates the bot, registers middlewares and routers, runs polling.
"""
import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage

from app.core.config import settings
from app.database import async_session_factory, engine
from app.database.models import Base
from app.handlers import admin, catalog, retention, user_base
from app.middlewares.db import DbSessionMiddleware
from app.middlewares.locale import LocaleMiddleware
from app.services.crypto_pay import close as close_crypto

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


async def create_tables() -> None:
    """Auto-create tables if they don't exist (dev convenience)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def main() -> None:
    logger.info("Starting AI OFM Store Bot...")

    # ── Database ──────────────────────────────────────────────────────────────
    await create_tables()

    # ── Bot & Dispatcher ──────────────────────────────────────────────────────
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    storage = RedisStorage.from_url(settings.redis_url)
    dp = Dispatcher(storage=storage)

    # ── Global middlewares ────────────────────────────────────────────────────────
    # DB must be registered FIRST so session is available to LocaleMiddleware
    dp.update.middleware(DbSessionMiddleware(async_session_factory))
    dp.update.middleware(LocaleMiddleware())

    # ── Routers (specific → general) ──────────────────────────────────────────
    # Admin routers first so admin callbacks don't fall through to catalog
    dp.include_router(admin.router)
    dp.include_router(retention.router)
    dp.include_router(catalog.router)
    dp.include_router(user_base.router)

    # ── Start polling ─────────────────────────────────────────────────────────
    try:
        logger.info("Bot is running. Press Ctrl+C to stop.")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        logger.info("Shutting down...")
        await close_crypto()
        await bot.session.close()
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
