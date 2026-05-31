"""
Async broadcast service.
Telegram allows ~30 messages/second globally; we send in batches with sleep.
"""
import asyncio
import logging
from dataclasses import dataclass

from aiogram import Bot
from aiogram.types import InputMediaPhoto

logger = logging.getLogger(__name__)

_BATCH_SIZE = 25       # messages per batch
_BATCH_SLEEP = 1.0     # seconds between batches  (~25 msg/s, safe margin)


@dataclass
class BroadcastResult:
    sent: int = 0
    failed: int = 0


async def broadcast_message(
    bot: Bot,
    user_ids: list[int],
    text: str,
    photo_file_id: str | None = None,
) -> BroadcastResult:
    """
    Send *text* (with optional photo) to every user in *user_ids*.
    Respects Telegram rate limits via batch sleep.
    """
    result = BroadcastResult()

    for i in range(0, len(user_ids), _BATCH_SIZE):
        batch = user_ids[i : i + _BATCH_SIZE]
        tasks = [_send_one(bot, uid, text, photo_file_id) for uid in batch]
        outcomes = await asyncio.gather(*tasks, return_exceptions=True)

        for outcome in outcomes:
            if isinstance(outcome, Exception):
                result.failed += 1
                logger.warning("Broadcast failed for one user: %s", outcome)
            else:
                result.sent += 1

        if i + _BATCH_SIZE < len(user_ids):
            await asyncio.sleep(_BATCH_SLEEP)

    logger.info("Broadcast done: %d sent, %d failed", result.sent, result.failed)
    return result


async def _send_one(
    bot: Bot,
    user_id: int,
    text: str,
    photo_file_id: str | None,
) -> None:
    if photo_file_id:
        await bot.send_photo(chat_id=user_id, photo=photo_file_id, caption=text, parse_mode="HTML")
    else:
        await bot.send_message(chat_id=user_id, text=text, parse_mode="HTML")
