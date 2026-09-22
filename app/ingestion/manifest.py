"""`data/raw/manifest.jsonl`: one row per raw file — source, url, local path, sha256, bytes, retrieved_at, licence."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class ManifestRow:
    source: str
    url: str
    local_path: str  # relative to DATA_DIR, forward slashes
    sha256: str
    bytes: int
    retrieved_at: str
    licence: str
    source_page: str | None = None  # human-facing page for the file (e.g. an India Code handle page)
    extra: dict | None = None


class Manifest:
    def __init__(self, path: Path, data_dir: Path):
        self.path = path
        self.data_dir = data_dir
        self._rows: dict[str, ManifestRow] = {}
        if path.exists():
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    row = ManifestRow(**json.loads(line))
                    self._rows[row.url] = row  # later rows win

    def get(self, url: str) -> ManifestRow | None:
        return self._rows.get(url)

    def rows(self, source: str | None = None) -> list[ManifestRow]:
        return [r for r in self._rows.values() if source is None or r.source == source]

    def is_current(self, url: str) -> bool:
        """True when the URL was fetched before and the local file still matches its recorded sha256."""
        row = self._rows.get(url)
        if row is None:
            return False
        local = self.data_dir / row.local_path
        return local.exists() and local.stat().st_size == row.bytes and sha256_file(local) == row.sha256

    def record(self, row: ManifestRow) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(row), ensure_ascii=False) + "\n")
        self._rows[row.url] = row

    def rel(self, path: Path) -> str:
        return path.resolve().relative_to(self.data_dir.resolve()).as_posix()
