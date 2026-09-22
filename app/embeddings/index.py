"""FAISS IndexIDMap2(IndexFlatIP) over L2-normalised bge-m3 vectors; the FAISS id is chunks.rowid.

`sync_index` makes the index match the chunk table: vectors whose chunk is gone are removed, chunks without a
vector are embedded and added. So re-running over an unchanged corpus embeds nothing. `index_manifest.json`
records the model, dimension and a corpus hash; readers refuse an index that disagrees with the configuration.
"""

from __future__ import annotations

import hashlib
import json
import logging
import sqlite3
import time
from pathlib import Path

import faiss
import numpy as np

from app.config import Settings
from app.embeddings.embedder import EMBED_DIM, Embedder
from app.ingestion.manifest import utc_now
from app.store.db import chunk_rowids, chunks_by_rowids

log = logging.getLogger(__name__)


def new_index(dim: int = EMBED_DIM) -> faiss.IndexIDMap2:
    return faiss.IndexIDMap2(faiss.IndexFlatIP(dim))


def load_index(path: Path) -> faiss.IndexIDMap2 | None:
    return faiss.read_index(str(path)) if path.exists() else None


def index_ids(index: faiss.IndexIDMap2) -> set[int]:
    return set(faiss.vector_to_array(index.id_map).tolist()) if index.ntotal else set()


def corpus_hash(conn: sqlite3.Connection) -> str:
    h = hashlib.sha256()
    for (cid,) in conn.execute("SELECT chunk_id FROM chunks ORDER BY chunk_id"):
        h.update(cid.encode())
    return h.hexdigest()


def sync_index(settings: Settings, conn: sqlite3.Connection, embedder: Embedder | None = None) -> dict:
    settings.index_dir.mkdir(parents=True, exist_ok=True)
    manifest = read_manifest(settings)
    index = load_index(settings.faiss_path)
    if index is None or (manifest and (manifest.get("embed_model") != settings.embed_model or manifest.get("dim") != EMBED_DIM)):
        if index is not None:
            log.warning("embedding model or dim changed; rebuilding the FAISS index from scratch")
        index = new_index()
    have = index_ids(index)
    want = set(chunk_rowids(conn))
    stale = sorted(have - want)
    missing = sorted(want - have)
    if stale:
        index.remove_ids(np.array(stale, dtype=np.int64))
    embed_s = 0.0
    if missing:
        embedder = embedder or Embedder(settings.embed_model, settings.embed_device, settings.embed_batch_size)
        t0 = time.perf_counter()
        for i in range(0, len(missing), 256):
            ids = missing[i:i + 256]
            rows = chunks_by_rowids(conn, ids)
            vecs = embedder.encode([r["embed_text"] for r in rows], show_progress=False)
            index.add_with_ids(vecs, np.array([r["rowid"] for r in rows], dtype=np.int64))
        embed_s = time.perf_counter() - t0
    faiss.write_index(index, str(settings.faiss_path))
    info = {
        "embed_model": settings.embed_model, "dim": EMBED_DIM, "normalized": True,
        "index_type": "IndexIDMap2(IndexFlatIP)", "chunk_count": len(want), "faiss_ntotal": int(index.ntotal),
        "corpus_hash": corpus_hash(conn), "created_at": utc_now(),
    }
    settings.index_manifest_path.write_text(json.dumps(info, indent=2), encoding="utf-8")
    return {**info, "added": len(missing), "removed": len(stale), "embed_seconds": round(embed_s, 1)}


def read_manifest(settings: Settings) -> dict | None:
    p = settings.index_manifest_path
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def check_index(settings: Settings, conn: sqlite3.Connection) -> list[str]:
    """Problems that must stop the API / ask: missing index, model or dimension mismatch, stale vectors."""
    problems = []
    m = read_manifest(settings)
    if not settings.faiss_path.exists() or m is None:
        return ["FAISS index or index_manifest.json missing: run `praetor index`"]
    if m["embed_model"] != settings.embed_model:
        problems.append(f"index built with {m['embed_model']}, EMBED_MODEL is {settings.embed_model}: run `praetor index`")
    if m["dim"] != EMBED_DIM:
        problems.append(f"index dimension {m['dim']} != {EMBED_DIM}: run `praetor index`")
    n = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
    if m["faiss_ntotal"] != n:
        problems.append(f"index has {m['faiss_ntotal']} vectors but the store has {n} chunks: run `praetor index`")
    return problems
