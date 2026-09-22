"""Tesseract OCR. Not installed on the dev machine yet (DECISIONS D9): until it is, pages that need OCR are
reported as unusable by the parser and never indexed. Page OCR itself is implemented once Tesseract is available
and can be tested against real pages."""

from __future__ import annotations

import shutil
from functools import lru_cache
from pathlib import Path

_WINDOWS_DEFAULT = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")


@lru_cache(maxsize=1)
def tesseract_path() -> str | None:
    found = shutil.which("tesseract")
    if found:
        return found
    return str(_WINDOWS_DEFAULT) if _WINDOWS_DEFAULT.exists() else None


def tesseract_available() -> bool:
    return tesseract_path() is not None
