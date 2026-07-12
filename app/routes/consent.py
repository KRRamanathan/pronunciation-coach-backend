"""POST /api/consent — record DPDP consent before audio upload."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.session import get_db
from app.models.result import ScoringResult

router = APIRouter()


class ConsentRequest(BaseModel):
    accepted: bool = Field(..., description="User must accept consent to proceed.")


class ConsentResponse(BaseModel):
    session_id: str
    consent_accepted: bool
    consent_timestamp: str
    retention_expiry_at: str


@router.post("/consent", response_model=ConsentResponse)
async def record_consent(
    body: ConsentRequest,
    db: AsyncSession = Depends(get_db),
) -> ConsentResponse:
    if not body.accepted:
        from fastapi import HTTPException

        raise HTTPException(status_code=400, detail="Consent must be accepted to use this service.")

    settings = get_settings()
    now = datetime.now(timezone.utc)
    expiry = now + timedelta(days=settings.retention_days)
    session_id = str(uuid.uuid4())

    row = ScoringResult(
        session_id=session_id,
        consent_accepted=True,
        consent_timestamp=now,
        retention_expiry_at=expiry,
    )
    db.add(row)
    await db.commit()

    return ConsentResponse(
        session_id=session_id,
        consent_accepted=True,
        consent_timestamp=now.isoformat(),
        retention_expiry_at=expiry.isoformat(),
    )
