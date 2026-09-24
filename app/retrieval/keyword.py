"""FTS5 keyword search ranked by bm25() (retrieval-pipeline note, step 5).

Raw user text breaks FTS5 syntax (quotes, hyphens, NOT, parentheses), so the query is split into word tokens,
stop-words are dropped, each token is quoted, and the tokens are OR-ed. Filters are applied in SQL.
"""

from __future__ import annotations

import sqlite3
import time

import regex

TOKEN = regex.compile(r"[\p{L}\p{M}\p{N}]+")
STOPWORDS = set("""a an the and or of to in on for by with from at as is are was were be been being it its this that
these those what which who whom whose when where why how do does did can could should would may might must shall will
i me my we our you your he she they them their his her not no any all there here into under about if then than so such
also only other over upon within without per between after before""".split()) | {"क्या", "है", "के", "की", "का",
"में", "से", "को", "और", "या", "कि", "होता", "होती", "करना", "लिए", "कैसे", "एक"}


def fts_query(text: str, extra_phrases: list[str] | None = None) -> str | None:
    """Sanitised FTS5 MATCH expression: quoted tokens OR-ed together, plus optional quoted phrases."""
    terms = []
    for tok in TOKEN.findall(text.lower()):
        if tok in STOPWORDS or (len(tok) < 2 and not tok.isdigit()):
            continue
        terms.append(f'"{tok}"')
    for p in extra_phrases or []:
        # A phrase keeps its stop-words: FTS5 phrases match adjacent tokens and the index keeps every token, so
        # "transfer property act" can never match "Transfer of Property Act" (found 2026-09-24: 0 hits vs 260).
        words = TOKEN.findall(p.lower())
        if words:
            terms.append('"' + " ".join(words) + '"')
    terms = list(dict.fromkeys(terms))
    return " OR ".join(terms) if terms else None


class KeywordRetriever:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def search(self, text: str, k: int, extra_phrases: list[str] | None = None,
               where: str = "", params: tuple = ()) -> tuple[list[tuple[int, float]], dict]:
        t0 = time.perf_counter()
        match = fts_query(text, extra_phrases)
        if not match:
            return [], {"keyword_ms": 0, "match": None}
        sql = ("SELECT c.rowid, bm25(chunks_fts) AS s FROM chunks_fts JOIN chunks c ON c.rowid = chunks_fts.rowid "
               f"WHERE chunks_fts MATCH ? {('AND ' + where) if where else ''} ORDER BY s LIMIT ?")
        rows = self.conn.execute(sql, (match, *params, k)).fetchall()
        # bm25() is lower-is-better; negate so higher is better like the other retrievers
        return [(r[0], -float(r[1])) for r in rows], {"keyword_ms": round((time.perf_counter() - t0) * 1000), "match": match}
