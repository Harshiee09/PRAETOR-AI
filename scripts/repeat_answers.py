"""Run the same gold questions several times and show where answers vary (one-off diagnostic utility).

For each run it records hashes of the retrieval context (S# -> chunk ids), the raw model output and the final answer,
plus validator removals and whether the question's must_mention phrases survived. Identical context hashes with
different raw-output hashes mean the variation starts in generation, not retrieval. There is no answer cache to bypass
(nothing reads the `cache` table; DECISIONS D37), so every run is a fresh call.

    uv run python scripts/repeat_answers.py tpa-106-lease-notice --runs 5                  # current decoding settings
    uv run python scripts/repeat_answers.py tpa-106-lease-notice --runs 5 --temperature 0.1 --no-seed   # Phase 2 decoding
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone

from app.config import REPO_ROOT, get_settings
from app.rag.evaluate import load_gold, run_metadata
from app.rag.pipeline import Engine, answer


def h(x) -> str:
    return hashlib.sha256(json.dumps(x, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:12]


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("ids", nargs="+")
    p.add_argument("--runs", type=int, default=5)
    p.add_argument("--temperature", type=float, default=None)
    p.add_argument("--no-seed", action="store_true")
    args = p.parse_args()

    settings = get_settings()
    update = {}
    if args.temperature is not None:
        update["llm_temperature"] = args.temperature
    if args.no_seed:
        update["llm_seed"] = None
    settings = settings.model_copy(update=update)
    engine = Engine.load(settings)
    gold = {g["id"]: g for g in load_gold("all")}
    out = {"run": run_metadata(settings, engine, None), "runs_per_question": args.runs, "questions": {}}
    for qid in args.ids:
        g = gold[qid]
        rows = []
        for i in range(args.runs):
            o = answer(engine, g["question"], explain=True)
            e = o["explain"]
            text = o["answer_markdown"].lower()
            rows.append({
                "run": i + 1, "abstained": o["abstained"], "provider": o["provider"], "confidence": o["confidence"],
                "context": h(e.get("context_ids")), "raw": h([a["raw"] for a in e.get("attempts", [])]),
                "final": h(o["answer_markdown"]), "removed": len((e.get("validator") or {}).get("removed_sentences", [])),
                "unsupported": (e.get("validator") or {}).get("unsupported"),
                "cited": sorted(c["chunk_id"] for c in o["citations"]),
                "must_mention": all(m.lower() in text for m in g["must_mention"]) if g["must_mention"] else None})
        summary = {k: dict(Counter(str(r[k]) for r in rows)) for k in ("context", "raw", "final", "must_mention", "confidence")}
        out["questions"][qid] = {"rows": rows, "distinct": summary}
        print(qid, json.dumps(summary, ensure_ascii=False))
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = REPO_ROOT / "evaluation" / "reports" / f"repeat_{ts}.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print(f"report -> {path.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
