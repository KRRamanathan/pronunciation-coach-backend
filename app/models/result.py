import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class ScoringResult(Base):
    __tablename__ = "scoring_results"

    session_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    consent_accepted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    consent_timestamp: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    transcript: Mapped[str] = mapped_column(Text, default="", nullable=False)
    overall_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    accuracy_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    fluency_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    words_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    retention_expiry_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
