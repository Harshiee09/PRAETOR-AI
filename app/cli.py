"""`praetor` command-line entry point. Every real workflow starts here (see the command table in CLAUDE.md)."""

from __future__ import annotations

import argparse
import os
import sys

# Windows without Developer Mode can't symlink in the HF cache; that works (with more disk), so skip the warning.
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

from app.config import REPO_ROOT, get_settings
from app.config.logs import setup_logging


def _cmd_gpu_check(args: argparse.Namespace) -> int:
    from app.embeddings.gpu_check import run

    return run(get_settings())


def _parse_years(spec: str) -> list[int]:
    if "-" in spec:
        a, b = (int(x) for x in spec.split("-"))
        return list(range(a, b + 1))
    return [int(x) for x in spec.split(",")]


def _cmd_ingest(args: argparse.Namespace) -> int:
    from app.ingestion.http import BlockedError

    settings = get_settings()
    reports = REPO_ROOT / "docs" / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    try:
        if args.source == "indiacode":
            from app.ingestion import indiacode

            rows = indiacode.ingest(settings, act_ids=args.act or None, phase=args.phase, languages=tuple(args.lang))
            for r in rows:
                print(f"{r.extra['act']:<20} {r.extra['language']}  {r.bytes:>9,} B  sha256 {r.sha256[:12]}  {r.local_path}")
        elif args.source == "sc-judgments":
            import math

            from app.ingestion import sc_judgments as sc

            years = _parse_years(args.years)
            sc.fetch_metadata(settings, years)
            df = sc.load_metadata(settings, years)
            (reports / "sc_metadata_profile.md").write_text(sc.profile_markdown(df, years), encoding="utf-8")
            print(f"metadata: {len(df)} rows for {years[0]}-{years[-1]}; profile -> docs/reports/sc_metadata_profile.md")
            selected = sc.select(df, limit=args.limit, min_year=years[0])
            if args.dry_run:
                print(f"would select {len(selected)}: {selected['matched_act'].value_counts().to_dict()}; "
                      f"by year {selected['year'].value_counts().sort_index().to_dict()}")
                return 0
            fetch = sc.download_selected_via_tar if args.via == "tar" else sc.download_selected
            rows = fetch(settings, selected)
            lines = ["# SC judgments selected for the corpus", "",
                     f"_Rule: newest first, English available, decided {years[0]} or later, headnote names a corpus Act "
                     f"with its year; up to {math.ceil(args.limit / len(sc.ACT_PATTERNS))} per Act, leftover slots to the "
                     f"newest remaining hits. `matched Act` is the Act whose quota the judgment filled._", "",
                     "| matched Act | decided | neutral citation | SCR citation | title |", "|---|---|---|---|---|"]
            lines += [f"| {r['matched_act']} | {r['_date']} | {r['case_id']} | {r['citation']} | {r['title'].strip()} |"
                      for r in selected.to_dict("records")]
            (reports / "sc_selection.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
            print(f"selected {len(selected)} judgments ({selected['matched_act'].value_counts().to_dict()}); "
                  f"{len(rows)} PDFs present; list -> docs/reports/sc_selection.md")
    except BlockedError as exc:
        print(f"BLOCKED: {exc}\nNot working around it. Download the file manually and tell me where it is.")
        return 2
    return 0


def _cmd_index(args: argparse.Namespace) -> int:
    from app.ingestion.build import build

    r = build(get_settings(), embed=not args.no_embed, force=args.force, workers=args.workers)
    print(f"run {r['run_id']}: docs seen {r['docs_seen']}, changed {r['docs_changed']}, skipped {r['docs_skipped']}, "
          f"failed {r['docs_failed']}, removed {r['docs_removed']}")
    print(f"chunks: added {r['chunks_added']}, removed {r['chunks_removed']}, rejected {r['chunks_rejected']}, "
          f"duplicates dropped {r['duplicates_dropped']}, total {r['chunks_total']}")
    if r["reject_reasons"]:
        print("reject reasons: " + ", ".join(f"{k} ({v})" for k, v in sorted(r["reject_reasons"].items())))
    for f in r["failures"]:
        print(f"FAILED {f['file']}: {f['error']}")
    if r["index"]:
        i = r["index"]
        print(f"faiss: {i['faiss_ntotal']} vectors (added {i['added']}, removed {i['removed']}, "
              f"embedded in {i['embed_seconds']}s), corpus hash {i['corpus_hash'][:12]}")
    return 1 if r["docs_failed"] else 0


def _cmd_profile(args: argparse.Namespace) -> int:
    from app.ingestion.profile import profile
    from app.store.db import connect

    settings = get_settings()
    conn = connect(settings.sqlite_path)
    report, all_green = profile(conn)
    conn.close()
    out = REPO_ROOT / "docs" / "reports" / "corpus_profile.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report, encoding="utf-8")
    print(f"corpus profile -> {out.relative_to(REPO_ROOT)}; every required field green: {'PASS' if all_green else 'FAIL'}")
    return 0 if all_green else 1


def _cmd_eval(args: argparse.Namespace) -> int:
    from app.rag.evaluate import run

    payload, path = run(get_settings(), split=args.split, modes=args.modes.split(",") if args.modes else None,
                        with_answers=not args.no_llm, model=args.model, calibrate_gate=args.calibrate)
    print(f"report -> {path.relative_to(REPO_ROOT)}")
    for t in payload["retrieval"]:
        print(f"  {t['mode']:<14} n={t['n']:<3} R@5 {t['recall@5']:.2f}  R@10 {t['recall@10']:.2f}  MRR {t['mrr']:.2f}  "
              f"statute R@5 {t['statute_recall@5']:.2f} (n={t['statute_n']})")
    print(f"  abstention: {payload['abstention']}")
    if "answers" in payload:
        for k, v in payload["answers"].items():
            print(f"  {k}: {v}")
    return 0


def _cmd_ask(args: argparse.Namespace) -> int:
    import json

    from app.rag.pipeline import Engine, answer

    settings = get_settings()
    out = answer(Engine.load(settings), args.question, explain=args.explain, mode=args.mode)
    if args.json:
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0
    print(out["answer_markdown"])
    if out["citations"]:
        print("\nSources")
        for c in out["citations"]:
            extra = f", {c['citation']}" if c.get("citation") else ""
            print(f"  [{c['id']}] {c['title']}, {c['locator']}{extra} | {c['status'].replace('_', ' ')} | "
                  f"{c['authority']} ({c['jurisdiction']}) | retrieved {c['retrieved_at']}\n       {c['source_url']}")
    for w in out["warnings"]:
        print(f"! {w}")
    print(f"\nConfidence: {out['confidence']} · {out['disclaimer']}")
    if args.explain:
        e = out["explain"]
        c0 = e["classification"]
        print(f"\n--- explain (trace {out['trace_id']}, mode {args.mode}) ---")
        print(f"classified: domain {c0['domain']}, intent {c0['intent']}, high_stakes {c0['high_stakes']}, "
              f"acts {c0['acts']}, section refs {c0['section_refs']}, dates {c0['event_dates']}")
        print(f"gate: {e['gate']} · timings {e['timings_ms']}")
        print(f"keyword query: {e['keyword_match']}")
        print("  ctx  exact dense  kw  fused rerank(score)  source")
        for c in e["candidates"]:
            used = next((sid for sid, cid in e.get("context_ids", {}).items() if cid == c["chunk_id"]), "")
            r, s = c["ranks"], c["scores"]
            rr = f"{r.get('rerank', '-')}({s['rerank']:.3f})" if "rerank" in s else "-"
            print(f"  {used:<4} {str(r.get('exact', '-')):>5} {str(r.get('dense', '-')):>5} {str(r.get('keyword', '-')):>3} "
                  f"{r.get('fused', '-'):>5} {rr:>13}  {c['title'][:42]} — {c['locator']}")
        if "llm" in e:
            attempts = [{k: v for k, v in a.items() if k != "raw"} for a in e["attempts"]]
            print(f"llm: {e['llm']} prompt {e['prompt_version']} attempts {attempts}")
            print(f"validator: {e['validator']}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="praetor", description="PRAETOR AI — informational legal RAG (not legal advice)")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("gpu-check", help="prove CUDA works and bge-m3 embeds on the GPU")
    p.set_defaults(func=_cmd_gpu_check)

    p = sub.add_parser("ingest", help="download sources into data/raw with manifest rows")
    p.add_argument("--source", required=True, choices=["indiacode", "sc-judgments"])
    p.add_argument("--act", action="append", help="indiacode: registry act id (repeatable); default = all acts up to --phase")
    p.add_argument("--phase", type=int, default=1, help="indiacode: include acts tagged with this phase or earlier")
    p.add_argument("--lang", action="append", default=None, choices=["en", "hi"], help="indiacode: PDF language(s)")
    p.add_argument("--years", default="2019-2025", help="sc-judgments: metadata years, e.g. 2019-2025")
    p.add_argument("--limit", type=int, default=50, help="sc-judgments: about how many judgments to select")
    p.add_argument("--via", choices=["pdf", "tar"], default="pdf",
                   help="sc-judgments: individual PDFs (targeted, a few hundred) or year tars (bulk, as the maintainers ask)")
    p.add_argument("--dry-run", action="store_true", help="sc-judgments: show the selection without downloading")
    p.set_defaults(func=_cmd_ingest)

    p = sub.add_parser("index", help="parse, chunk, validate, store and embed everything in the manifest (incremental)")
    p.add_argument("--no-embed", action="store_true", help="update SQLite only, skip FAISS")
    p.add_argument("--force", action="store_true", help="re-process every document even if unchanged")
    p.add_argument("--workers", type=int, default=4, help="parallel parse processes (lower it if RAM is short)")
    p.set_defaults(func=_cmd_index)

    p = sub.add_parser("profile", help="data profile of the chunk store -> docs/reports/corpus_profile.md")
    p.set_defaults(func=_cmd_profile)

    p = sub.add_parser("eval", help="retrieval ablation, abstention and answer metrics on evaluation/gold.jsonl")
    p.add_argument("--split", default="all", choices=["all", "dev", "test"])
    p.add_argument("--modes", default=None, help="comma-separated subset of dense,keyword,hybrid,hybrid_rerank,full")
    p.add_argument("--no-llm", action="store_true", help="retrieval and abstention only")
    p.add_argument("--model", default=None, help="Ollama model to answer with (default OLLAMA_MODEL)")
    p.add_argument("--calibrate", action="store_true", help="sweep the rerank evidence-gate threshold")
    p.set_defaults(func=_cmd_eval)

    p = sub.add_parser("ask", help="answer a question from the indexed sources, with citations")
    p.add_argument("question")
    p.add_argument("--explain", action="store_true", help="show per-stage ranks, scores, timings and tokens")
    p.add_argument("--json", action="store_true", help="print the full response object")
    p.add_argument("--mode", default="full", choices=["dense", "keyword", "hybrid", "hybrid_rerank", "full"],
                   help="retrieval configuration (default: full = exact + dense + keyword + RRF + rerank)")
    p.set_defaults(func=_cmd_ask)

    return parser


def main(argv: list[str] | None = None) -> int:
    # Windows consoles default to a legacy code page; Indic text needs UTF-8.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    settings = get_settings()
    setup_logging(settings.log_level)
    args = build_parser().parse_args(argv)
    if getattr(args, "lang", "unset") is None:
        args.lang = ["en"]
    return int(args.func(args) or 0)


if __name__ == "__main__":
    sys.exit(main())
