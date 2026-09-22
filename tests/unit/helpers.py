"""Build real Chunk records from fixtures (text and provenance come from the source; nothing is invented)."""

from __future__ import annotations

import dataclasses
from pathlib import Path

import yaml

from app.chunking.assemble import judgment_chunks, statute_chunks
from app.chunking.judgment import split_judgment
from app.chunking.schema import Chunk, Document, doc_id_for
from app.chunking.statute import split_statute
from tests.conftest import load_fixture, parsed_from_fixture

REGISTRY = Path(__file__).parents[2] / "data" / "registry"


def words(text: str) -> int:
    """Whitespace token count: the real pipeline uses the bge-m3 tokenizer, tests don't need to load it."""
    return len(text.split())


def statute_fixture_chunks(name: str, act_id: str) -> list[Chunk]:
    fx = load_fixture(name)
    jur = yaml.safe_load((REGISTRY / "jurisdictions.yaml").read_text(encoding="utf-8"))
    act = {s["id"]: s for s in yaml.safe_load((REGISTRY / "statutes.yaml").read_text(encoding="utf-8"))}[act_id]
    sp = split_statute(parsed_from_fixture(name), set(jur["codes"]) | set(jur["aliases"]))
    doc = Document(doc_id=doc_id_for(fx["source_url"] + "#en"), doc_type="statute", title=act["short_title"],
                   source_name="India Code", source_url=fx["source_url"], licence=fx["licence"],
                   retrieved_at=fx["retrieved_at"], raw_path="fixture", raw_sha256=fx["raw_sha256"],
                   authority="Parliament of India", jurisdiction="IN", language="en", script="Latn", parser_version="test")
    return statute_chunks(doc, sp, act, jur, ["property_land"], words, 450)


def judgment_fixture_chunks(name: str) -> list[Chunk]:
    fx = load_fixture(name)
    doc = Document(doc_id=doc_id_for(fx["download_url"]), doc_type="judgment", title=fx["metadata"]["case_title"],
                   source_name="Indian Supreme Court Judgments (AWS Open Data)", source_url=fx["download_url"],
                   licence=fx["licence"], retrieved_at=fx["retrieved_at"], raw_path="fixture", raw_sha256=fx["raw_sha256"],
                   authority="Supreme Court of India", jurisdiction="IN", language="en", script="Latn", parser_version="test")
    return judgment_chunks(doc, split_judgment(parsed_from_fixture(name)), fx["metadata"], ["case_law"], words, 450)


def as_row(c: Chunk) -> dict:
    return dataclasses.asdict(c)
