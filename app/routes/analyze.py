"""POST /api/analyze — upload audio and run scoring pipeline."""

from __future__ import annotations

import json
import logging
import tempfile
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.session import get_db
from app.models.result import ScoringResult
from app.services import phoneme_id, whisper_stt
from app.services.audio_utils import (
    ALLOWED_EXTENSIONS,
    get_audio_duration_sec,
    normalize_to_wav,
)
from app.services.gemini_polish import polish_feedback
from app.services.scoring import score_pronunciation

logger = logging.getLogger(__name__)
router = APIRouter()


class WordResult(BaseModel):
    word: str
    start_ms: int
    end_ms: int
    expected_phonemes: list[str]
    actual_phonemes: list[str]
    accuracy_score: int
    error_type: str
    feedback: str


class AnalyzeResponse(BaseModel):
    session_id: str
    overall_score: int
    sub_scores: dict[str, int]
    transcript: str
    words: list[WordResult]
    created_at: str
    retention_expiry_at: str


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_audio(
    audio: UploadFile = File(...),
    session_id: str = Form(...),
    db: AsyncSession = Depends(get_db),
) -> AnalyzeResponse:
    settings = get_settings()

    # Verify consent was recorded
    result = await db.execute(
        select(ScoringResult).where(ScoringResult.session_id == session_id)
    )
    row = result.scalar_one_or_none()
    if row is None or not row.consent_accepted:
        raise HTTPException(status_code=403, detail="Consent must be accepted before analysis.")

    if not audio.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    ext = Path(audio.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    content = await audio.read()
    if len(content) > settings.max_upload_bytes:
        raise HTTPException(status_code=400, detail="File too large (max 15 MB).")

    tmp_dir = Path(tempfile.mkdtemp(prefix="pc_audio_"))
    raw_path = tmp_dir / f"upload{ext}"
    wav_path = tmp_dir / "normalized.wav"

    try:
        raw_path.write_bytes(content)

        duration = get_audio_duration_sec(raw_path)
        if duration < settings.min_duration_sec or duration > settings.max_duration_sec:
            raise HTTPException(
                status_code=400,
                detail=f"Audio must be {int(settings.min_duration_sec)}–{int(settings.max_duration_sec)} seconds. Got {duration:.1f}s.",
            )

        normalize_to_wav(raw_path, wav_path)

        transcription = whisper_stt.transcribe(wav_path)

        if transcription.language != "en" or transcription.language_probability < 0.7:
            raise HTTPException(
                status_code=400,
                detail="English only. Detected language is not English with sufficient confidence.",
            )

        if not transcription.words:
            raise HTTPException(
                status_code=400,
                detail="Could not detect any speech. Please speak clearly and try again.",
            )

        segments = [(w.start, w.end) for w in transcription.words]
        actual_phonemes = phoneme_id.recognize_word_phonemes(wav_path, segments)

        scoring = score_pronunciation(
            transcription.words,
            actual_phonemes,
            transcription.text,
        )

        # Optional Gemini polish for words with feedback
        feedback_indices = [i for i, w in enumerate(scoring.words) if w.feedback]
        if feedback_indices:
            tips = [scoring.words[i].feedback for i in feedback_indices]
            polished = await polish_feedback(tips)
            for idx, new_tip in zip(feedback_indices, polished):
                scoring.words[idx].feedback = new_tip

        now = datetime.now(timezone.utc)
        expiry = now + timedelta(days=settings.retention_days)

        words_payload = [
            WordResult(
                word=w.word,
                start_ms=w.start_ms,
                end_ms=w.end_ms,
                expected_phonemes=w.expected_phonemes,
                actual_phonemes=w.actual_phonemes,
                accuracy_score=w.accuracy_score,
                error_type=w.error_type,
                feedback=w.feedback,
            )
            for w in scoring.words
        ]

        if row:
            row.transcript = scoring.transcript
            row.overall_score = scoring.overall_score
            row.accuracy_score = scoring.accuracy_score
            row.fluency_score = scoring.fluency_score
            row.words_json = json.dumps([w.model_dump() for w in words_payload])
            row.retention_expiry_at = expiry
        else:
            row = ScoringResult(
                session_id=session_id,
                consent_accepted=True,
                transcript=scoring.transcript,
                overall_score=scoring.overall_score,
                accuracy_score=scoring.accuracy_score,
                fluency_score=scoring.fluency_score,
                words_json=json.dumps([w.model_dump() for w in words_payload]),
                retention_expiry_at=expiry,
            )
            db.add(row)

        await db.commit()

        return AnalyzeResponse(
            session_id=session_id,
            overall_score=scoring.overall_score,
            sub_scores={"accuracy": scoring.accuracy_score, "fluency": scoring.fluency_score},
            transcript=scoring.transcript,
            words=words_payload,
            created_at=now.isoformat(),
            retention_expiry_at=expiry.isoformat(),
        )
    finally:
        import shutil

        shutil.rmtree(tmp_dir, ignore_errors=True)


@router.get("/results/{session_id}", response_model=AnalyzeResponse)
async def get_results(session_id: str, db: AsyncSession = Depends(get_db)) -> AnalyzeResponse:
    result = await db.execute(
        select(ScoringResult).where(ScoringResult.session_id == session_id)
    )
    row = result.scalar_one_or_none()
    if row is None or not row.words_json or row.words_json == "[]":
        raise HTTPException(status_code=404, detail="Results not found.")

    words = [WordResult(**w) for w in json.loads(row.words_json)]
    return AnalyzeResponse(
        session_id=row.session_id,
        overall_score=row.overall_score,
        sub_scores={"accuracy": row.accuracy_score, "fluency": row.fluency_score},
        transcript=row.transcript,
        words=words,
        created_at=row.created_at.isoformat() if row.created_at else "",
        retention_expiry_at=row.retention_expiry_at.isoformat() if row.retention_expiry_at else "",
    )
