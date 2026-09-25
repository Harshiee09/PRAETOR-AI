"""SQLite store: documents, chunks (+ FTS5 external-content index), ingest runs, rejects, the answer cache and the vector map.

`chunks.rowid` is the FAISS id (IndexIDMap2), so a chunk and its vector share one integer key.
Columns are generated from the Chunk dataclass so the table can't drift from the schema; list/dict fields are
stored as JSON.
"""

from __future__ import annotations

import json
import sqlite3
import threading
from dataclasses import fields
from pathlib import Path

from app.chunking.schema import Chunk, Document, text_hash

FTS_TOKENIZER = "unicode61 remove_diacritics 0 categories 'L* N* Co M*'"
_JSON_FIELDS = {"domain_tags", "amendment_notes", "judges"}
_INT_FIELDS = {"page_start", "page_end", "token_count", "act_year", "para_start", "para_end"}
_REAL_FIELDS = {"ocr_confidence"}
CHUNK_FIELDS = [f.name for f in fields(Chunk)]


def _chunk_ddl() -> str:
    cols = []
    for name in CHUNK_FIELDS:
        typ = "INTEGER" if name in _INT_FIELDS else "REAL" if name in _REAL_FIELDS else "TEXT"
        extra = " NOT NULL UNIQUE" if name == "chunk_id" else ""
        cols.append(f"{name} {typ}{extra}")
    return (
        "CREATE TABLE IF NOT EXISTS chunks (\n  rowid INTEGER PRIMARY KEY,\n  "
        + ",\n  ".join(cols)
        + ",\n  text_sha1 TEXT NOT NULL,\n  UNIQUE(doc_id, text_sha1)\n)"
    )


SCHEMA = [
    """CREATE TABLE IF NOT EXISTS documents (
        doc_id TEXT PRIMARY KEY, doc_type TEXT NOT NULL, title TEXT NOT NULL, source_name TEXT NOT NULL,
        source_url TEXT NOT NULL, licence TEXT NOT NULL, retrieved_at TEXT NOT NULL, raw_path TEXT NOT NULL,
        raw_sha256 TEXT NOT NULL, authority TEXT NOT NULL, jurisdiction TEXT NOT NULL, language TEXT NOT NULL,
        script TEXT NOT NULL, is_translation INTEGER NOT NULL DEFAULT 0, translation_of TEXT,
        parser_version TEXT NOT NULL, extra TEXT, indexed_at TEXT NOT NULL)""",
    _chunk_ddl(),
    "CREATE INDEX IF NOT EXISTS ix_chunks_doc ON chunks(doc_id)",
    "CREATE INDEX IF NOT EXISTS ix_chunks_act_section ON chunks(act_title, section)",
    # `categories 'L* N* Co M*'` makes combining marks token characters: the default unicode61 splits Indic words at
    # every vowel sign (रजिस्ट्रीकरण -> र, रज, स, ट, करण), which wrecks BM25 for Hindi and Tamil (DECISIONS V22).
    f"""CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
        embed_text, content='chunks', content_rowid='rowid', tokenize="{FTS_TOKENIZER}")""",
    """CREATE TRIGGER IF NOT EXISTS chunks_ai AFTER INSERT ON chunks BEGIN
        INSERT INTO chunks_fts(rowid, embed_text) VALUES (new.rowid, new.embed_text); END""",
    """CREATE TRIGGER IF NOT EXISTS chunks_ad AFTER DELETE ON chunks BEGIN
        INSERT INTO chunks_fts(chunks_fts, rowid, embed_text) VALUES ('delete', old.rowid, old.embed_text); END""",
    """CREATE TABLE IF NOT EXISTS ingest_runs (
        run_id TEXT PRIMARY KEY, started_at TEXT NOT NULL, finished_at TEXT, docs_seen INTEGER, docs_changed INTEGER,
        docs_skipped INTEGER, chunks_added INTEGER, chunks_removed INTEGER, chunks_rejected INTEGER,
        duplicates_dropped INTEGER, notes TEXT)""",
    """CREATE TABLE IF NOT EXISTS rejects (
        run_id TEXT NOT NULL, doc_id TEXT, locator TEXT, problems TEXT NOT NULL)""",
    """CREATE TABLE IF NOT EXISTS cache (
        key TEXT PRIMARY KEY, task TEXT, value TEXT NOT NULL, created_at TEXT NOT NULL, expires_at TEXT NOT NULL)""",
    # What each FAISS vector was embedded from. chunks.rowid can be reused after a delete (no AUTOINCREMENT), so an id
    # match alone does not prove the vector belongs to the current text; sync_index compares these hashes.
    """CREATE TABLE IF NOT EXISTS vectors (rowid INTEGER PRIMARY KEY, embed_sha1 TEXT NOT NULL)""",
]


_READY: set[str] = set()
_READY_LOCK = threading.Lock()


