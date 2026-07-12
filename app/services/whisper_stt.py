"""faster-whisper STT wrapper with word-level timestamps."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from app.config import get_settings

logger = logging.getLogger(__name__)

_model = None


@dataclass
class WordSegment:
    word: str
    start: float
    end: float
    probability: float


@dataclass
class TranscriptionResult:
    text: str
    language: str
    language_probability: float
    words: list[WordSegment]


def load_model() -> None:
    global _model
    if _model is None:
        from faster_whisper import WhisperModel

        settings = get_settings()
        logger.info("Loading faster-whisper model %s...", settings.whisper_model)
        _model = WhisperModel(
            settings.whisper_model,
            device="cpu",
            compute_type=settings.whisper_compute_type,
        )
        logger.info("Whisper model loaded.")


def transcribe(audio_path: str | Path) -> TranscriptionResult:
    if _model is None:
        load_model()
    assert _model is not None

    segments, info = _model.transcribe(
        str(audio_path),
        language="en",
        word_timestamps=True,
        vad_filter=True,
    )

    words: list[WordSegment] = []
    text_parts: list[str] = []

    for segment in segments:
        if segment.text.strip():
            text_parts.append(segment.text.strip())
        if segment.words:
            for w in segment.words:
                if w.word.strip():
                    words.append(
                        WordSegment(
                            word=w.word.strip(),
                            start=w.start,
                            end=w.end,
                            probability=w.probability or 0.0,
                        )
                    )

    return TranscriptionResult(
        text=" ".join(text_parts),
        language=info.language or "en",
        language_probability=info.language_probability or 0.0,
        words=words,
    )
