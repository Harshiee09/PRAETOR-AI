"""Document and chunk records, and the ingestion gate: reject, don't warn (docs/topics/architecture/chunk-schema.md).

`validate_chunk` returns the list of problems; an empty list means the chunk may be stored. Citations are rendered
from these fields, so a missing field would become a missing or wrong citation.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass, field
from datetime import date

DOC_TYPES = {"statute", "judgment", "procedure", "form"}
STATUSES = {"in_force", "repealed", "partially_in_force", "unknown", "n/a"}
PLACEHOLDERS = {"...", "…", "tbd", "n/a", "na", "example", "placeholder", "unknown party", "xxx", "-", "none", "null"}
SC_FOUNDED = date(1950, 1, 28)
ENUM_FIELDS = {"status", "doc_type", "text_source"}  # checked against their allowed sets instead ("n/a" is valid)

COMMON_REQUIRED = ["chunk_id", "doc_id", "doc_type", "title", "source_name", "source_url", "licence", "retrieved_at",
                   "authority", "jurisdiction", "language", "script", "locator", "text", "embed_text", "token_count",
                   "status", "domain_tags", "text_source"]
TYPE_REQUIRED = {
    "statute": ["act_title", "act_year", "section", "section_heading"],
    "judgment": ["case_title", "court", "decision_date"],
    "procedure": ["issuing_body", "valid_as_of"],
    "form": ["issuing_body", "valid_as_of"],
}


def doc_id_for(canonical_url: str) -> str:
    return hashlib.sha256(canonical_url.encode("utf-8")).hexdigest()


def text_hash(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


def slug(locator: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", locator.lower()).strip("-") or "x"


def make_chunk_id(doc_id: str, locator: str, text: str) -> str:
    return f"{doc_id[:12]}:{slug(locator)}:{text_hash(text)[:8]}"


@dataclass
class Document:
    doc_id: str
    doc_type: str
    title: str
    source_name: str
    source_url: str
    licence: str
    retrieved_at: str
    raw_path: str
    raw_sha256: str
    authority: str
    jurisdiction: str
    language: str
    script: str
    parser_version: str
    is_translation: bool = False
    translation_of: str | None = None
    extra: dict = field(default_factory=dict)  # parse stats: pages, unusable pages, sections found vs expected...


@dataclass
class Chunk:
    chunk_id: str
    doc_id: str
    doc_type: str
    title: str
    source_name: str
    source_url: str
    licence: str
    retrieved_at: str
    authority: str
    jurisdiction: str
    language: str
    script: str
    locator: str
    page_start: int | None
    page_end: int | None
    text: str
    embed_text: str
    token_count: int
    status: str
    domain_tags: list[str]
    text_source: str
    ocr_confidence: float | None = None
    # statute
    act_title: str | None = None
    act_year: int | None = None
    act_number: str | None = None
    part: str | None = None
    chapter: str | None = None
    section: str | None = None
    section_heading: str | None = None
    subsection: str | None = None
    amendment_notes: list[dict] | None = None
    successor: str | None = None
    # judgment
    case_title: str | None = None
    court: str | None = None
    decision_date: str | None = None
    judges: list[str] | None = None
    case_number: str | None = None
    citation: str | None = None
    para_start: int | None = None
    para_end: int | None = None
    disposal_nature: str | None = None
    cnr: str | None = None
    # procedure / form
    issuing_body: str | None = None
    valid_as_of: str | None = None
    service_name: str | None = None
    step_range: str | None = None

    def as_dict(self) -> dict:
        return asdict(self)


def _empty(v) -> bool:
    return v is None or (isinstance(v, str) and not v.strip()) or (isinstance(v, (list, dict)) and not v)


def _placeholder(v) -> bool:
    return isinstance(v, str) and v.strip().lower() in PLACEHOLDERS


def validate_chunk(c: Chunk, today: date | None = None) -> list[str]:
    today = today or date.today()
    problems: list[str] = []
    if c.doc_type not in DOC_TYPES:
        return [f"doc_type {c.doc_type!r} not in {sorted(DOC_TYPES)}"]
    for name in COMMON_REQUIRED + TYPE_REQUIRED[c.doc_type]:
        v = getattr(c, name)
        if _empty(v):
            problems.append(f"missing {name}")
        elif name not in ENUM_FIELDS and _placeholder(v):
            problems.append(f"placeholder value in {name}: {v!r}")
    if c.status not in STATUSES:
        problems.append(f"status {c.status!r} not allowed")
    if not (c.source_url or "").startswith(("https://", "s3://")):
        problems.append(f"source_url must start with https:// or s3://: {c.source_url!r}")
    if c.text_source not in {"layer", "ocr", "metadata"}:
        problems.append(f"text_source {c.text_source!r} not allowed")
    if c.token_count is not None and c.token_count <= 0:
        problems.append("token_count must be positive")
    # Pages are the locator of last resort for PDF text; only metadata-rendered chunks (a judgment's case header,
    # DECISIONS D13) and HTML have none. OCR text must say how confident the OCR was.
    if c.text_source in {"layer", "ocr"} and (c.page_start is None or c.page_end is None):
        problems.append("missing page_start/page_end for text taken from a PDF")
    if c.text_source == "ocr" and c.ocr_confidence is None:
        problems.append("missing ocr_confidence for OCR text")
    if c.doc_type == "judgment":
        for party in re.split(r"\s+(?:v\.|vs\.?|versus)\s+", c.case_title or "", flags=re.I):
            if party.strip(" .").lower() in PLACEHOLDERS or not party.strip(" ."):
                problems.append(f"placeholder party in case_title: {c.case_title!r}")
        try:
            d = date.fromisoformat(c.decision_date or "")
            if d > today:
                problems.append(f"decision_date in the future: {d}")
            if c.court == "Supreme Court of India" and d < SC_FOUNDED:
                problems.append(f"Supreme Court decision_date before 1950-01-28: {d}")
        except ValueError:
            problems.append(f"decision_date not an ISO date: {c.decision_date!r}")
    if c.doc_type == "statute" and c.act_year and not (1800 <= c.act_year <= today.year):
        problems.append(f"impossible act_year {c.act_year}")
    if c.retrieved_at:
        try:
            if date.fromisoformat(c.retrieved_at[:10]) > today:
                problems.append("retrieved_at in the future")
        except ValueError:
            problems.append(f"retrieved_at not ISO: {c.retrieved_at!r}")
    return problems
