"""Request and response models: the contract the frontend builds against (exported to docs/api/openapi.json).

The answer shape is the grounding note's response contract. Citation cards are rendered from stored metadata, never
from model text, so the frontend should display `citations[]` as the sources and treat `answer_markdown` as prose
that refers to them by [S#].
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

Mode = Literal["full", "hybrid_rerank", "hybrid", "dense", "keyword"]


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000, description="The user's question, in any supported language.")
    mode: Mode = Field("full", description="Retrieval configuration; keep `full` in production.")
    explain: bool = Field(False, description="Include per-stage retrieval ranks, timings and validator details.")
    use_cache: bool = Field(True, description="Reuse a cached answer for the same question and system version.")


class Citation(BaseModel):
    id: str = Field(description="The marker used in answer_markdown: [S#] for law, [D#] for the user's own document.")
    kind: Literal["law", "document"] = Field("law", description="`document`: a passage of an uploaded document; its "
                                                               "full text is in GET /v1/documents/{document_id}.")
    chunk_id: str = Field(description="Law: pass to GET /v1/sources/{chunk_id}. Document: `<document_id>:<passage n>`.")
    title: str
    locator: str = Field(description="Where in the source: `s. 106`, `paras 12-15`, `pp. 8-9`.")
    authority: str
    jurisdiction: str = Field(description="`IN` for central law; ISO 3166-2 code for a state amendment.")
    status: str = Field(description="`in_force`, `repealed`, `partially_in_force` or `n/a` (judgments).")
    source_url: str
    retrieved_at: str
    quote: str = Field(description="Verbatim excerpt (<= 300 characters) cut from the stored text in code.")
    section_heading: str | None = None
    court: str | None = None
    decision_date: str | None = None
    citation: str | None = Field(None, description="Neutral or reporter citation as printed in the source record.")
    document_id: str | None = Field(None, description="Uploaded document the passage comes from (kind `document`).")
    page_start: int | None = None
    page_end: int | None = None


class Classification(BaseModel):
    domain: str
    intent: str
    high_stakes: bool


class AskResponse(BaseModel):
    answer_markdown: str = Field(description="Markdown answer. A high-stakes answer starts with a safety block.")
    language: str
    confidence: Literal["high", "medium", "low"]
    abstained: bool = Field(description="True when the system declined to answer (thin evidence or a refused request).")
    citations: list[Citation]
    warnings: list[str] = Field(description="Deterministic notes to show with the answer: repeal, transition, "
                                            "state-law coverage, removed sentences.")
    jurisdiction_note: str
    disclaimer: str = Field(description="Show once with every answer.")
    trace_id: str = Field(description="Equals the X-Request-ID response header.")
    provider: str | None = Field(description="`ollama`, `extractive` (no model; verbatim passages) or null.")
    model: str | None = None
    classification: Classification
    cached: bool = False
    latency_ms: int
    explain: dict | None = None


DocumentTask = Literal["ask", "summary", "risks", "checklist", "lawyer_questions", "compare"]


class DocumentInfo(BaseModel):
    document_id: str = Field(description="Use in POST /v1/documents/analyze; expires at `expires_at`.")
    filename: str
    pages: int
    unreadable_pages: list[int] = Field(description="Pages without a usable text layer (scanned); left out.")
    passage_count: int
    words: int
    uploaded_at: str
    expires_at: str = Field(description="The document is held in server memory until then, never written to disk.")
    warnings: list[str]


class Passage(BaseModel):
    n: int = Field(description="Passage number; a [D#] card's chunk_id is `<document_id>:<n>`.")
    locator: str = Field(description="`clause 7 · p. 2`, `paras 12-14 · pp. 3-4` or `p. 5`.")
    page_start: int
    page_end: int
    text: str


class DocumentDetail(DocumentInfo):
    passages: list[Passage]


class AnalyzeRequest(BaseModel):
    document_ids: list[str] = Field(min_length=1, max_length=2, description="One document; two for `compare`.")
    task: DocumentTask = Field("ask", description="`ask` (needs `question`), `summary`, `risks` (clauses, obligations, "
                                                  "risks, inconsistencies, comparison with the law), `checklist`, "
                                                  "`lawyer_questions`, `compare` (two documents).")
    question: str | None = Field(None, max_length=2000, description="Required for `ask`; optional focus for the rest.")
    explain: bool = False

    @model_validator(mode="after")
    def _shape(self):
        if self.task == "ask" and not (self.question or "").strip():
            raise ValueError("task `ask` needs a question")
        if (self.task == "compare") != (len(self.document_ids) == 2):
            raise ValueError("`compare` needs exactly two document_ids; the other tasks take one")
        return self


class Coverage(BaseModel):
    document_id: str
    filename: str
    pages_read: str = Field(description="Pages the analysis could read, e.g. `1-6, 9`.")
    complete: bool = Field(description="False when the document was too long for one pass or had unreadable pages.")


class AnalyzeResponse(AskResponse):
    task: DocumentTask
    documents: list[Coverage]
    law_checked: bool = Field(description="True when Indian law passages were searched for (they are added only if "
                                          "they pass the evidence gate).")


class Source(BaseModel):
    chunk_id: str
    doc_type: str
    title: str
    locator: str
    text: str = Field(description="The full stored passage.")
    authority: str
    jurisdiction: str
    status: str
    language: str
    source_url: str
    retrieved_at: str
    licence: str
    page_start: int | None = None
    page_end: int | None = None
    act_title: str | None = None
    section: str | None = None
    section_heading: str | None = None
    case_title: str | None = None
    court: str | None = None
    decision_date: str | None = None
    citation: str | None = None


class Health(BaseModel):
    status: Literal["ok", "degraded", "down"] = Field(description="Library questions (/v1/ask). `degraded`: no answer "
                                                                  "model, so answers fall back to verbatim passages; "
                                                                  "`down`: the index or engine is unusable. Document "
                                                                  "mode is separate: see `checks.documents`.")
    checks: dict[str, str]


class Stats(BaseModel):
    documents: dict[str, int]
    chunks: dict[str, int]
    index: dict
    model: dict
    prompt_version: str
    cache_entries: int
    uptime_s: int
    requests: dict[str, int]
    answer_latency_ms: dict[str, int | None]


class ErrorBody(BaseModel):
    code: str
    message: str
    request_id: str


class Error(BaseModel):
    error: ErrorBody
