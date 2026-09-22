"""Loaders for the committed registries under data/registry/."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml


@lru_cache(maxsize=8)
def _load(path: str) -> dict | list:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def load_sources(registry_dir: Path) -> dict:
    return _load(str(registry_dir / "sources.yaml"))


def load_statutes(registry_dir: Path) -> list[dict]:
    return _load(str(registry_dir / "statutes.yaml"))
