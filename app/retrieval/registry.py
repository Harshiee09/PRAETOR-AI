"""Statute registry and alias matching (data/registry/statutes.yaml + aliases.yaml).

`find_acts` returns Act mentions in a text, longest match first: "Consumer Protection Act 1986" resolves to the
1986 Act, a bare "Consumer Protection Act" to the alias's first id. Each mention carries the id it literally names
(`names`, used by exact section lookup) and the ids to search (`expands_to`, which adds successors/predecessors).
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import regex
import yaml


def _words(s: str) -> str:
    return r"\s+".join(regex.escape(w) for w in s.split())


def _name_pattern(name: str) -> str:
    """'Consumer Protection Act, 1986' also matches 'Consumer Protection Act 1986'."""
    m = regex.match(r"^(.*?),?\s*(\d{4})$", name)
    return _words(m.group(1)) + r",?\s*" + m.group(2) if m else _words(name)


@dataclass(frozen=True)
class ActMention:
    text: str
    start: int
    end: int
    names: str
    expands_to: tuple[str, ...]


class Registry:
    def __init__(self, registry_dir: Path):
        self.statutes: dict[str, dict] = {
            s["id"]: s for s in yaml.safe_load((registry_dir / "statutes.yaml").read_text(encoding="utf-8"))}
        aliases = yaml.safe_load((registry_dir / "aliases.yaml").read_text(encoding="utf-8"))
        entries: list[tuple[str, tuple[str, ...]]] = []
        for sid, s in self.statutes.items():
            succ = tuple(x for x in [s.get("successor"), s.get("replaces")] if x)
            for name in {s["title"], s["short_title"], s["title"].removeprefix("The ")}:
                entries.append((name, (sid, *succ)))
        for a in aliases:
            entries.append((a["alias"], tuple(a["expands_to"])))
        # longest first so "Consumer Protection Act, 1986" beats "Consumer Protection Act"
        entries.sort(key=lambda e: -len(e[0]))
        self._entries = entries
        parts = [f"(?P<a{i}>{_name_pattern(name)})" for i, (name, _) in enumerate(entries)]
        self._pattern = regex.compile(r"(?<![\w.])(?:" + "|".join(parts) + r")(?![\w])", regex.I)

    def find_acts(self, text: str) -> list[ActMention]:
        out = []
        for m in self._pattern.finditer(text):
            idx = int(m.lastgroup[1:])
            name, ids = self._entries[idx]
            out.append(ActMention(m.group(0), m.start(), m.end(), ids[0], ids))
        return out

    def get(self, sid: str) -> dict | None:
        return self.statutes.get(sid)

    def short_title(self, sid: str) -> str:
        s = self.statutes.get(sid)
        return s["short_title"] if s else sid

    def by_short_title(self, short_title: str) -> dict | None:
        return next((s for s in self.statutes.values() if s["short_title"] == short_title), None)


@lru_cache(maxsize=4)
def load_registry(registry_dir: str) -> Registry:
    return Registry(Path(registry_dir))
