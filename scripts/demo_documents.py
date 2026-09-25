"""Scripted demo of document mode against a running server (`praetor serve`): upload, then ask, summary, risks,
checklist, lawyer questions and compare, with invariant checks on every answer (DECISIONS D50).

    uv run python scripts/demo_documents.py AGREEMENT.pdf [OTHER.pdf] [--question "..."] [--save-examples DIR]

Checks per answer: HTTP 200; every [D#]/[S#] marker in the answer has a citation card and every card is cited; each
document card's quote is a verbatim substring of the uploaded passage it points to. Uploaded documents are deleted at
the end. The API key comes from the environment (.env), never from the command line.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.config import Settings  # noqa: E402

MARK = re.compile(r"\[([DS]\d{1,3})\]")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("pdfs", nargs="+", type=Path, help="one PDF, or two to include `compare`")
    ap.add_argument("--question", default="What happens if the promoter delays possession?")
    ap.add_argument("--save-examples", type=Path, help="write each response (without `explain`) here as JSON")
    ap.add_argument("--base-url", default=None)
    args = ap.parse_args()
    s = Settings()
    base = args.base_url or f"http://{s.api_host}:{s.api_port}"
    c = httpx.Client(base_url=base, headers={"X-API-Key": s.api_key} if s.api_key else {}, timeout=600)
    health = c.get("/v1/healthz").json()
    print("health:", health["status"], "| documents:", health["checks"].get("documents"))

    ids, passages = [], {}
    for p in args.pdfs[:2]:
        r = c.post("/v1/documents", files={"file": (p.name, p.read_bytes(), "application/pdf")})
        if r.status_code != 201:
            print(f"upload {p.name}: {r.status_code} {r.json()['error']['message']}")
            return 1
        info = r.json()
        ids.append(info["document_id"])
        detail = c.get(f"/v1/documents/{info['document_id']}").json()
        passages.update({f"{info['document_id']}:{x['n']}": x["text"] for x in detail["passages"]})
        if args.save_examples and len(ids) == 1:  # the upload and passage responses, for frontend builders
            args.save_examples.mkdir(parents=True, exist_ok=True)
            for name, body in (("document_upload", info), ("document_passages", detail)):
                (args.save_examples / f"{name}.json").write_text(json.dumps(body, ensure_ascii=False, indent=2) + "\n",
                                                                 encoding="utf-8")
        print(f"uploaded {p.name}: {info['pages']} pages, {info['passage_count']} passages {info['warnings'] or ''}")

    runs = [("ask", ids[:1], args.question), ("summary", ids[:1], None), ("risks", ids[:1], None),
            ("checklist", ids[:1], None), ("lawyer_questions", ids[:1], None)]
    if len(ids) == 2:
        runs.append(("compare", ids, "refunds, interest and cancellation"))
    failed = 0
    print(f"\n{'task':<17}{'status':<8}{'secs':>5}  {'provider':<11}{'conf':<8}{'cites':>5}  checks")
    for task, docs, q in runs:
        t0 = time.time()
        r = c.post("/v1/documents/analyze", json={"document_ids": docs, "task": task, "question": q})
        body = r.json()
        problems = []
        if r.status_code != 200:
            problems.append(body.get("error", {}).get("message", str(r.status_code)))
        else:
            marks = set(MARK.findall(body["answer_markdown"]))
            cards = {x["id"]: x for x in body["citations"]}
            if marks != set(cards):
                problems.append(f"markers {sorted(marks - set(cards))} have no card; cards {sorted(set(cards) - marks)} uncited")
            for x in cards.values():
                if x["kind"] == "document" and x["quote"] not in re.sub(r"\s+", " ", passages.get(x["chunk_id"], "")):
                    problems.append(f"{x['id']} quote is not in its passage")
            if args.save_examples:
                args.save_examples.mkdir(parents=True, exist_ok=True)
                (args.save_examples / f"document_{task}.json").write_text(
                    json.dumps({k: v for k, v in body.items() if k != "explain"}, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")
        failed += bool(problems)
        print(f"{task:<17}{r.status_code:<8}{time.time() - t0:>5.0f}  {str(body.get('provider')):<11}"
              f"{str(body.get('confidence')):<8}{len(body.get('citations', [])):>5}  {'; '.join(problems) or 'OK'}")
    for d in ids:
        c.delete(f"/v1/documents/{d}")
    print(f"\n{len(runs) - failed} of {len(runs)} OK")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
