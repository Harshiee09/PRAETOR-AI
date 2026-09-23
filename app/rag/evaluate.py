"""`praetor eval` (spec: docs/topics/ops/evaluation.md).

- Retrieval ablation over the same questions: dense, keyword, hybrid, hybrid+rerank, full (+ exact lookup):
  Recall@5, Recall@10 and MRR against each question's expected sources. No LLM needed.
- Abstention precision/recall against `should_abstain`, from the evidence gate (no LLM needed), and a threshold
  sweep on the dev split (`--calibrate`).
- Answer metrics for the full pipeline with a model: invalid citations after validation (must be 0), share of
  answers with a citation, unverified-authority removals, unsupported-sentence flags, must_mention hits, expected
  source cited, regime note on criminal-transition questions, latency and tokens.
Every percentage is reported with its n; slices by query language.
"""

from __future__ import annotations

import json
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path

from app.config import REPO_ROOT, Settings
from app.rag.pipeline import Engine, answer
from app.retrieval.hybrid import MODES
from app.store.db import connect

GOLD = REPO_ROOT / "evaluation" / "gold.jsonl"
MARKER_RE = r"\[S(\d{1,3})\]"


def load_gold(split: str = "all", path: Path = GOLD) -> list[dict]:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return [r for r in rows if split == "all" or r.get("split") == split]


def is_hit(chunk: dict, src: dict) -> bool:
    if "act" in src:
        return chunk.get("act_title") == src["act"] and str(chunk.get("section")) == str(src["section"])
    if "neutral_citation" in src:
        return src["neutral_citation"] in (chunk.get("citation") or "")
    return False


def retrieval_metrics(ranked: list[dict], expected: list[dict], match: str = "all") -> dict:
    """Recall@k: share of expected sources found in the top k (match="any": 1 if any alternative is found);
    MRR: 1/rank of the first relevant candidate."""
    ranks = []
    for src in expected:
        r = next((i for i, c in enumerate(ranked, 1) if is_hit(c, src)), None)
        ranks.append(r)
    found = [r for r in ranks if r is not None]
    if match == "any":
        best = min(found) if found else None
        r5, r10 = float(bool(best and best <= 5)), float(bool(best and best <= 10))
    else:
        r5 = sum(1 for r in ranks if r and r <= 5) / len(expected)
        r10 = sum(1 for r in ranks if r and r <= 10) / len(expected)
    return {"recall@5": r5, "recall@10": r10, "mrr": 1 / min(found) if found else 0.0, "ranks": ranks}


def _pct(x: float, n: int) -> str:
    return f"{x:.0%} (n={n})" if n else "—"


