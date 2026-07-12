"""Audio validation utilities."""

from __future__ import annotations

import io
from pathlib import Path

from pydub import AudioSegment

ALLOWED_EXTENSIONS = {".wav", ".mp3", ".m4a", ".webm", ".ogg"}
ALLOWED_MIME = {
    "audio/wav",
    "audio/x-wav",
    "audio/wave",
    "audio/mpeg",
    "audio/mp3",
    "audio/mp4",
    "audio/m4a",
    "audio/webm",
    "audio/ogg",
}


def get_audio_duration_sec(path: str | Path) -> float:
    audio = AudioSegment.from_file(str(path))
    return len(audio) / 1000.0


def get_audio_duration_from_bytes(data: bytes, filename: str) -> float:
    ext = Path(filename).suffix.lower().lstrip(".") or "wav"
    audio = AudioSegment.from_file(io.BytesIO(data), format=ext)
    return len(audio) / 1000.0


def normalize_to_wav(src_path: Path, dest_path: Path) -> None:
    audio = AudioSegment.from_file(str(src_path))
    audio = audio.set_channels(1).set_frame_rate(16000)
    audio.export(str(dest_path), format="wav")
