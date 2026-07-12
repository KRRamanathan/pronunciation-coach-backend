"""Background job to purge expired scoring results (DPDP storage limitation)."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import delete

from app.db.session import AsyncSessionLocal
from app.models.result import ScoringResult

logger = logging.getLogger(__name__)

PURGE_INTERVAL_SECONDS = 3600  # hourly


async def purge_expired_results() -> int:
    now = datetime.now(timezone.utc)
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            delete(ScoringResult).where(ScoringResult.retention_expiry_at < now)
        )
        await session.commit()
        count = result.rowcount or 0
        if count:
            logger.info("Purged %d expired scoring results", count)
        return count


async def retention_loop() -> None:
    while True:
        try:
            await purge_expired_results()
        except Exception:
            logger.exception("Retention purge failed")
        await asyncio.sleep(PURGE_INTERVAL_SECONDS)
