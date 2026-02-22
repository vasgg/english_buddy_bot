from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
import logging

from aiogram.exceptions import TelegramNetworkError, TelegramRetryAfter, TelegramServerError

MAX_PHOTO_CAPTION_LENGTH = 1024


def should_send_image_separately(message_text: str, send_image_separately: bool) -> bool:
    if send_image_separately:
        return True
    return len(message_text) > MAX_PHOTO_CAPTION_LENGTH


def is_retryable_delivery_exception(exc: Exception) -> bool:
    return isinstance(exc, (TelegramNetworkError, TelegramServerError, TelegramRetryAfter, TimeoutError))


async def send_with_single_retry(
    send_once: Callable[[], Awaitable[None]],
    *,
    base_retry_delay_seconds: float = 2.0,
    sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    logger: logging.Logger | None = None,
) -> tuple[int, Exception | None]:
    attempts = 0
    while attempts < 2:
        attempts += 1
        try:
            await send_once()
            return attempts, None
        except Exception as exc:  # noqa: BLE001
            if not is_retryable_delivery_exception(exc) or attempts >= 2:
                return attempts, exc

            retry_delay = base_retry_delay_seconds
            if isinstance(exc, TelegramRetryAfter):
                retry_after = getattr(exc, "retry_after", 0) or 0
                retry_delay = max(float(retry_after), base_retry_delay_seconds)
            if logger is not None:
                logger.warning(
                    "Transient delivery error (%s). Retrying once in %.2fs", type(exc).__name__, retry_delay
                )
            await sleep(retry_delay)

    return attempts, RuntimeError("Unexpected retry loop exit")
