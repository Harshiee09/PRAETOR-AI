"""Snapshot parsed lines from real source PDFs into tests/fixtures/ (one-off utility; re-run after parser changes).

Each fixture records the source URL, the raw file's sha256 and retrieval time from data/raw/manifest.jsonl, the
page numbers taken, and the parser output for those pages, so splitter tests run on real text without the PDFs.

    uv run python scripts/make_fixtures.py
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from app.config import REPO_ROOT, get_settings
from app.ingestion.manifest import Manifest
from app.parsing.pdf import parse_pdf

FIXTURES = [
    # (name, raw path under DATA_DIR, pages, judgment layout?)
    ("registration_1908_ss1-8", "raw/indiacode/registration-1908/a1908-16.pdf", [1, 4, 5, 6, 7], False),
    ("registration_1908_s23", "raw/indiacode/registration-1908/a1908-16.pdf", [17], False),
    ("tpa_1882_ss1-3_nested_footnotes", "raw/indiacode/tpa-1882/a1882-04.pdf", [1, 7, 8], False),
    ("tpa_1882_s53A-55_state_amendment", "raw/indiacode/tpa-1882/a1882-04.pdf", [20], False),
    ("cpa_2019_s69", "raw/indiacode/cpa-2019/A2019-35.pdf", [30], False),
    ("cpc_1908_toc_after_amending_acts_list", "raw/indiacode/cpc-1908/a1908-05.pdf", [2, 4], False),
    ("cpc_1908_order39_rule1", "raw/indiacode/cpc-1908/a1908-05.pdf", [214], False),
    ("sc_2016_3_scr_225_ocr_marker", "raw/sc-judgments/pdf/year=2016/english/2016_3_225_227_EN.pdf", [1, 2], True),
    ("sc_2021_11_scr_1181_old_layout", "raw/sc-judgments/pdf/year=2021/english/2021_11_1181_1194_EN.pdf", [3, 4, 14], True),
    ("sc_2025_1_scr_62_digital_layout", "raw/sc-judgments/pdf/year=2025/english/2025_1_62_80_EN.pdf", [4, 5, 19], True),
]


def main() -> None:
    settings = get_settings()
    manifest = {r.local_path: r for r in Manifest(settings.manifest_path, settings.data_dir).rows()}
    out_dir = REPO_ROOT / "tests" / "fixtures"
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, rel, pages, judgment in FIXTURES:
        row = manifest[rel]
        doc = parse_pdf(settings.data_dir / rel, drop_margin_letters=judgment, strip_running_headers=judgment,
                        drop_small_text=judgment)
        lines = [asdict(ln) for ln in doc.lines if ln.page in pages]
        source_url = row.source_page if row.source == "indiacode" else row.url
        payload = {
            "source_url": source_url, "download_url": row.url, "raw_sha256": row.sha256,
            "retrieved_at": row.retrieved_at, "licence": row.licence, "pages": pages,
            "parser": "app.parsing.pdf.parse_pdf", "judgment_layout": judgment,
            "body_size": doc.body_size, "page_height": doc.page_height, "lines": lines,
        }
        if row.source == "sc-judgments":
            payload["metadata"] = json.loads((settings.data_dir / rel).with_suffix(".json").read_text(encoding="utf-8"))
        path = out_dir / f"{name}.json"
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"{path.relative_to(REPO_ROOT)}: {len(lines)} lines from pages {pages}")


if __name__ == "__main__":
    main()
