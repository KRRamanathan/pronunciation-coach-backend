"""Scoring engine: phoneme diff, accuracy/fluency scores, feedback assembly."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from app.services import feedback_templates
from app.services.g2p import expected_phonemes_for_word
from app.services.whisper_stt import WordSegment

ErrorType = Literal["none", "mispronunciation", "omission", "insertion", "unclear"]

LOW_CONFIDENCE_THRESHOLD = 0.55
UNCLEAR_CONFIDENCE_THRESHOLD = 0.35


@dataclass
class WordScore:
    word: str
    start_ms: int
    end_ms: int
    expected_phonemes: list[str]
    actual_phonemes: list[str]
    accuracy_score: int
    error_type: ErrorType
    feedback: str


@dataclass
class ScoringOutput:
    overall_score: int
    accuracy_score: int
    fluency_score: int
    transcript: str
    words: list[WordScore]


def _levenshtein(a: list[str], b: list[str]) -> int:
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        curr = [i]
        for j, cb in enumerate(b, 1):
            cost = 0 if ca == cb else 1
            curr.append(min(prev[j] + 1, curr[j - 1] + 1, prev[j - 1] + cost))
        prev = curr
    return prev[-1]


def _align_operations(
    expected: list[str], actual: list[str]
) -> list[tuple[str, str | None, str | None]]:
    """Return list of (op, exp_phoneme, act_phoneme) for substitutions/deletions/insertions."""
    m, n = len(expected), len(actual)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            cost = 0 if expected[i - 1] == actual[j - 1] else 1
            dp[i][j] = min(dp[i - 1][j] + 1, dp[i][j - 1] + 1, dp[i - 1][j - 1] + cost)

    ops: list[tuple[str, str | None, str | None]] = []
    i, j = m, n
    while i > 0 or j > 0:
        if i > 0 and j > 0 and dp[i][j] == dp[i - 1][j - 1] + (0 if expected[i - 1] == actual[j - 1] else 1):
            if expected[i - 1] != actual[j - 1]:
                ops.append(("substitution", expected[i - 1], actual[j - 1]))
            i -= 1
            j -= 1
        elif i > 0 and dp[i][j] == dp[i - 1][j] + 1:
            ops.append(("deletion", expected[i - 1], None))
            i -= 1
        else:
            ops.append(("insertion", None, actual[j - 1]))
            j -= 1
    ops.reverse()
    return ops


def _word_accuracy(expected: list[str], actual: list[str]) -> int:
    if not expected:
        return 100 if not actual else max(0, 100 - len(actual) * 20)
    dist = _levenshtein(expected, actual)
    score = 100 * (1 - dist / len(expected))
    return max(0, min(100, int(round(score))))


def _classify_error(
    expected: list[str],
    actual: list[str],
    confidence: float,
) -> tuple[ErrorType, str]:
    if confidence < UNCLEAR_CONFIDENCE_THRESHOLD:
        return "unclear", ""

    if not expected and not actual:
        return "none", ""

    ops = _align_operations(expected, actual)
    if not ops:
        if confidence < LOW_CONFIDENCE_THRESHOLD:
            return "unclear", ""
        return "none", ""

    # Prioritize first significant error for feedback
    for op, exp_p, act_p in ops:
        if op == "substitution" and exp_p and act_p:
            tip = feedback_templates.tip_for_substitution(exp_p, act_p)
            return "mispronunciation", tip or feedback_templates.generic_mispronunciation("")
        if op == "deletion" and exp_p:
            return "omission", feedback_templates.tip_for_omission(exp_p)
        if op == "insertion" and act_p:
            return "insertion", feedback_templates.tip_for_insertion(act_p)

    if confidence < LOW_CONFIDENCE_THRESHOLD:
        return "unclear", ""

    return "none", ""


def _compute_fluency(words: list[WordSegment]) -> int:
    if len(words) < 2:
        return 70

    total_duration = words[-1].end - words[0].start
    if total_duration <= 0:
        return 50

    wpm = (len(words) / total_duration) * 60
    # Ideal conversational pace ~120-160 wpm for learners
    if 100 <= wpm <= 170:
        pace_score = 100
    elif wpm < 100:
        pace_score = max(40, int(100 - (100 - wpm) * 1.5))
    else:
        pace_score = max(40, int(100 - (wpm - 170) * 1.2))

    # Penalize long pauses between words (> 0.8s)
    pause_penalty = 0
    for i in range(1, len(words)):
        gap = words[i].start - words[i - 1].end
        if gap > 0.8:
            pause_penalty += min(15, int((gap - 0.8) * 20))

    return max(0, min(100, pace_score - pause_penalty))


def score_pronunciation(
    whisper_words: list[WordSegment],
    actual_phoneme_lists: list[list[str]],
    transcript: str,
) -> ScoringOutput:
    word_scores: list[WordScore] = []

    for idx, w in enumerate(whisper_words):
        expected = expected_phonemes_for_word(w.word)
        actual = actual_phoneme_lists[idx] if idx < len(actual_phoneme_lists) else []
        accuracy = _word_accuracy(expected, actual)
        error_type, feedback = _classify_error(expected, actual, w.probability)

        if error_type == "unclear":
            feedback = feedback_templates.tip_for_unclear(w.word)
        elif error_type == "mispronunciation" and not feedback:
            feedback = feedback_templates.generic_mispronunciation(w.word)
        elif error_type == "none":
            feedback = ""

        word_scores.append(
            WordScore(
                word=w.word,
                start_ms=int(w.start * 1000),
                end_ms=int(w.end * 1000),
                expected_phonemes=expected,
                actual_phonemes=actual,
                accuracy_score=accuracy,
                error_type=error_type,
                feedback=feedback,
            )
        )

    if word_scores:
        accuracy_score = int(round(sum(ws.accuracy_score for ws in word_scores) / len(word_scores)))
    else:
        accuracy_score = 0

    fluency_score = _compute_fluency(whisper_words)
    overall_score = int(round(accuracy_score * 0.7 + fluency_score * 0.3))

    return ScoringOutput(
        overall_score=overall_score,
        accuracy_score=accuracy_score,
        fluency_score=fluency_score,
        transcript=transcript,
        words=word_scores,
    )
