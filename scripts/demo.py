"""Scripted demo against the running API (`praetor serve`): seven real gold-set questions, one per demo scenario.

    python scripts/demo.py                                  # http://127.0.0.1:8000, key from API_KEY if set
    python scripts/demo.py --url https://<tunnel-host>      # through a tunnel (needs API_KEY)
    python scripts/demo.py --save-examples docs/api/examples   # also write the real responses for the frontend

For each question it prints the answer's first lines, its sources, warnings and timing, and checks two invariants:
every [S#] marker in the answer has a source card, and the out-of-corpus question abstains. Exit code 1 if a check
fails or the server is unreachable. Questions come from evaluation/gold.jsonl (ids below), not written here.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
SCENARIOS = [  # (scenario, gold id, should abstain)
    ("statute lookup", "reg-023-time-limit", False),
    ("procedure", "proc-cpa-035-file", False),
    ("case law", "cl-ida-24-2-lapse", False),
    ("criminal-code transition", "tr-438-anticipatory", False),
    ("Hindi question", "hi-bnss-482-anticipatory", False),
    ("out of corpus", "oos-visa", True),
    ("high stakes", "hs-eviction-tomorrow", False),
]


def check(resp: dict, should_abstain: bool) -> list[str]:
    """Invariants the frontend can rely on."""
    problems = []
    ids = {c["id"] for c in resp.get("citations", [])}
    missing = set(re.findall(r"\[(S\d+)\]", resp.get("answer_markdown", ""))) - ids
    if missing:
        problems.append(f"markers without a source card: {sorted(missing)}")
    if should_abstain and not resp.get("abstained"):
        problems.append("expected an abstention")
    if not should_abstain and not resp.get("abstained") and not resp.get("citations"):
        problems.append("answered without citations")
    return problems


def _api_key() -> str:
    if os.environ.get("API_KEY"):
        return os.environ["API_KEY"]
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            if line.startswith("API_KEY="):
                return line.split("=", 1)[1].strip().strip('"')
    return ""


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    p = argparse.ArgumentParser()
    p.add_argument("--url", default="http://127.0.0.1:8000")
    p.add_argument("--save-examples", default=None, help="folder for the raw JSON responses")
    p.add_argument("--fresh", action="store_true", help="bypass the answer cache")
    args = p.parse_args()

    gold = {json.loads(line)["id"]: json.loads(line) for line in
            (ROOT / "evaluation" / "gold.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()}
    headers = {"X-API-Key": key} if (key := _api_key()) else {}
    client = httpx.Client(base_url=args.url.rstrip("/"), headers=headers, timeout=300)
    try:
        health = client.get("/v1/healthz")
    except httpx.HTTPError as exc:
        print(f"cannot reach {args.url}: {exc}\nstart the server first:  praetor serve")
        return 1
    print(f"server {args.url}: {health.json()['status']}  {health.json()['checks']}\n")
    out_dir = Path(args.save_examples) if args.save_examples else None
    if out_dir:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "healthz.json").write_text(json.dumps(health.json(), ensure_ascii=False, indent=2), encoding="utf-8")

    failures, rows = 0, []
    for scenario, gid, should_abstain in SCENARIOS:
        q = gold[gid]["question"]
        r = client.post("/v1/ask", json={"question": q, "use_cache": not args.fresh})
        if r.status_code != 200:
            print(f"[{scenario}] HTTP {r.status_code}: {r.text[:300]}")
            failures += 1
            continue
        resp = r.json()
        problems = check(resp, should_abstain)
        failures += bool(problems)
        print(f"=== {scenario} ({gid}) ===\nQ: {q}")
        body = [ln for ln in resp["answer_markdown"].splitlines() if ln.strip()]
        print("\n".join(body[:6]) + ("\n..." if len(body) > 6 else ""))
        for c in resp["citations"][:5]:
            print(f"  [{c['id']}] {c['title']} — {c['locator']} ({c['status']})")
        print(f"  confidence {resp['confidence']} · abstained {resp['abstained']} · provider {resp['provider']} · "
              f"{len(resp['warnings'])} warning(s) · {resp['latency_ms'] / 1000:.1f} s{' (cached)' if resp['cached'] else ''}")
        print(f"  checks: {'OK' if not problems else '; '.join(problems)}\n")
        rows.append((scenario, resp["abstained"], len(resp["citations"]), resp["latency_ms"], not problems))
        if out_dir:
            (out_dir / f"ask_{gid}.json").write_text(json.dumps(resp, ensure_ascii=False, indent=2), encoding="utf-8")
            if resp["citations"] and gid == "reg-023-time-limit":
                src = client.get(f"/v1/sources/{resp['citations'][0]['chunk_id']}").json()
                (out_dir / "source_example.json").write_text(json.dumps(src, ensure_ascii=False, indent=2), encoding="utf-8")
    if out_dir:
        (out_dir / "stats.json").write_text(json.dumps(client.get("/v1/stats").json(), ensure_ascii=False, indent=2),
                                            encoding="utf-8")

    print("scenario                   abstained  sources  seconds  checks")
    for scenario, abstained, n, ms, ok in rows:
        print(f"{scenario:26} {str(abstained):9} {n:7}  {ms / 1000:7.1f}  {'OK' if ok else 'FAIL'}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
