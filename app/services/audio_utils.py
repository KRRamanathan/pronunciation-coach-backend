"""Audio validation utilities."""

from __future__ import annotations

import io
import logging
import shutil
import subprocess
import tempfile
from pathlib import Path

import av

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {".wav", ".mp3", ".m4a", ".webm", ".ogg", ".opus"}
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
    "audio/opus",
}


def _configure_ffmpeg() -> None:
    """Configure pydub fallback paths when system ffmpeg is unavailable."""
    from pydub import AudioSegment

    ffmpeg_path = shutil.which("ffmpeg")
    ffprobe_path = shutil.which("ffprobe")
    if ffmpeg_path:
        AudioSegment.converter = ffmpeg_path
        AudioSegment.ffmpeg = ffmpeg_path
        AudioSegment.ffprobe = ffprobe_path or ffmpeg_path
        return
    try:
        import imageio_ffmpeg

        ffmpeg = Path(imageio_ffmpeg.get_ffmpeg_exe())
        AudioSegment.converter = str(ffmpeg)
        AudioSegment.ffmpeg = str(ffmpeg)
        ffprobe = ffmpeg.parent / "ffprobe.exe"
        AudioSegment.ffprobe = str(ffprobe if ffprobe.exists() else ffmpeg)
    except Exception:
        logger.debug("ffmpeg not configured for pydub fallback")


_configure_ffmpeg()


def get_audio_duration_sec(path: str | Path) -> float:
    with av.open(str(path)) as container:
        if container.duration:
            return float(container.duration) / 1_000_000
        total = 0.0
        stream = container.streams.audio[0]
        for frame in container.decode(stream):
            if frame.time is not None:
                frame_end = frame.time + (frame.samples / frame.rate)
                total = max(total, frame_end)
        return total


def get_audio_duration_from_bytes(data: bytes, filename: str) -> float:
    ext = Path(filename).suffix.lower().lstrip(".") or "wav"
    with tempfile.NamedTemporaryFile(suffix=f".{ext}", delete=False) as tmp:
        tmp.write(data)
        tmp_path = tmp.name
    try:
        return get_audio_duration_sec(tmp_path)
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def normalize_to_wav(src_path: Path, dest_path: Path) -> None:
    """Convert any supported audio to 16 kHz mono WAV using PyAV."""
    with av.open(str(src_path)) as inp:
        in_stream = inp.streams.audio[0]
        resampler = av.audio.resampler.AudioResampler(
            format="s16",
            layout="mono",
            rate=16000,
        )
        with av.open(str(dest_path), "w", format="wav") as out:
            out_stream = out.add_stream("pcm_s16le", rate=16000, layout="mono")
            for frame in inp.decode(in_stream):
                for resampled in resampler.resample(frame):
                    for packet in out_stream.encode(resampled):
                        out.mux(packet)
            for packet in out_stream.encode(None):
                out.mux(packet)
