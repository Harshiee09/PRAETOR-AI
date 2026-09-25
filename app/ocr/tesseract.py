"""Tesseract OCR: the engine on Linux servers (DECISIONS D58; Windows uses the built-in engine, D55).

`tesseract_images` reads PNG pages through `tesseract stdin stdout ... tsv` (bytes over stdin, nothing written to
disk), several pages at a time, and groups the recognised words into lines with positions, like the Windows path.
The corpus parser still only uses `tesseract_available` (D9).
"""

from __future__ import annotations

import os
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from pathlib import Path

from app.ocr.windows_ocr import OcrLine, OcrUnavailable

_WINDOWS_DEFAULT = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")
WORKERS = 4


@lru_cache(maxsize=1)
def tesseract_path() -> str | None:
    found = shutil.which("tesseract")
    if found:
        return found
    return str(_WINDOWS_DEFAULT) if _WINDOWS_DEFAULT.exists() else None


def tesseract_available() -> bool:
    return tesseract_path() is not None


@lru_cache(maxsize=1)
def tesseract_languages() -> tuple[str, ...]:
    exe = tesseract_path()
    if not exe:
        return ()
    try:
        out = subprocess.run([exe, "--list-langs"], capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        return ()
    return tuple(line.strip() for line in out.stdout.splitlines()[1:] if line.strip())


def parse_tsv(tsv: str, scale: float) -> list[OcrLine]:
    """Tesseract TSV (word rows, level 5) -> lines in reading order; positions multiplied by `scale`."""
    rows = [r.split("\t") for r in tsv.splitlines() if r.strip()]
    if not rows:
        return []
    col = {name: i for i, name in enumerate(rows[0])}
    groups: dict[tuple, list[tuple]] = {}
    for f in rows[1:]:
        if len(f) < len(col) or f[col["level"]] != "5":
            continue
        text = f[col["text"]].strip()
        try:
            conf = float(f[col["conf"]])
        except ValueError:
            continue
        if not text or conf < 0:
            continue
        key = tuple(int(f[col[k]]) for k in ("page_num", "block_num", "par_num", "line_num"))
        groups.setdefault(key, []).append((int(f[col["left"]]), int(f[col["top"]]), int(f[col["width"]]),
                                           int(f[col["height"]]), text))
    lines = []
    for words in groups.values():
        words.sort(key=lambda w: w[0])
        lines.append(OcrLine(text=" ".join(w[4] for w in words), x0=min(w[0] for w in words) * scale,
                             x1=max(w[0] + w[2] for w in words) * scale, top=min(w[1] for w in words) * scale,
                             size=round(max(w[3] for w in words) * scale, 1)))
    return lines


def tesseract_images(images: dict[int, bytes], language: str, timeout_s: float = 240,
                     dpi: int = 200) -> dict[int, list[OcrLine]]:
    exe = tesseract_path()
    if not exe:
        raise OcrUnavailable("Tesseract is not installed")
    env = {**os.environ, "OMP_THREAD_LIMIT": "1"}  # one core per page; pages run side by side

    def one(item: tuple[int, bytes]) -> tuple[int, list[OcrLine]]:
        number, png = item
        try:
            out = subprocess.run([exe, "stdin", "stdout", "-l", language, "--psm", "3", "--dpi", str(dpi), "tsv"],
                                 input=png, capture_output=True, timeout=timeout_s, env=env)
        except subprocess.TimeoutExpired as exc:
            raise OcrUnavailable(f"OCR took longer than {timeout_s:.0f} s") from exc
        if out.returncode != 0:
            raise OcrUnavailable(f"Tesseract failed: {out.stderr.decode('utf-8', 'replace').strip()[:300]}")
        return number, parse_tsv(out.stdout.decode("utf-8", "replace"), 72 / dpi)

    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        return dict(pool.map(one, images.items()))
