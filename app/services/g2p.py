"""Expected phoneme sequences via g2p_en (CMU Pronouncing Dictionary)."""

from __future__ import annotations

import re

from g2p_en import G2p

_g2p: G2p | None = None

# ARPAbet (CMU) -> IPA mapping for learner-facing output
ARPABET_TO_IPA: dict[str, str] = {
    "AA": "ɑ", "AE": "æ", "AH": "ʌ", "AO": "ɔ", "AW": "aʊ", "AY": "aɪ",
    "B": "b", "CH": "tʃ", "D": "d", "DH": "ð", "EH": "ɛ", "ER": "ɚ",
    "EY": "eɪ", "F": "f", "G": "g", "HH": "h", "IH": "ɪ", "IY": "i",
    "JH": "dʒ", "K": "k", "L": "l", "M": "m", "N": "n", "NG": "ŋ",
    "OW": "oʊ", "OY": "ɔɪ", "P": "p", "R": "r", "S": "s", "SH": "ʃ",
    "T": "t", "TH": "θ", "UH": "ʊ", "UW": "u", "V": "v", "W": "w",
    "Y": "j", "Z": "z", "ZH": "ʒ",
}


def _ensure_nltk_data() -> None:
    import nltk

    for resource in ("averaged_perceptron_tagger_eng", "cmudict"):
        try:
            nltk.data.find(f"taggers/{resource}" if "tagger" in resource else f"corpora/{resource}")
        except LookupError:
            nltk.download(resource, quiet=True)


def _get_g2p() -> G2p:
    global _g2p
    if _g2p is None:
        _ensure_nltk_data()
        _g2p = G2p()
    return _g2p


def _arpabet_to_ipa(arpabet_tokens: list[str]) -> list[str]:
    ipa: list[str] = []
    for token in arpabet_tokens:
        base = re.sub(r"\d", "", token.upper())
        if base in ARPABET_TO_IPA:
            ipa.append(ARPABET_TO_IPA[base])
        elif base:
            ipa.append(base.lower())
    return ipa


def expected_phonemes_for_word(word: str) -> list[str]:
    """Return IPA phoneme list for a single English word."""
    clean = re.sub(r"[^a-zA-Z']", "", word).lower()
    if not clean:
        return []

    g2p = _get_g2p()
    tokens = g2p(clean)
    # g2p_en returns mixed chars and ARPAbet; keep only uppercase ARPAbet tokens
    arpabet = [t for t in tokens if t.isalpha() and t.upper() == t and len(t) >= 1]
    return _arpabet_to_ipa(arpabet)


def expected_phonemes_for_transcript(words: list[str]) -> dict[str, list[str]]:
    return {w: expected_phonemes_for_word(w) for w in words}
