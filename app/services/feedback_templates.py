"""Curated English-learner phoneme confusion tips (rule-based, no LLM)."""

CONFUSION_TIPS: dict[tuple[str, str], str] = {
    ("θ", "s"): "Your 'th' sound came out as 's'. Place your tongue lightly between your teeth and blow air — don't use your teeth like an 's'.",
    ("ð", "d"): "The voiced 'th' (as in 'the') sounded like 'd'. Keep your tongue between your teeth and add voice from your throat.",
    ("θ", "t"): "The 'th' sound was replaced with 't'. Soften it — tongue between teeth, not behind them.",
    ("ð", "z"): "Voiced 'th' came out as 'z'. Tongue between teeth with gentle voicing, not a buzzy 'z'.",
    ("v", "w"): "The 'v' sounded like 'w'. Bite your lower lip gently and push air through — 'v' needs lip contact.",
    ("w", "v"): "The 'w' sounded like 'v'. Round your lips without touching them to your teeth.",
    ("r", "l"): "The 'r' came out as 'l'. Curl your tongue back without touching the roof of your mouth.",
    ("l", "r"): "The 'l' sounded like 'r'. Touch the tip of your tongue to the ridge behind your upper teeth.",
    ("ɪ", "i"): "The short 'ih' (as in 'sit') was too long like 'ee'. Keep it short and relaxed.",
    ("i", "ɪ"): "The long 'ee' was too short. Stretch it slightly and smile a bit more.",
    ("æ", "ɛ"): "The 'a' in 'cat' sounded like 'e' in 'bet'. Open your mouth wider for 'æ'.",
    ("ɛ", "æ"): "The 'e' in 'bet' sounded like 'a' in 'cat'. Relax your jaw — less open mouth.",
    ("ʌ", "ɑ"): "The 'uh' in 'cup' was too open. Keep your mouth more neutral and relaxed.",
    ("ɑ", "ʌ"): "The 'ah' sound was too closed. Open your mouth a bit more.",
    ("ʃ", "s"): "'Sh' came out as 's'. Round your lips and push air forward over your tongue.",
    ("ʒ", "z"): "The 'zh' sound (as in 'measure') came out as 'z'. Round lips and soften the friction.",
    ("tʃ", "t"): "'Ch' lost its second part. Start with 't' then quickly release into 'sh'.",
    ("dʒ", "d"): "'J' sounded like plain 'd'. Add a quick 'zh' glide after the 'd'.",
    ("ŋ", "n"): "The '-ng' ending used 'n' instead. Raise the back of your tongue to block air through your nose.",
    ("n", "ŋ"): "An 'n' was used where '-ng' belongs. Close off airflow with the back of your tongue.",
    ("h", ""): "The 'h' sound was dropped. Breathe out gently before the vowel — like fogging a mirror.",
    ("f", "p"): "'F' came out as 'p'. Rest your top teeth on your lower lip and blow — no lip pop.",
    ("p", "f"): "'P' came out as 'f'. Close your lips fully, then release with a pop.",
    ("b", "p"): "'B' was too soft like 'p'. Add voice — feel your throat vibrate.",
    ("p", "b"): "'P' had too much voice like 'b'. Use just air pressure, no throat vibration.",
    ("s", "θ"): "'S' was used instead of 'th'. Move your tongue forward between your teeth.",
    ("z", "ð"): "'Z' replaced voiced 'th'. Tongue between teeth with voicing.",
    ("ɚ", "ə"): "The 'er' r-coloring was weak. Curl your tongue slightly while saying 'uh'.",
    ("aɪ", "a"): "The diphthong 'ai' (as in 'time') was cut short. Glide from 'ah' to 'ee'.",
    ("aʊ", "a"): "The 'ow' diphthong (as in 'house') needs a glide from 'ah' to 'oo'.",
    ("ɔɪ", "ɔ"): "The 'oy' sound (as in 'boy') needs a glide to 'ee'.",
    ("j", ""): "The 'y' glide before a vowel was dropped. Start with tongue high and lips spread.",
    ("w", ""): "The 'w' glide got dropped — round your lips before the vowel.",
    ("k", "g"): "'K' sounded voiced like 'g'. Keep your throat still — no vibration.",
    ("g", "k"): "'G' was too voiceless like 'k'. Activate your vocal cords.",
    ("t", "d"): "'T' sounded like 'd'. Use a sharper, voiceless release.",
    ("d", "t"): "'D' sounded like 't'. Add clear voicing throughout.",
    ("m", "n"): "'M' came out as 'n'. Close your lips completely for 'm'.",
    ("n", "m"): "'N' came out as 'm'. Keep your lips open and tongue on the ridge.",
}


def tip_for_substitution(expected: str, actual: str) -> str | None:
    return CONFUSION_TIPS.get((expected, actual))


def tip_for_omission(phoneme: str) -> str:
    return (
        f"The '{phoneme}' sound was missing. "
        f"Try exaggerating it slightly — record yourself and compare to a native speaker."
    )


def tip_for_insertion(phoneme: str) -> str:
    return (
        f"An extra '{phoneme}' sound appeared. "
        f"Slow down and focus on saying only the sounds in the word."
    )


def tip_for_unclear(word: str) -> str:
    return (
        f"'{word}' was hard to hear clearly. "
        f"Speak a bit louder, reduce background noise, and enunciate each syllable."
    )


def generic_mispronunciation(word: str) -> str:
    return (
        f"'{word}' wasn't quite right. "
        f"Listen to a native pronunciation, then try again slowly — focus on one sound at a time."
    )
