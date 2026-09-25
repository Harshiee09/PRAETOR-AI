"""Which OCR engine reads uploaded scans and photos: Windows OCR on the laptop (D55), Tesseract on Linux (D58).

`ocr_language` returns "<engine>:<languages>" (e.g. "windows:en-GB", "tesseract:eng+hin") or None when no engine
can read the script; `ocr_images` / `ocr_pages` dispatch on it.
"""

from __future__ import annotations

import sys

from app.ocr.tesseract import tesseract_available, tesseract_images, tesseract_languages
from app.ocr.windows_ocr import MIN_PAGE_CHARS, RENDER_DPI, OcrLine, OcrUnavailable, render_pages  # noqa: F401
from app.ocr.windows_ocr import ocr_images as windows_images
from app.ocr.windows_ocr import ocr_language as windows_language

# Tesseract languages per script; English is added so mixed pages (English headings, numbers) still read.
SCRIPT_LANGS = {
    "Latn": ["eng", "hin"], "Deva": ["hin", "mar", "eng"], "Beng": ["ben", "eng"], "Taml": ["tam", "eng"],
    "Telu": ["tel", "eng"], "Gujr": ["guj", "eng"], "Knda": ["kan", "eng"], "Mlym": ["mal", "eng"],
    "Guru": ["pan", "eng"], "Orya": ["ori", "eng"], "Arab": ["urd", "eng"],
}


def ocr_language(script: str) -> str | None:
    if sys.platform == "win32":
        lang = windows_language(script)
        if lang:
            return f"windows:{lang}"
    if tesseract_available():
        installed = set(tesseract_languages())
        wanted = [lang for lang in SCRIPT_LANGS.get(script, ["eng"]) if lang in installed]
        if wanted:
            return "tesseract:" + "+".join(wanted)
    return None


def ocr_images(images: dict[int, bytes], language: str, timeout_s: float = 240,
               dpi: int = RENDER_DPI) -> dict[int, list[OcrLine]]:
    engine, _, lang = language.partition(":")
    if engine == "windows":
        return windows_images(images, lang, timeout_s, dpi)
    if engine == "tesseract":
        return tesseract_images(images, lang, timeout_s, dpi)
    raise OcrUnavailable(f"unknown OCR engine {language!r}")


def ocr_pages(data: bytes, page_numbers: list[int], language: str, timeout_s: float = 240,
              dpi: int = RENDER_DPI) -> dict[int, list[OcrLine]]:
    if not page_numbers:
        return {}
    return ocr_images(render_pages(data, page_numbers, dpi), language, timeout_s, dpi)
