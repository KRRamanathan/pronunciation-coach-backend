"""Allosaurus universal phone recognizer wrapper."""

from __future__ import annotations

import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)

_model = None

# Allosaurus IPA-like output -> our IPA symbols
ALLO_TO_IPA: dict[str, str] = {
    "th": "θ", "dh": "ð", "sh": "ʃ", "zh": "ʒ", "ch": "tʃ", "jh": "dʒ",
    "ng": "ŋ", "y": "j", "w": "w", "r": "r", "l": "l", "h": "h",
    "aa": "ɑ", "ae": "æ", "ah": "ʌ", "ao": "ɔ", "aw": "aʊ", "ay": "aɪ",
    "eh": "ɛ", "er": "ɚ", "ey": "eɪ", "ih": "ɪ", "iy": "i", "ow": "oʊ",
    "oy": "ɔɪ", "uh": "ʊ", "uw": "u",
}


def load_model() -> None:
    global _model
    if _model is None:
        from allosaurus.app import read_recognizer

        logger.info("Loading Allosaurus phoneme recognizer...")
        _model = read_recognizer()
        logger.info("Allosaurus loaded.")


def _normalize_phoneme(token: str) -> str:
    t = token.strip().lower()
    if t in ALLO_TO_IPA:
        return ALLO_TO_IPA[t]
    if len(t) == 1:
        return t
    return t


def _parse_allosaurus_output(raw: str) -> list[str]:
    """Parse Allosaurus output into IPA phoneme list."""
    if not raw or not raw.strip():
        return []
    # Allosaurus may return space-separated phonemes or timestamped format
    tokens = re.split(r"\s+", raw.strip())
    phonemes: list[str] = []
    for tok in tokens:
        # Skip timestamp tokens like "0.12" or "0.12-0.45"
        if re.match(r"^[\d.\-]+$", tok):
            continue
        # Handle "phoneme" or "phoneme|score" formats
        base = tok.split("|")[0].split(":")[-1]
        if base:
            phonemes.append(_normalize_phoneme(base))
    return phonemes


def recognize_phonemes(audio_path: str | Path) -> list[str]:
    """Recognize phoneme sequence for an audio segment."""
    if _model is None:
        load_model()
    assert _model is not None
    raw = _model.recognize(str(audio_path), timestamp=False)
    return _parse_allosaurus_output(raw)


def recognize_word_phonemes(
    full_audio_path: str | Path,
    word_segments: list[tuple[float, float]],
) -> list[list[str]]:
    """
    Slice audio by Whisper word boundaries and run Allosaurus per segment.
    word_segments: list of (start_sec, end_sec) tuples.
    """
    results: list[list[str]] = []
    parent = Path(full_audio_path).parent

    for start_sec, end_sec in word_segments:
        if end_sec <= start_sec:
            results.append([])
            continue

        start_ms = int(start_sec * 1000)
        end_ms = int(end_sec * 1000)
        tmp_path = parent / f"_seg_{start_ms}_{end_ms}.wav"

        try:
            if not _export_segment_wav(full_audio_path, start_sec, end_sec, tmp_path):
                results.append([])
                continue
            phonemes = recognize_phonemes(tmp_path)
            results.append(phonemes)
        finally:
            tmp_path.unlink(missing_ok=True)

    return results


def _export_segment_wav(
    full_audio_path: str | Path,
    start_sec: float,
    end_sec: float,
    out_path: Path,
) -> bool:
    import av

    wrote = False
    with av.open(str(full_audio_path)) as inp:
        in_stream = inp.streams.audio[0]
        resampler = av.audio.resampler.AudioResampler(
            format="s16",
            layout="mono",
            rate=16000,
        )
        with av.open(str(out_path), "w", format="wav") as out:
            out_stream = out.add_stream("pcm_s16le", rate=16000, layout="mono")
            for frame in inp.decode(in_stream):
                if frame.time is None:
                    continue
                frame_end = frame.time + float(frame.samples) / float(frame.rate)
                if frame_end <= start_sec:
                    continue
                if frame.time >= end_sec:
                    break
                for resampled in resampler.resample(frame):
                    wrote = True
                    for packet in out_stream.encode(resampled):
                        out.mux(packet)
            if wrote:
                for packet in out_stream.encode(None):
                    out.mux(packet)
    return wrote
