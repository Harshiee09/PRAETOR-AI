"""`praetor index`: manifest -> parse -> legal-aware chunks -> validate -> SQLite + FTS5 -> embed -> FAISS.

Incremental: a document is re-processed only when its raw file's sha256 or the parser/chunker version changed, so
re-running over unchanged sources adds zero rows and embeds nothing. Documents whose raw file is no longer an
input are removed along with their chunks and vectors.
"""

from __future__ import annotations

import json
import logging
import uuid
from functools import partial

import yaml

from app.chunking.assemble import judgment_chunks, statute_chunks
from app.chunking.judgment import clean_case_title, split_judgment
from app.chunking.schema import Chunk, Document, doc_id_for, validate_chunk
from app.chunking.statute import split_statute
from app.config import Settings
from app.embeddings.embedder import count_tokens
from app.embeddings.index import sync_index
from app.ingestion.manifest import Manifest, ManifestRow, utc_now
from app.ingestion.sources import load_sources, load_statutes
from app.parsing.pdf import PARSER_VERSION, parse_pdf
from app.store.db import connect, get_document, replace_document

log = logging.getLogger(__name__)
STATUTE_VERSION = f"{PARSER_VERSION}+statute-2"
JUDGMENT_VERSION = f"{PARSER_VERSION}+judgment-3"
SC_HTTPS = "https://{bucket}.s3.{region}.amazonaws.com/{key}"


def _inputs(settings: Settings) -> list[tuple[str, ManifestRow]]:
    manifest = Manifest(settings.manifest_path, settings.data_dir)
    out = []
    for row in manifest.rows():
        extra = row.extra or {}
        if row.source == "indiacode" and row.local_path.lower().endswith(".pdf"):
            out.append(("statute", row))
        elif row.source == "sc-judgments" and extra.get("kind") == "judgment_pdf":
            if (settings.data_dir / row.local_path).with_suffix(".json").exists():
                out.append(("judgment", row))
    return out


def _statute_doc(settings, row: ManifestRow, act: dict, reg: dict) -> tuple[Document, list[Chunk]]:
    lang = row.extra["language"]
    canonical = f"{row.source_page}#{lang}"
    path = settings.data_dir / row.local_path
    parsed = parse_pdf(path, expected_script="Latn" if lang == "en" else "Deva")
    jur = yaml.safe_load((settings.registry_dir / "jurisdictions.yaml").read_text(encoding="utf-8"))
    sp = split_statute(parsed, set(jur["codes"]) | set(jur["aliases"]))
    doc = Document(
        doc_id=doc_id_for(canonical), doc_type="statute", title=act["short_title"], source_name=reg["name"],
        source_url=row.source_page, licence=row.licence, retrieved_at=row.retrieved_at, raw_path=row.local_path,
        raw_sha256=row.sha256, authority=reg["authority"], jurisdiction=reg["jurisdiction"], language=lang,
        script="Latn" if lang == "en" else "Deva", parser_version=STATUTE_VERSION,
        extra={"pages": len(parsed.pages), "unusable_pages": [p.number for p in parsed.unusable_pages],
               "toc_sections": len(sp.toc), "sections_found": sum(1 for s in sp.sections if s.kind == "section"),
               "sections_missing": sp.missing, "state_blocks": sum(len(s.state_blocks) for s in sp.sections),
               "footnotes": sum(len(v) for v in sp.footnotes.values()),
               "watermark_chars_removed": sum(p.watermark_chars for p in parsed.pages)},
    )
    src_act = next(a for a in reg["acts"] if a["id"] == row.extra["act"])
    count = partial(count_tokens, model_name=settings.embed_model)
    chunks = statute_chunks(doc, sp, act, jur, src_act["domain_tags"], count, settings.max_chunk_tokens)
    return doc, chunks


def _judgment_doc(settings, row: ManifestRow, reg: dict, act_tags: dict[str, list[str]]) -> tuple[Document, list[Chunk]]:
    path = settings.data_dir / row.local_path
    meta = json.loads(path.with_suffix(".json").read_text(encoding="utf-8"))
    meta["case_title"] = clean_case_title(meta)
    key = row.url.split("/", 3)[3]
    parsed = parse_pdf(path, "Latn", drop_margin_letters=True, strip_running_headers=True, drop_small_text=True)
    jp = split_judgment(parsed)
    doc = Document(
        doc_id=doc_id_for(row.url), doc_type="judgment", title=meta["case_title"], source_name=reg["name"],
        source_url=SC_HTTPS.format(bucket=reg["bucket"], region=reg["region"], key=key), licence=row.licence,
        retrieved_at=row.retrieved_at, raw_path=row.local_path, raw_sha256=row.sha256, authority=reg["authority"],
        jurisdiction=reg["jurisdiction"], language="en", script="Latn", parser_version=JUDGMENT_VERSION,
        extra={"pages": len(parsed.pages), "unusable_pages": [p.number for p in parsed.unusable_pages],
               "paragraphs": len(jp.paras), "numbered_paragraphs": sum(1 for p in jp.paras if p.number is not None),
               "opinions": jp.opinions, "body_start_page": jp.body_start_page,
               "margin_letters_removed": sum(p.margin_chars for p in parsed.pages)},
    )
    tags = sorted({t for a in meta.get("matched_acts", []) for t in act_tags.get(a, [])} | {"case_law"})
    count = partial(count_tokens, model_name=settings.embed_model)
    return doc, judgment_chunks(doc, jp, meta, tags, count, settings.max_chunk_tokens)


