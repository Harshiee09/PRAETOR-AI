"""Deterministic script detection by Unicode property (ISO 15924 codes), plus NFC normalisation."""

from __future__ import annotations

import unicodedata
from collections import Counter
from functools import lru_cache
from pathlib import Path

import regex
import yaml

# ISO 15924 code -> Unicode script property name used by the `regex` module
SCRIPTS = {
    "Latn": "Latin", "Deva": "Devanagari", "Beng": "Bengali", "Gujr": "Gujarati", "Guru": "Gurmukhi",
    "Knda": "Kannada", "Mlym": "Malayalam", "Orya": "Oriya", "Taml": "Tamil", "Telu": "Telugu",
    "Arab": "Arabic", "Olck": "Ol_Chiki", "Mtei": "Meetei_Mayek",
}
_PATTERNS = {code: regex.compile(rf"\p{{Script={name}}}") for code, name in SCRIPTS.items()}
_LETTER = regex.compile(r"\p{L}")


def nfc(text: str) -> str:
    return unicodedata.normalize("NFC", text)


def script_counts(text: str) -> Counter:
    counts: Counter = Counter()
    for ch in _LETTER.findall(text):
        for code, pat in _PATTERNS.items():
            if pat.match(ch):
                counts[code] += 1
                break
        else:
            counts["Zyyy"] += 1  # a letter in a script we don't track
    return counts


def dominant_script(text: str) -> tuple[str | None, float]:
    """(ISO 15924 code, share of letters) for the most common script, or (None, 0.0) when there are no letters."""
    counts = script_counts(text)
    total = sum(counts.values())
    if not total:
        return None, 0.0
    code, n = counts.most_common(1)[0]
    return code, n / total


def script_share(text: str, code: str) -> float:
    counts = script_counts(text)
    total = sum(counts.values())
    return counts.get(code, 0) / total if total else 0.0


@lru_cache(maxsize=1)
def languages() -> dict:
    return yaml.safe_load((Path(__file__).parent / "languages.yaml").read_text(encoding="utf-8"))


def primary_script(lang: str) -> str:
    return languages()[lang]["scripts"][0]
