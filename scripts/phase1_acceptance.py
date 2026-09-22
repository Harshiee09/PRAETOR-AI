"""Phase 1 acceptance run (build-plan note): three known-item questions answered with the right section cited,
plus an out-of-corpus question that must abstain. Writes evaluation/reports/phase1_acceptance_<ts>.json.

    uv run python scripts/phase1_acceptance.py
"""

from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone

from app.config import REPO_ROOT, get_settings
from app.config.logs import setup_logging
from app.rag.pipeline import Engine, answer

CASES = [
    # question, expected (act_title, section), phrase that must appear in the cited section's stored text
    ("What is the time limit for presenting a document for registration?", ("Registration Act, 1908", "23"),
     "within four months from the date of its execution"),
    ("What counts as a sale of immovable property?", ("Transfer of Property Act, 1882", "54"),
     "is a transfer of ownership in exchange for a price paid or promised"),
    ("What is the limitation period for filing a consumer complaint?", ("Consumer Protection Act, 2019", "69"),
     "within two years from the date on which the cause of action has arisen"),
    ("How do I apply for a passport?", None, None),
]


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    settings = get_settings()
    setup_logging("ERROR")
    engine = Engine.load(settings)
    results, ok = [], True
    for q, expected, phrase in CASES:
        t0 = time.perf_counter()
        out = answer(engine, q, explain=True)
        secs = round(time.perf_counter() - t0, 1)
        cited = [(c["title"], c["locator"]) for c in out["citations"]]
        if expected is None:
            passed = out["abstained"]
        else:
            act, sec = expected
            hit = [c for c in out["citations"] if c["title"] == act and c["locator"] == f"s. {sec}"]
            # the phrase is checked against the stored chunk behind the citation, not against model output
            chunk_ok = bool(hit) and phrase in " ".join(engine_text(settings, hit[0]["chunk_id"]).split())
            passed = bool(hit) and chunk_ok and not out["abstained"]
        ok &= passed
        results.append({"question": q, "expected": expected, "passed": passed, "seconds": secs, "cited": cited,
                        "abstained": out["abstained"], "provider": out.get("provider"), "llm": out["explain"].get("llm"),
                        "top_dense": out["explain"]["top_dense_score"], "warnings": out["warnings"],
                        "answer_markdown": out["answer_markdown"]})
        print(f"{'PASS' if passed else 'FAIL'}  {secs:>6}s  {q}\n      cited: {cited}\n")
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = REPO_ROOT / "evaluation" / "reports" / f"phase1_acceptance_{ts}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"model": settings.ollama_model, "results": results}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{'ALL PASS' if ok else 'FAILURES'} -> {path.relative_to(REPO_ROOT)}")
    return 0 if ok else 1


def engine_text(settings, chunk_id: str) -> str:
    from app.store.db import chunk_by_id, connect

    conn = connect(settings.sqlite_path)
    try:
        return chunk_by_id(conn, chunk_id)["text"]
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
