"""FAISS sync: a vector must belong to the chunk text that now owns its id.

chunks.rowid is the FAISS id and SQLite reuses the highest rowids after a delete, so re-indexing a changed document
can hand an old id to new text. The embedder here is a deterministic stand-in (hash -> unit vector): the test is about
which texts get embedded, not about embedding quality.
"""

import dataclasses
import hashlib
from types import SimpleNamespace

import numpy as np

from app.embeddings.index import load_index, sync_index
from app.store.db import connect, replace_document
from tests.unit.helpers import statute_fixture_chunks
from tests.unit.test_store_idempotency import _doc


class HashEmbedder:
    def __init__(self):
        self.seen: list[str] = []

    def encode(self, texts, show_progress=False):
        self.seen += list(texts)
        out = []
        for t in texts:
            v = np.frombuffer(hashlib.sha512(t.encode()).digest() * 32, dtype=np.uint8)[:1024].astype(np.float32) - 127.5
            out.append(v / np.linalg.norm(v))
        return np.vstack(out).astype(np.float32)


def _settings(tmp_path):
    return SimpleNamespace(index_dir=tmp_path, faiss_path=tmp_path / "faiss.index",
                           index_manifest_path=tmp_path / "index_manifest.json", embed_model="BAAI/bge-m3")


def test_reused_rowid_with_new_text_is_re_embedded(tmp_path):
    chunks = statute_fixture_chunks("registration_1908_ss1-8", "registration-1908")
    s, emb = _settings(tmp_path), HashEmbedder()
    conn = connect(tmp_path / "t.sqlite")
    with conn:
        replace_document(conn, _doc(chunks[0]), chunks, "2026-09-24")
    sync_index(s, conn, emb)
    assert len(emb.seen) == len(chunks)

    # the document changes: every row is deleted and re-inserted, so the same rowids come back with one new text
    changed = dataclasses.replace(chunks[-1], text=chunks[-1].text + " (amended)",
                                  embed_text=chunks[-1].embed_text + " (amended)", chunk_id=chunks[-1].chunk_id + "x")
    with conn:
        removed, _, _ = replace_document(conn, _doc(chunks[0]), chunks[:-1] + [changed], "2026-09-24")
    rowid = conn.execute("SELECT rowid FROM chunks WHERE chunk_id = ?", (changed.chunk_id,)).fetchone()[0]
    assert rowid in removed  # the id really was reused

    emb.seen.clear()
    info = sync_index(s, conn, emb)
    assert emb.seen == [changed.embed_text] and info["added"] == 1
    stored = load_index(s.faiss_path).reconstruct(int(rowid))
    assert np.allclose(stored, HashEmbedder().encode([changed.embed_text])[0])


def test_unchanged_corpus_embeds_nothing(tmp_path):
    chunks = statute_fixture_chunks("registration_1908_ss1-8", "registration-1908")
    s, emb = _settings(tmp_path), HashEmbedder()
    conn = connect(tmp_path / "t.sqlite")
    with conn:
        replace_document(conn, _doc(chunks[0]), chunks, "2026-09-24")
    sync_index(s, conn, emb)
    emb.seen.clear()
    info = sync_index(s, conn, emb)
    assert emb.seen == [] and info["added"] == info["removed"] == 0