def _process(settings: Settings, kind: str, row: ManifestRow, sources: dict, statutes: dict, act_tags: dict):
    """Parse and chunk one document (runs in a worker process). Returns (doc, chunks)."""
    if kind == "statute":
        act = statutes.get(row.extra["act"])
        if act is None:
            raise ValueError(f"act {row.extra['act']!r} has no entry in statutes.yaml (status unknown)")
        return _statute_doc(settings, row, act, sources["indiacode"])
    return _judgment_doc(settings, row, sources["sc-judgments"], act_tags)


def build(settings: Settings, embed: bool = True, force: bool = False, workers: int = 4) -> dict:
    run_id = uuid.uuid4().hex[:12]
    started = utc_now()
    conn = connect(settings.sqlite_path)
    sources = load_sources(settings.registry_dir)
    statutes = {s["id"]: s for s in load_statutes(settings.registry_dir)}
    act_tags = {a["id"]: a["domain_tags"] for a in sources["indiacode"]["acts"]}
    stats = dict(docs_seen=0, docs_changed=0, docs_skipped=0, docs_failed=0, docs_removed=0, chunks_added=0,
                 chunks_removed=0, chunks_rejected=0, duplicates_dropped=0)
    failures, reject_reasons = [], {}
    input_doc_ids = set()

    todo = []
    for kind, row in _inputs(settings):
        stats["docs_seen"] += 1
        version = STATUTE_VERSION if kind == "statute" else JUDGMENT_VERSION
        canonical = f"{row.source_page}#{row.extra['language']}" if kind == "statute" else row.url
        doc_id = doc_id_for(canonical)
        input_doc_ids.add(doc_id)
        existing = get_document(conn, doc_id)
        if not force and existing and existing["raw_sha256"] == row.sha256 and existing["parser_version"] == version:
            stats["docs_skipped"] += 1
            continue
        todo.append((kind, row))

    # Parsing is CPU-bound and per-document, so it runs in worker processes; this process stays the only writer.
    from concurrent.futures import ProcessPoolExecutor, as_completed

    results = []
    if todo:
        with ProcessPoolExecutor(max_workers=max(1, min(workers, len(todo)))) as ex:
            futures = {ex.submit(_process, settings, kind, row, sources, statutes, act_tags): row for kind, row in todo}
            for i, fut in enumerate(as_completed(futures), 1):
                row = futures[fut]
                try:
                    results.append(fut.result())
                except Exception as exc:  # noqa: BLE001 — one bad document must not stop the run; it is reported
                    stats["docs_failed"] += 1
                    failures.append({"file": row.local_path, "error": str(exc)})
                    log.error("document failed", extra={"file": row.local_path, "error": str(exc)})
                if i % 50 == 0:
                    log.warning("parse progress", extra={"done": i, "of": len(todo)})

    for doc, chunks in results:
        good = []
        for c in chunks:
            problems = validate_chunk(c)
            if problems:
                stats["chunks_rejected"] += 1
                conn.execute("INSERT INTO rejects (run_id, doc_id, locator, problems) VALUES (?,?,?,?)",
                             (run_id, c.doc_id, c.locator, json.dumps(problems)))
                for p in problems:
                    key = p.split(":")[0]
                    reject_reasons[key] = reject_reasons.get(key, 0) + 1
            else:
                good.append(c)
        with conn:
            removed, added, dups = replace_document(conn, doc, good, utc_now())
            # (doc_id, sha1(text)) keeps one row; record which locator lost its row so the drop is auditable
            for loc, kept in dups:
                conn.execute("INSERT INTO rejects (run_id, doc_id, locator, problems) VALUES (?,?,?,?)",
                             (run_id, doc.doc_id, loc, json.dumps([f"duplicate text of {kept}"])))
        stats["docs_changed"] += 1
        stats["chunks_added"] += added
        stats["chunks_removed"] += len(removed)
        stats["duplicates_dropped"] += len(dups)

    stale_docs = [r[0] for r in conn.execute("SELECT doc_id FROM documents")]
    with conn:
        for doc_id in stale_docs:
            if doc_id not in input_doc_ids:
                n = conn.execute("DELETE FROM chunks WHERE doc_id = ?", (doc_id,)).rowcount
                conn.execute("DELETE FROM documents WHERE doc_id = ?", (doc_id,))
                stats["docs_removed"] += 1
                stats["chunks_removed"] += n

    index_info = sync_index(settings, conn) if embed else None
    with conn:
        conn.execute(
            """INSERT INTO ingest_runs (run_id, started_at, finished_at, docs_seen, docs_changed, docs_skipped,
               chunks_added, chunks_removed, chunks_rejected, duplicates_dropped, notes) VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (run_id, started, utc_now(), stats["docs_seen"], stats["docs_changed"], stats["docs_skipped"],
             stats["chunks_added"], stats["chunks_removed"], stats["chunks_rejected"], stats["duplicates_dropped"],
             json.dumps({"failures": failures, "reject_reasons": reject_reasons})),
        )
    total = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
    conn.close()
    return {"run_id": run_id, **stats, "chunks_total": total, "reject_reasons": reject_reasons,
            "failures": failures, "index": index_info}