def _mean(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


def run_retrieval(engine: Engine, gold: list[dict], modes: list[str]) -> dict:
    conn = connect(engine.settings.sqlite_path)
    out: dict = {m: [] for m in modes}
    try:
        for g in gold:
            for m in modes:
                t0 = time.perf_counter()
                r = engine.retriever.retrieve(conn, g["question"], mode=m)
                row = {"id": g["id"], "language": g["language"], "intent": g["intent"], "should_abstain": g["should_abstain"],
                       "abstained": r.abstained, "gate": r.gate, "ms": round((time.perf_counter() - t0) * 1000),
                       "timings": r.timings_ms}
                if g["expected_sources"]:
                    row.update(retrieval_metrics(r.candidates, g["expected_sources"], g.get("match", "all")))
                out[m].append(row)
    finally:
        conn.close()
    return out


def summarise_retrieval(res: dict) -> list[dict]:
    table = []
    for mode, rows in res.items():
        answerable = [r for r in rows if "recall@5" in r]
        statute = [r for r in answerable if r["intent"] == "statute_lookup"]
        table.append({"mode": mode, "n": len(answerable),
                      "recall@5": _mean([r["recall@5"] for r in answerable]),
                      "recall@10": _mean([r["recall@10"] for r in answerable]),
                      "mrr": _mean([r["mrr"] for r in answerable]),
                      "statute_n": len(statute), "statute_recall@5": _mean([r["recall@5"] for r in statute]),
                      "p50_ms": statistics.median([r["ms"] for r in rows]) if rows else 0})
    return table


def abstention(rows: list[dict]) -> dict:
    tp = sum(1 for r in rows if r["should_abstain"] and r["abstained"])
    fp = sum(1 for r in rows if not r["should_abstain"] and r["abstained"])
    fn = sum(1 for r in rows if r["should_abstain"] and not r["abstained"])
    return {"should_abstain": tp + fn, "abstained_correctly": tp, "false_abstentions": fp,
            "precision": tp / (tp + fp) if tp + fp else None, "recall": tp / (tp + fn) if tp + fn else None}


def calibrate(rows: list[dict]) -> list[dict]:
    """Sweep the rerank-gate threshold over dev-split questions (exact-lookup hits always answer)."""
    sweep = []
    scored = [r for r in rows if r["gate"].get("on") in ("rerank", "exact")]
    for t in [x / 100 for x in range(5, 80, 5)]:
        tp = fp = fn = 0
        for r in scored:
            abst = r["gate"]["on"] == "rerank" and r["gate"]["score"] < t
            tp += r["should_abstain"] and abst
            fp += (not r["should_abstain"]) and abst
            fn += r["should_abstain"] and not abst
        sweep.append({"threshold": t, "correct_abstentions": tp, "false_abstentions": fp, "missed_abstentions": fn})
    return sweep


def run_answers(engine: Engine, gold: list[dict], model: str | None) -> list[dict]:
    import re

    rows = []
    for g in gold:
        t0 = time.perf_counter()
        out = answer(engine, g["question"], explain=True, model=model)
        e = out["explain"]
        text = out["answer_markdown"]
        markers = set(re.findall(MARKER_RE, text))
        ctx = e.get("context_ids", {})
        invalid_after = [m for m in markers if f"S{m}" not in ctx]
        cited_chunks = {c["chunk_id"] for c in out["citations"]}
        row = {"id": g["id"], "language": g["language"], "intent": g["intent"], "should_abstain": g["should_abstain"],
               "abstained": out["abstained"], "provider": out.get("provider"), "confidence": out["confidence"],
               "invalid_after_validation": len(invalid_after), "n_citations": len(out["citations"]),
               "seconds": round(time.perf_counter() - t0, 1)}
        v = e.get("validator") or {}
        row.update(invalid_removed=len(v.get("invalid_ids", [])), unverified_authority=len(v.get("unverified_authority", [])),
                   unverified_quotes=len(v.get("unverified_quotes", [])), unsupported=v.get("unsupported", 0),
                   llm=e.get("llm"), attempts=e.get("attempts"))
        if g["must_mention"] and not out["abstained"]:
            low = text.lower()
            row["must_mention_hit"] = all(m.lower() in low for m in g["must_mention"])
        if g["expected_sources"] and not out["abstained"]:
            conn = connect(engine.settings.sqlite_path)
            try:
                from app.store.db import chunk_by_id

                cited = [chunk_by_id(conn, cid) for cid in cited_chunks]
            finally:
                conn.close()
            row["expected_cited"] = any(is_hit(c, s) for c in cited if c for s in g["expected_sources"])
        if g.get("domain") == "criminal_procedure" and "transition" in g.get("tags", []):
            row["regime_note"] = any("1 July 2024" in w or "2024-07-01" in w for w in out["warnings"])
        rows.append(row)
    return rows


def summarise_answers(rows: list[dict]) -> dict:
    answered = [r for r in rows if not r["abstained"]]
    mm = [r for r in answered if "must_mention_hit" in r]
    ec = [r for r in answered if "expected_cited" in r]
    rn = [r for r in rows if "regime_note" in r]
    lat = [r["seconds"] for r in answered if r["provider"] not in (None, "extractive")]
    return {"n": len(rows), "answered": len(answered),
            "invalid_citations_after_validation": sum(r["invalid_after_validation"] for r in rows),
            "with_citation": _pct(_mean([1.0 if r["n_citations"] else 0.0 for r in answered]), len(answered)),
            "unverified_authority_removals": sum(r["unverified_authority"] for r in rows),
            "invalid_ids_removed": sum(r["invalid_removed"] for r in rows),
            "unsupported_flags": sum(r["unsupported"] for r in rows),
            "extractive_fallbacks": sum(1 for r in answered if r["provider"] == "extractive"),
            "must_mention": _pct(_mean([1.0 if r["must_mention_hit"] else 0.0 for r in mm]), len(mm)),
            "expected_source_cited": _pct(_mean([1.0 if r["expected_cited"] else 0.0 for r in ec]), len(ec)),
            "regime_note": _pct(_mean([1.0 if r["regime_note"] else 0.0 for r in rn]), len(rn)),
            "latency_p50_s": statistics.median(lat) if lat else None,
            "latency_p95_s": sorted(lat)[max(0, int(0.95 * len(lat)) - 1)] if lat else None,
            "tokens_in_mean": _mean([r["llm"]["input_tokens"] for r in answered if r.get("llm")]),
            "tokens_out_mean": _mean([r["llm"]["output_tokens"] for r in answered if r.get("llm")]),
            "abstention": abstention(rows)}


def write_report(settings: Settings, payload: dict) -> Path:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = REPO_ROOT / "evaluation" / "reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{ts}.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    lines = [f"# Evaluation {ts}", "", f"Split: **{payload['split']}** · questions: {payload['n_questions']} · "
             f"model: {payload.get('model') or '—'} · MIN_EVIDENCE_SCORE {settings.min_evidence_score}", "",
             "_Small-sample caveat: with this few questions, differences of a few points between configurations are "
             "not meaningful. Gold questions are drafts until a person verifies them (`verified_by`)._", ""]
    if "retrieval" in payload:
        lines += ["## Retrieval ablation", "", "| configuration | n | Recall@5 | Recall@10 | MRR | statute Recall@5 (n) | p50 ms |",
                  "|---|---|---|---|---|---|---|"]
        for t in payload["retrieval"]:
            lines.append(f"| {t['mode']} | {t['n']} | {t['recall@5']:.2f} | {t['recall@10']:.2f} | {t['mrr']:.2f} | "
                         f"{t['statute_recall@5']:.2f} ({t['statute_n']}) | {t['p50_ms']:.0f} |")
        lines += ["", "### Abstention (evidence gate, full configuration)", "", f"`{payload['abstention']}`", ""]
        for lang, t in payload.get("retrieval_by_language", {}).items():
            lines.append(f"- language `{lang}`: full Recall@5 {t['recall@5']:.2f} (n={t['n']})")
    if "calibration" in payload:
        lines += ["", "## Gate calibration (dev split, rerank score)", "", "| threshold | correct abstentions | false abstentions | missed |",
                  "|---|---|---|---|"]
        lines += [f"| {c['threshold']:.2f} | {c['correct_abstentions']} | {c['false_abstentions']} | {c['missed_abstentions']} |"
                  for c in payload["calibration"]]
    if "answers" in payload:
        a = payload["answers"]
        lines += ["", "## Answers (full pipeline)", ""] + [f"- **{k}**: {v}" for k, v in a.items()]
    path = out_dir / f"{ts}.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def run(settings: Settings, split: str = "all", modes: list[str] | None = None, with_answers: bool = True,
        model: str | None = None, calibrate_gate: bool = False) -> tuple[dict, Path]:
    gold = load_gold(split)
    engine = Engine.load(settings)
    modes = modes or list(MODES)
    payload: dict = {"split": split, "n_questions": len(gold), "model": model or settings.ollama_model}
    res = run_retrieval(engine, gold, modes)
    payload["retrieval"] = summarise_retrieval(res)
    payload["retrieval_rows"] = res
    full = res.get("full") or res[modes[-1]]
    payload["abstention"] = abstention(full)
    by_lang: dict = {}
    for lang in sorted({r["language"] for r in full}):
        rows = [r for r in full if r["language"] == lang and "recall@5" in r]
        if rows:
            by_lang[lang] = {"n": len(rows), "recall@5": _mean([r["recall@5"] for r in rows])}
    payload["retrieval_by_language"] = by_lang
    if calibrate_gate:
        payload["calibration"] = calibrate(full)
    if with_answers:
        rows = run_answers(engine, gold, model)
        payload["answers"] = summarise_answers(rows)
        payload["answer_rows"] = rows
    return payload, write_report(settings, payload)
