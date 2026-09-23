"""Exact statute lookup: "section 23 of the Registration Act", "s. 54 TPA", "Order 39 Rule 1 CPC", "धारा 23".

A section reference resolves only against the Act the query literally names (never a successor: section numbers
differ between codes). Hits are placed at rank 1. A reference to an Act whose text is not ingested is reported so
the answer can say so.
"""

from __future__ import annotations

import re
import sqlite3

import numpy as np
import regex

from app.rag.classify import Classification
from app.retrieval.registry import Registry

CASE_IN_QUERY = regex.compile(
    r"(?P<a>[A-Z][\w.&'’-]*(?:\s+(?:of|and|&|the|[A-Z][\w.&'’-]*)){0,6})\s+(?:v\.|vs\.?|versus)\s+"
    r"(?P<b>[A-Z][\w.&'’-]*(?:\s+(?:of|and|&|the|[A-Z][\w.&'’-]*)){0,6})")
PARTY_STOP = {"the", "state", "union", "of", "and", "ors", "anr", "others", "another", "india", "m/s", "smt", "shri",
              "limited", "ltd", "pvt", "private", "company", "through", "dead", "since", "deceased", "lrs"}
CASE_PASSAGES = 3


def _party_words(party: str) -> list[str]:
    return [w for w in re.findall(r"[a-z]{3,}", party.lower()) if w not in PARTY_STOP][:2]


def _rank_by_similarity(query: str, rowids: list[int], dense, k: int) -> list[int]:
    if not rowids:
        return []
    q = dense.embedder.encode([query])[0]
    vecs = np.vstack([dense.index.reconstruct(int(r)) for r in rowids])
    return [rowids[i] for i in np.argsort(-(vecs @ q))[:k]]


def act_scoped(conn: sqlite3.Connection, query: str, act_titles: list[str], dense, k: int) -> list[int]:
    """The named Acts' own (central) sections ranked by dense similarity to the query."""
    if not act_titles:
        return []
    marks = ",".join("?" for _ in act_titles)
    rowids = [r[0] for r in conn.execute(
        f"SELECT rowid FROM chunks WHERE doc_type = 'statute' AND jurisdiction = 'IN' AND act_title IN ({marks})",
        act_titles)]
    return _rank_by_similarity(query, rowids, dense, k)


def case_lookup(conn: sqlite3.Connection, query: str, dense) -> list[int]:
    """Judgments named in the query ("X v. Y"): matched on significant words of both parties against the stored case
    titles (which come from the dataset record); the named judgment's passages closest to the query are pinned."""
    out: list[int] = []
    for m in CASE_IN_QUERY.finditer(query):
        a, b = _party_words(m.group("a")), _party_words(m.group("b"))
        if not a or not b:
            continue
        words = a[:1] + b[:1]
        sql = "SELECT doc_id FROM documents WHERE doc_type = 'judgment' AND " + " AND ".join("lower(title) LIKE ?" for _ in words)
        docs = [r[0] for r in conn.execute(sql + " LIMIT 3", [f"%{w}%" for w in words])]
        for doc_id in docs:
            rows = [r[0] for r in conn.execute("SELECT rowid FROM chunks WHERE doc_id = ? AND locator != 'header'", (doc_id,))]
            if not rows:
                continue
            best = _rank_by_similarity(query, rows, dense, CASE_PASSAGES)
            header = conn.execute("SELECT rowid FROM chunks WHERE doc_id = ? AND locator = 'header'", (doc_id,)).fetchone()
            out += ([header[0]] if header else []) + best
    return list(dict.fromkeys(out))


def exact_lookup(conn: sqlite3.Connection, cls: Classification, registry: Registry) -> tuple[list[int], list[str]]:
    rowids: list[int] = []
    notes: list[str] = []
    for ref in cls.section_refs:
        act_id = ref["act"]
        if act_id is None:
            # a bare "section 23" with exactly one Act named elsewhere in the query
            if len(cls.acts) == 1:
                act_id = cls.acts[0]
            else:
                continue
        act = registry.get(act_id)
        if act is None:
            continue
        rows = conn.execute(
            "SELECT rowid FROM chunks WHERE act_title = ? AND section = ? AND jurisdiction = 'IN' ORDER BY rowid",
            (act["short_title"], ref["section"])).fetchall()
        if rows:
            rowids += [r[0] for r in rows]
        else:
            ingested = conn.execute("SELECT 1 FROM chunks WHERE act_title = ? LIMIT 1", (act["short_title"],)).fetchone()
            if not ingested:
                succ = registry.short_title(act["successor"]) if act.get("successor") else None
                notes.append(f"The text of the {act['short_title']} is not in the corpus"
                             + (f"; it was replaced by the {succ}, whose section numbers differ." if succ else "."))
            else:
                notes.append(f"No s. {ref['section']} found in the {act['short_title']} as ingested.")
    return list(dict.fromkeys(rowids)), notes
