"""Answer cache in the SQLite `cache` table (API only).

The key is a hash of the normalised question and everything that could change the answer: mode, prompt version, model
and its digest, decoding, the index's corpus hash, the registries and the evidence threshold. So a new prompt, model,
index or registry entry simply misses. The stored value is the response without its trace id; the question itself is
never stored (only inside the hash), and the database lives in the gitignored data/processed/.
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import unicodedata
from datetime import datetime, timedelta, timezone


def _now() -> datetime:
    return datetime.now(timezone.utc)


def normalise_question(q: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", q)).strip().casefold()


def cache_key(question: str, version: dict) -> str:
    material = json.dumps({"q": normalise_question(question), **version}, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def get(conn: sqlite3.Connection, key: str) -> dict | None:
    row = conn.execute("SELECT value, expires_at FROM cache WHERE key = ? AND task = 'answer'", (key,)).fetchone()
    if row is None or row[1] <= _now().isoformat():
        return None
    return json.loads(row[0])


def put(conn: sqlite3.Connection, key: str, value: dict, ttl_hours: int) -> None:
    now = _now()
    with conn:
        conn.execute("INSERT OR REPLACE INTO cache (key, task, value, created_at, expires_at) VALUES (?, 'answer', ?, ?, ?)",
                     (key, json.dumps(value, ensure_ascii=False), now.isoformat(),
                      (now + timedelta(hours=ttl_hours)).isoformat()))
        conn.execute("DELETE FROM cache WHERE expires_at <= ?", (now.isoformat(),))


def count(conn: sqlite3.Connection) -> int:
    return conn.execute("SELECT COUNT(*) FROM cache WHERE task = 'answer' AND expires_at > ?",
                        (_now().isoformat(),)).fetchone()[0]


def cacheable(response: dict) -> bool:
    """Transient failures are not cached: an answer produced because Ollama was unreachable would otherwise stick."""
    return not any(w.startswith(("ollama unavailable", "The generated answer was not grounded"))
                   for w in response.get("warnings", []))
