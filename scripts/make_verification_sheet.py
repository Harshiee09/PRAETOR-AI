"""Write evaluation/verification_sheet.csv: one row per gold question for a person to verify (one-off utility).

Each row shows the question, the proposed expected sources and must-mention phrases, a verbatim excerpt of each
expected source cut from the stored chunk text (never paraphrased), its URL, and the known uncertainties. The reviewer
fills `verdict`, `corrected_expected_sources`, `verified_by`, `verified_on` and `reviewer_notes`; nothing here marks a
question verified. Opens in Excel (UTF-8 with BOM, so Hindi displays).

    uv run python scripts/make_verification_sheet.py
"""

from __future__ import annotations

import csv
import re

from app.config import REPO_ROOT, get_settings
from app.rag.classify import expand_terms
from app.rag.evaluate import load_gold
from app.store.db import connect

OUT = REPO_ROOT / "evaluation" / "verification_sheet.csv"
EXCERPT = 500


def _excerpt(text: str) -> str:
    t = re.sub(r"\s+", " ", text).strip()
    return t if len(t) <= EXCERPT else t[:EXCERPT].rsplit(" ", 1)[0] + " …"


def _source(conn, src: dict) -> tuple[str, str, str]:
    """(label, url, verbatim excerpt) for one expected source."""
    if "act" in src:
        rows = conn.execute("SELECT text, source_url, locator FROM chunks WHERE act_title = ? AND section = ? AND "
                            "jurisdiction = 'IN' ORDER BY rowid", (src["act"], str(src["section"]))).fetchall()
        if not rows:
            return f"{src['act']} s. {src['section']}", "", "NOT FOUND IN THE INDEX"
        return f"{src['act']} {rows[0][2]}", rows[0][1], _excerpt(" ".join(r[0] for r in rows))
    if "neutral_citation" in src:
        row = conn.execute("SELECT case_title, decision_date, citation, source_url FROM chunks WHERE citation LIKE ? "
                           "AND locator = 'header' LIMIT 1", (f"%{src['neutral_citation']}%",)).fetchone()
        if not row:
            return src["neutral_citation"], "", "NOT FOUND IN THE INDEX"
        return f"{row[0]} ({row[1]}), {row[2]}", row[3], "(judgment: check the passage the question relies on)"
    return str(src), "", ""


def _uncertainties(g: dict, settings) -> list[str]:
    out = ["draft written by Claude; expected sources copied from the ingested text"]
    if g["language"] != "en":
        out.append("phrasing drafted by Claude: needs a native speaker")
    ids, _ = expand_terms(g["question"], settings.registry_dir)
    if ids:
        out.append(f"retrieval uses term expansion {ids} (data/registry/legal_terms.yaml), added after seeing failures")
    if g["should_abstain"] or g["id"] == "hs-eviction-tomorrow":
        out.append("the evidence threshold (0.10) was chosen after seeing this question's score (DECISIONS D27)")
    if g.get("domain") == "criminal_procedure":
        out.append("CrPC text is not ingested; old-law answers rely on judgments and the BNSS repeal section")
    if g.get("notes"):
        out.append("note: " + g["notes"])
    if g.get("split_note"):
        out.append(g["split_note"])
    return out


def main() -> None:
    settings = get_settings()
    conn = connect(settings.sqlite_path)
    gold = load_gold("all")
    cols = ["id", "group", "split", "language", "intent", "question", "should_abstain", "match", "expected_sources",
            "must_mention", "source_urls", "source_excerpts", "uncertainties", "verdict (ok / fix / drop)",
            "corrected_expected_sources", "verified_by", "verified_on", "reviewer_notes"]
    with OUT.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for g in gold:
            srcs = [_source(conn, s) for s in g["expected_sources"]]
            w.writerow([g["id"], g.get("group", g["id"]), g["split"], g["language"], g["intent"], g["question"],
                        g["should_abstain"], g.get("match", "all"), " | ".join(s[0] for s in srcs),
                        " | ".join(g["must_mention"]), " | ".join(s[1] for s in srcs),
                        " || ".join(f"[{s[0]}] {s[2]}" for s in srcs), "; ".join(_uncertainties(g, settings)),
                        "", "", g.get("verified_by") or "", g.get("verified_on") or "", ""])
    conn.close()
    print(f"{OUT.relative_to(REPO_ROOT)}: {len(gold)} questions")


if __name__ == "__main__":
    main()
