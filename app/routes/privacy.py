"""DELETE /api/results/{session_id} — right to erasure (DPDP)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.result import ScoringResult

router = APIRouter()


@router.delete("/results/{session_id}", status_code=204)
async def delete_results(
    session_id: str,
    db: AsyncSession = Depends(get_db),
) -> Response:
    result = await db.execute(
        select(ScoringResult).where(ScoringResult.session_id == session_id)
    )
    row = result.scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Session not found.")

    await db.execute(delete(ScoringResult).where(ScoringResult.session_id == session_id))
    await db.commit()
    return Response(status_code=204)
