---
id: 20260922-grounding-and-citations
title: Grounding and citations
tags: [legal, safety, llm]
created: 2026-09-22
updated: 2026-09-22
related: [20260922-retrieval-pipeline, 20260922-llm-layer, 20260922-statute-status, 20260922-chunk-schema, 20260922-evaluation]
summary: Answer contract, deterministic citation validator, abstention and high-stakes handling.
---

# Grounding and citations

> Summary: Answer contract, deterministic citation validator, abstention and high-stakes handling.

## Context
PRAETOR AI is an informational legal-assistance and professional-preparation tool. It has to separate what the sources say from what is uncertain, cite everything it asserts about the law, name the jurisdiction and date context, and say plainly when it doesn't have enough to answer. The prompt asks for this; deterministic code enforces it.

## Details

### Response contract (`POST /v1/ask`)
```json
{
  "answer_markdown": "...",
  "language": "hi",
  "confidence": "high | medium | low",
  "abstained": false,
  "citations": [
    {"id": "S1", "chunk_id": "...", "title": "Registration Act, 1908", "locator": "s. 23",
     "authority": "Parliament of India", "jurisdiction": "IN", "status": "in_force",
     "source_url": "https://...", "retrieved_at": "2026-09-23",
     "quote": "verbatim excerpt of at most 300 characters"}
  ],
  "warnings": ["..."],
  "jurisdiction_note": "...",
  "disclaimer": "...",
  "trace_id": "..."
}
```

### Answer shape (what the system prompt asks for)
1. **Short answer**, pitched at the confidence the sources actually support.
2. **What the sources say** — every sentence carries at least one `[S#]`.
3. **How it may apply** — conditions and exceptions found in the sources, cited.
4. **Uncertain or not covered** — what the sources don't settle: state-specific rules, facts we don't know, later amendments.
5. **Jurisdiction and date** — central versus state law, "based on texts retrieved on <date>", and any repeal or transition note.
6. **Next steps** — practical lawful steps, and for anything high-stakes, consulting an advocate or the local legal services authority.

One short disclaimer at the end: general information, not legal advice. Say it once, not in every section.

### Citation validator (`app/citations/validator.py`, deterministic)
1. Parse `[S#]` markers. IDs outside this request's `S# -> chunk_id` map are removed and logged as `invalid_citation`.
2. Scan the answer for authority-like strings: section references (`Section 23`, `s. 23`, `धारा 23`), Act titles with years, case names (`X v. Y`, `X vs. Y`), and citation formats such as `(YYYY) N SCC N`, `AIR YYYY SC N` or neutral citations like `YYYY INSC N`. Each must appear in the cited chunks' text or metadata. Anything else has its sentence removed, adds a warning, and counts as `unverified_authority`.
3. Sentences under "What the sources say" with no marker are flagged. If more than 20% are flagged, regenerate once with a stricter instruction; if it still fails, return the `extractive` answer instead.
4. If a cited chunk is `repealed` and the answer carries no repeal note, append a deterministic warning naming the successor from `data/registry/statutes.yaml`.
5. `quote` must be a verbatim substring of the chunk text, checked in code, not trusted from the model.
6. Citation cards are built from metadata only. Model text never becomes a citation.
7. Confidence: `high` only when the evidence gate passed comfortably and the validator changed nothing; `low` when anything was removed or only one weak source survived.

### Abstention
Two gates: the retrieval evidence gate before the LLM, and the validator after it. An abstention says what was searched, what was missing, and which kind of source would answer the question — for example the relevant state's rules — and suggests a qualified professional where that fits. Never guess in order to avoid abstaining.

### High-stakes handling and refusals
- When `high_stakes` is true, answer from the sources as usual but lead with a short safety block: if anyone is in immediate danger, contact emergency services (112 in India); for arrest, detention, eviction or an imminent deadline, involve a lawyer or the legal services authority now. Beyond 112, include helpline numbers or addresses only when they appear in an ingested official source.
- Decline to help fabricate documents or evidence, evade lawful process, or target a specific person, and offer the lawful alternative instead — for example how to respond to a notice.
- Never present an uncertain or unsourced statement as settled law. Attribute an interpretation to the judgment that made it.

### Tests (`tests/unit/test_validator.py`)
Hand-written model outputs must prove that: an unknown `[S9]` is stripped; a case name absent from the context is removed; a citation to repealed law gains the warning; a non-verbatim quote is rejected; and a clean answer passes through unchanged.

## Related
- [Retrieval pipeline](../architecture/retrieval-pipeline.md) — prerequisite: the evidence gate and the S# map.
- [LLM layer](../architecture/llm-layer.md) — the generation step this contract constrains.
- [Statute status and repeal](statute-status.md) — source of the repeal warnings.
- [Chunk schema and provenance](../architecture/chunk-schema.md) — the fields citation cards are built from.
- [Evaluation](../ops/evaluation.md) — citation and abstention metrics.
