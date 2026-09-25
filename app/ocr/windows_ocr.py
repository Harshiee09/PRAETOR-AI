"""OCR for uploaded pages that have no usable text layer, with the engine built into Windows 10/11
(Windows.Media.Ocr) reached through Windows PowerShell (DECISIONS D55).

Nothing to install and nothing leaves the laptop: pages are rendered with pypdfium2, sent to the OCR engine as PNG
bytes over stdin, and never written to disk. Only the languages installed in Windows are available (English on this
machine). Returned lines carry positions so the uploaded-document parser can build passages from them.
"""

from __future__ import annotations

import base64
import io
import json
import logging
import subprocess
import time
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

log = logging.getLogger(__name__)
SCRIPT = Path(__file__).with_name("windows_ocr.ps1")
RENDER_DPI = 200          # A4 at 200 dpi is 1654 x 2339 px, inside the engine's maximum image size
MIN_PAGE_CHARS = 20       # fewer recognised characters than this: the page stays unreadable


class OcrUnavailable(RuntimeError):
    pass


@dataclass
class OcrLine:
    text: str
    x0: float
    x1: float
    top: float
    size: float  # line height in points


def _powershell() -> list[str]:
    return ["powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File", str(SCRIPT)]


@lru_cache(maxsize=1)
def windows_ocr_languages() -> tuple[str, ...]:
    """Installed Windows OCR languages, e.g. ("en-GB", "en-US"); empty when the engine is not reachable."""
    probe = ("Add-Type -AssemblyName System.Runtime.WindowsRuntime; "
             "$null = [Windows.Media.Ocr.OcrEngine, Windows.Foundation, ContentType = WindowsRuntime]; "
             "[Windows.Media.Ocr.OcrEngine]::AvailableRecognizerLanguages | ForEach-Object { $_.LanguageTag }")
    try:
        out = subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", probe],
                             capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired):
        return ()
    return tuple(line.strip() for line in out.stdout.splitlines() if line.strip())


def ocr_language(script: str) -> str | None:
    """The Windows OCR language to use for a document in `script`, if one is installed (Latin script only here)."""
    if script != "Latn":
        return None
    langs = windows_ocr_languages()
    for preferred in ("en-IN", "en-GB", "en-US"):
        if preferred in langs:
            return preferred
    return next((lang for lang in langs if lang.startswith("en")), None)


def render_pages(data: bytes, page_numbers: list[int], dpi: int = RENDER_DPI) -> dict[int, bytes]:
    """PNG bytes for the given 1-based page numbers, rendered in memory."""
    import pypdfium2 as pdfium

    pdf = pdfium.PdfDocument(data)
    try:
        images = {}
        for number in page_numbers:
            page = pdf[number - 1]
            try:
                bitmap = page.render(scale=dpi / 72, grayscale=True)
                buffer = io.BytesIO()
                bitmap.to_pil().save(buffer, format="PNG", optimize=False)
                images[number] = buffer.getvalue()
            finally:
                page.close()
        return images
    finally:
        pdf.close()


def ocr_pages(data: bytes, page_numbers: list[int], language: str, timeout_s: float = 240,
              dpi: int = RENDER_DPI) -> dict[int, list[OcrLine]]:
    """Recognised lines per page (1-based page numbers), positions in PDF points like pdfplumber's."""
    if not page_numbers:
        return {}
    t0 = time.perf_counter()
    images = render_pages(data, page_numbers, dpi)
    payload = "".join(json.dumps({"page": n, "png": base64.b64encode(png).decode("ascii")}) + "\n"
                      for n, png in images.items())
    try:
        out = subprocess.run(_powershell() + ["-Lang", language], input=payload.encode("utf-8"),
                             capture_output=True, timeout=timeout_s)
    except FileNotFoundError as exc:
        raise OcrUnavailable("Windows PowerShell is not available") from exc
    except subprocess.TimeoutExpired as exc:
        raise OcrUnavailable(f"OCR took longer than {timeout_s:.0f} s") from exc
    if out.returncode != 0:
        raise OcrUnavailable(f"Windows OCR failed: {out.stderr.decode('utf-8', 'replace').strip()[:300]}")
    pages = json.loads(out.stdout.decode("utf-8-sig") or "[]")
    scale = 72 / dpi
    result: dict[int, list[OcrLine]] = {}
    for page in pages if isinstance(pages, list) else [pages]:
        lines = page.get("lines") or []
        lines = lines if isinstance(lines, list) else [lines]
        result[int(page["page"])] = [OcrLine(text=str(line["text"]), x0=float(line["x0"]) * scale,
                                             x1=float(line["x1"]) * scale, top=float(line["top"]) * scale,
                                             size=round(float(line["height"]) * scale, 1))
                                     for line in lines if str(line.get("text", "")).strip()]
    log.info("ocr done", extra={"pages": len(page_numbers), "language": language,
                                "seconds": round(time.perf_counter() - t0, 1)})
    return result
