"""Phase 1 checks against the real downloaded corpus. Needs data/raw (run `praetor ingest`), and for the retrieval
test the built index and a GPU or CPU embedder (run `praetor index`)."""

import json
import shutil

import pytest

from app.config import Settings, get_settings
from app.ingestion.manifest import Manifest

pytestmark = pytest.mark.integration
REAL = get_settings()


def _need(path):
    if not path.exists():
        pytest.skip(f"{path} missing: run `praetor ingest` / `praetor index` first")


def test_parser_removes_watermark_and_margin_letters():
    from app.parsing.pdf import parse_pdf

    act = REAL.raw_dir / "indiacode" / "registration-1908" / "a1908-16.pdf"
    scr = REAL.raw_dir / "sc-judgments" / "pdf" / "year=2021" / "english" / "2021_11_1181_1194_EN.pdf"
    _need(act), _need(scr)
    doc = parse_pdf(act)
    assert sum(p.watermark_chars for p in doc.pages) > 0
    heading = next(ln for ln in doc.lines if ln.text.startswith("OF THE TIME OF PRESENTA"))
    assert heading.text == "OF THE TIME OF PRESENTATION"  # a watermark glyph once landed inside this word
    j = parse_pdf(scr, drop_margin_letters=True, strip_running_headers=True, drop_small_text=True)
    assert sum(p.margin_chars for p in j.pages) > 0
    assert not any(ln.text.strip() in list("ABCDEFGH") for ln in j.lines)
    assert not any("SUPREME COURT REPORTS" in ln.text for ln in j.lines)


def test_index_twice_adds_zero_rows(tmp_path):
    from app.ingestion.build import build

    _need(REAL.manifest_path)
    data = tmp_path / "data"
    shutil.copytree(REAL.registry_dir, data / "registry")
    rows = [r for r in Manifest(REAL.manifest_path, REAL.data_dir).rows()
            if r.local_path.endswith("cpa-2019/A2019-35.pdf") or "2021_11_1181_1194_EN" in r.local_path]
    assert len(rows) == 2
    (data / "raw").mkdir(parents=True)
    with (data / "raw" / "manifest.jsonl").open("w", encoding="utf-8") as f:
        for r in rows:
            src = REAL.data_dir / r.local_path
            dst = data / r.local_path
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            if src.with_suffix(".json").exists():
                shutil.copy2(src.with_suffix(".json"), dst.with_suffix(".json"))
            f.write(json.dumps(r.__dict__, ensure_ascii=False) + "\n")
    s = Settings(_env_file=None, data_dir=data)
    first = build(s, embed=False)
    second = build(s, embed=False)
    assert first["docs_changed"] == 2 and first["chunks_added"] > 100 and first["chunks_rejected"] == 0
    assert second["docs_changed"] == 0 and second["chunks_added"] == 0 and second["chunks_total"] == first["chunks_total"]


@pytest.mark.parametrize("question, act, section", [
    ("What is the time limit for presenting a document for registration?", "Registration Act, 1908", "23"),
    ("What counts as a sale of immovable property?", "Transfer of Property Act, 1882", "54"),
    ("What is the limitation period for filing a consumer complaint?", "Consumer Protection Act, 2019", "69"),
])
def test_known_item_questions_rank_the_right_section_first(question, act, section):
    from app.retrieval.dense import DenseRetriever
    from app.store.db import chunks_by_rowids, connect

    _need(REAL.faiss_path)
    retriever = DenseRetriever(REAL)
    hits, _ = retriever.search(question, 5)
    conn = connect(REAL.sqlite_path)
    top = chunks_by_rowids(conn, [hits[0][0]])[0]
    assert (top["act_title"], top["section"]) == (act, section)
    assert hits[0][1] >= REAL.min_dense_score