def connect(path: Path) -> sqlite3.Connection:
    """Open a connection. Schema creation, the FTS migration and WAL mode run once per database file per process
    (they used to run on every request) and again if the file has been removed; per-connection settings (row factory,
    foreign keys) are applied every time."""
    path = Path(path)
    key = str(path.resolve())
    if key not in _READY or not path.exists():
        with _READY_LOCK:
            if key not in _READY or not path.exists():
                path.parent.mkdir(parents=True, exist_ok=True)
                conn = sqlite3.connect(path)
                conn.row_factory = sqlite3.Row
                conn.execute("PRAGMA foreign_keys = ON")
                conn.execute("PRAGMA journal_mode = WAL")
                _migrate_fts(conn)
                for stmt in SCHEMA:
                    conn.execute(stmt)
                conn.commit()
                _READY.add(key)
                return conn
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _migrate_fts(conn: sqlite3.Connection) -> None:
    """Recreate chunks_fts (and its triggers) when it was built with a different tokenizer, then rebuild it from
    the chunks table."""
    row = conn.execute("SELECT sql FROM sqlite_master WHERE name = 'chunks_fts'").fetchone()
    if row is None or "categories" in row[0]:
        return
    for stmt in ("DROP TRIGGER IF EXISTS chunks_ai", "DROP TRIGGER IF EXISTS chunks_ad", "DROP TABLE chunks_fts"):
        conn.execute(stmt)
    for stmt in SCHEMA:
        conn.execute(stmt)
    conn.execute("INSERT INTO chunks_fts(chunks_fts) VALUES ('rebuild')")
    conn.commit()


def _encode(name: str, value):
    if name in _JSON_FIELDS:
        return json.dumps(value, ensure_ascii=False) if value is not None else None
    return value


def _decode(name: str, value):
    if name in _JSON_FIELDS and value is not None:
        return json.loads(value)
    return value


def get_document(conn: sqlite3.Connection, doc_id: str) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM documents WHERE doc_id = ?", (doc_id,)).fetchone()


def replace_document(conn: sqlite3.Connection, doc: Document, chunks: list[Chunk],
                     indexed_at: str) -> tuple[list[int], int, list[tuple[str, str]]]:
    """Replace a document's chunks in one transaction. Returns (removed rowids, added count, dropped duplicates as
    (locator, locator of the row that kept the same text)) so a dropped chunk is never silent."""
    removed = [r[0] for r in conn.execute("SELECT rowid FROM chunks WHERE doc_id = ?", (doc.doc_id,))]
    conn.execute("DELETE FROM chunks WHERE doc_id = ?", (doc.doc_id,))
    conn.execute(
        """INSERT OR REPLACE INTO documents (doc_id, doc_type, title, source_name, source_url, licence, retrieved_at,
           raw_path, raw_sha256, authority, jurisdiction, language, script, is_translation, translation_of,
           parser_version, extra, indexed_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (doc.doc_id, doc.doc_type, doc.title, doc.source_name, doc.source_url, doc.licence, doc.retrieved_at,
         doc.raw_path, doc.raw_sha256, doc.authority, doc.jurisdiction, doc.language, doc.script,
         int(doc.is_translation), doc.translation_of, doc.parser_version, json.dumps(doc.extra, ensure_ascii=False),
         indexed_at),
    )
    cols = CHUNK_FIELDS + ["text_sha1"]
    sql = f"INSERT OR IGNORE INTO chunks ({', '.join(cols)}) VALUES ({', '.join('?' for _ in cols)})"
    added, dropped = 0, []
    for c in chunks:
        d = c.as_dict()
        h = text_hash(c.text)
        cur = conn.execute(sql, [_encode(n, d[n]) for n in CHUNK_FIELDS] + [h])
        added += cur.rowcount
        if not cur.rowcount:
            kept = conn.execute("SELECT locator FROM chunks WHERE doc_id = ? AND text_sha1 = ?", (doc.doc_id, h)).fetchone()
            dropped.append((c.locator, kept[0] if kept else "?"))
    return removed, added, dropped


def chunk_rowids(conn: sqlite3.Connection) -> list[int]:
    return [r[0] for r in conn.execute("SELECT rowid FROM chunks ORDER BY rowid")]


def chunks_by_rowids(conn: sqlite3.Connection, rowids: list[int]) -> list[dict]:
    if not rowids:
        return []
    out = {}
    for i in range(0, len(rowids), 500):
        batch = rowids[i:i + 500]
        q = f"SELECT rowid, * FROM chunks WHERE rowid IN ({','.join('?' for _ in batch)})"
        for row in conn.execute(q, batch):
            out[row["rowid"]] = {k: _decode(k, row[k]) for k in row.keys()}
    return [out[r] for r in rowids if r in out]


def chunk_by_id(conn: sqlite3.Connection, chunk_id: str) -> dict | None:
    row = conn.execute("SELECT rowid, * FROM chunks WHERE chunk_id = ?", (chunk_id,)).fetchone()
    return {k: _decode(k, row[k]) for k in row.keys()} if row else None
