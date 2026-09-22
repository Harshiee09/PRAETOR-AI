"""Replacing a document with the same chunks keeps the row count constant; duplicates keep one row."""

from app.chunking.schema import Document
from app.store.db import connect, replace_document
from tests.unit.helpers import statute_fixture_chunks


def _doc(c) -> Document:
    return Document(doc_id=c.doc_id, doc_type="statute", title=c.title, source_name=c.source_name,
                    source_url=c.source_url, licence=c.licence, retrieved_at=c.retrieved_at, raw_path="fixture",
                    raw_sha256="0" * 64, authority=c.authority, jurisdiction="IN", language="en", script="Latn",
                    parser_version="test")


def test_replace_twice_adds_no_rows(tmp_path):
    chunks = statute_fixture_chunks("registration_1908_ss1-8", "registration-1908")
    conn = connect(tmp_path / "t.sqlite")
    with conn:
        _, added1, _ = replace_document(conn, _doc(chunks[0]), chunks, "2026-09-23")
    n1 = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
    with conn:
        removed, added2, _ = replace_document(conn, _doc(chunks[0]), chunks, "2026-09-23")
    n2 = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
    assert added1 == n1 == n2 == len(chunks) and len(removed) == n1


def test_duplicate_text_keeps_one_row(tmp_path):
    chunks = statute_fixture_chunks("registration_1908_ss1-8", "registration-1908")
    conn = connect(tmp_path / "t.sqlite")
    with conn:
        _, added, dups = replace_document(conn, _doc(chunks[0]), chunks + [chunks[0]], "2026-09-23")
    assert added == len(chunks) and dups == 1


def test_fts_is_populated_and_searchable(tmp_path):
    chunks = statute_fixture_chunks("registration_1908_ss1-8", "registration-1908")
    conn = connect(tmp_path / "t.sqlite")
    with conn:
        replace_document(conn, _doc(chunks[0]), chunks, "2026-09-23")
    hits = conn.execute("SELECT c.locator FROM chunks_fts f JOIN chunks c ON c.rowid = f.rowid "
                        "WHERE chunks_fts MATCH '\"Inspector\" AND \"Registration\"'").fetchall()
    assert any(h[0] == "s. 3" for h in hits)
