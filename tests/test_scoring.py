"""Unit tests for scoring engine (no ML models required)."""

from app.services.scoring import _levenshtein, _word_accuracy, score_pronunciation
from app.services.whisper_stt import WordSegment


def test_levenshtein_identical():
    assert _levenshtein(["k", "w", "ɪ", "k"], ["k", "w", "ɪ", "k"]) == 0


def test_levenshtein_omission():
    assert _levenshtein(["k", "w", "ɪ", "k"], ["k", "ɪ", "k"]) == 1


def test_word_accuracy_full():
    assert _word_accuracy(["k", "w", "ɪ", "k"], ["k", "w", "ɪ", "k"]) == 100


def test_word_accuracy_partial():
    assert _word_accuracy(["k", "w", "ɪ", "k"], ["k", "ɪ", "k"]) == 75


def test_score_pronunciation_integration():
    words = [
        WordSegment(word="hello", start=0.0, end=0.5, probability=0.9),
        WordSegment(word="world", start=0.6, end=1.0, probability=0.9),
    ]
    actual = [["h", "ɛ", "l", "oʊ"], ["w", "ɚ", "l", "d"]]
    result = score_pronunciation(words, actual, "hello world")
    assert 0 <= result.overall_score <= 100
    assert len(result.words) == 2
