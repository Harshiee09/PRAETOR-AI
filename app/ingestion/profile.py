"""`praetor profile`: data profile of the chunk store -> docs/reports/corpus_profile.md (spec: chunk-schema note).

Completeness grades per required field: >99% green, 95-99% yellow, 80-95% orange, <80% red. The Phase 1 gate is
every required field green.
"""

from __future__ import annotations

import json
import sqlite3

import pandas as pd

from app.chunking.schema import COMMON_REQUIRED, TYPE_REQUIRED
from app.ingestion.manifest import utc_now

CATEGORICAL = ["doc_type", "title", "source_name", "licence", "authority", "jurisdiction", "language", "script",
               "status", "text_source", "act_title", "part", "chapter", "court", "disposal_nature"]


def _grade(pct: float) -> str:
    return "green" if pct > 99 else "yellow" if pct >= 95 else "orange" if pct >= 80 else "red"


def _empty(v) -> bool:
    if v is None:
        return True
    if isinstance(v, float) and pd.isna(v):
        return True
    if isinstance(v, str):
        return not v.strip() or v.strip() in ("[]", "{}", "null")
    return False


def profile(conn: sqlite3.Connection) -> tuple[str, bool]:
    df = pd.read_sql_query("SELECT * FROM chunks", conn)
    docs = pd.read_sql_query("SELECT doc_id, doc_type, title, extra FROM documents", conn)
    n = len(df)
    lines = ["# Corpus profile", "", f"_Generated {utc_now()} by `praetor profile` from `data/processed/praetor.sqlite`._", "",
             f"**Documents:** {len(docs)} · **Chunks:** {n}", ""]

    lines += ["## Chunks by type, language and domain tag", "", "| doc_type | language | domain tag | chunks |", "|---|---|---|---|"]
    tagged = df.assign(tag=df["domain_tags"].map(lambda s: json.loads(s) if s else [])).explode("tag")
    for (t, lang, tag), k in tagged.groupby(["doc_type", "language", "tag"], dropna=False).size().items():
        lines.append(f"| {t} | {lang} | {tag} | {k} |")

    all_green = True
    lines += ["", "## Required-field completeness", "", "| doc_type | field | filled | grade |", "|---|---|---|---|"]
    for t, required in TYPE_REQUIRED.items():
        sub = df[df["doc_type"] == t]
        if sub.empty:
            continue
        for f in COMMON_REQUIRED + required:
            pct = 100.0 * (1 - sub[f].map(_empty).mean())
            g = _grade(pct)
            all_green &= g == "green"
            lines.append(f"| {t} | `{f}` | {pct:.1f}% | {g} |")

    lines += ["", "## Optional fields (filled share)", "", "| doc_type | field | filled |", "|---|---|---|"]
    optional = {"statute": ["act_number", "part", "chapter", "amendment_notes", "page_start"],
                "judgment": ["judges", "citation", "para_start", "disposal_nature", "cnr", "page_start"]}
    for t, fields in optional.items():
        sub = df[df["doc_type"] == t]
        for f in fields:
            if not sub.empty:
                lines.append(f"| {t} | `{f}` | {100.0 * (1 - sub[f].map(_empty).mean()):.1f}% |")

    tok = df["token_count"]
    dup_hash = int(df.duplicated(["doc_id", "text_sha1"]).sum())
    dup_text = int(df.duplicated(["text_sha1"]).sum())
    lines += ["", "## Tokens, duplicates, OCR, status", "",
              f"- `token_count` (bge-m3 tokenizer): p5 {tok.quantile(.05):.0f}, p50 {tok.quantile(.5):.0f}, "
              f"p95 {tok.quantile(.95):.0f}, max {tok.max():.0f}; over MAX_CHUNK_TOKENS=450: {(tok > 450).sum()}",
              f"- duplicate `(doc_id, sha1(text))`: {dup_hash} · identical text across documents: {dup_text}",
              f"- text_source: " + ", ".join(f"{k} {v}" for k, v in df["text_source"].value_counts().items()),
              f"- OCR share: {(df['text_source'] == 'ocr').mean():.1%}; mean OCR confidence: "
              f"{df['ocr_confidence'].mean() if df['ocr_confidence'].notna().any() else 'n/a'}",
              f"- status: " + ", ".join(f"{k} {v}" for k, v in df["status"].value_counts().items())]
    j = df[df["doc_type"] == "judgment"]
    if not j.empty:
        dates = pd.to_datetime(j["decision_date"], errors="coerce")
        lines.append(f"- `decision_date`: oldest {dates.min().date()}, newest {dates.max().date()}, unparseable {int(dates.isna().sum())}")
        loc = j["locator"]
        by_page = int(loc.str.match(r"^pp?\. ").sum())
        lines.append(f"- judgment locators: header {int((loc == 'header').sum())}, by paragraph "
                     f"{int(loc.str.startswith('para').sum())}, by page {by_page}")

    lines += ["", "## Categorical values (top 10 / bottom 5)", ""]
    for col in CATEGORICAL:
        vc = df[col].fillna("(null)").value_counts()
        top = "; ".join(f"{str(k)[:50]} ({v})" for k, v in vc.head(10).items())
        bottom = "; ".join(f"{str(k)[:50]} ({v})" for k, v in vc.tail(5).items()) if len(vc) > 10 else "—"
        lines.append(f"- **{col}** ({len(vc)} values): top: {top} · bottom: {bottom}")

    lines += ["", "## Per-document parse checks", "", "| type | title | checks |", "|---|---|---|"]
    for _, d in docs.sort_values(["doc_type", "title"]).iterrows():
        e = json.loads(d["extra"] or "{}")
        if d["doc_type"] == "statute":
            chk = (f"sections {e.get('sections_found')}/{e.get('toc_sections')} (missing {e.get('sections_missing')}), "
                   f"state blocks {e.get('state_blocks')}, footnotes {e.get('footnotes')}, unusable pages {e.get('unusable_pages')}")
        else:
            chk = (f"pages {e.get('pages')}, units {e.get('paragraphs')} ({e.get('numbered_paragraphs')} numbered), "
                   f"opinions {e.get('opinions')}, unusable pages {e.get('unusable_pages')}")
        lines.append(f"| {d['doc_type']} | {d['title'][:60]} | {chk} |")

    lines += ["", f"## Gate", "", f"Every required field green: **{'PASS' if all_green else 'FAIL'}**"]
    return "\n".join(lines) + "\n", all_green
