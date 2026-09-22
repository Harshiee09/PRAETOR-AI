---
id: 20260922-chunk-schema
title: Chunk schema and provenance
tags: [schema, data, architecture]
created: 2026-09-22
updated: 2026-09-22
related: [20260922-minimum-viable-architecture, 20260922-retrieval-pipeline, 20260922-grounding-and-citations, 20260922-statute-status, 20260922-multilingual, 20260922-evaluation]
summary: Storage layout, required provenance fields, parsing and legal-aware chunking rules, and ingestion validation.
---

# Chunk schema and provenance

> Summary: Storage layout, required provenance fields, parsing and legal-aware chunking rules, and ingestion validation.

## Context
Citations are rendered from this metadata, so a missing field becomes a missing or wrong citation. Provenance is a hard gate at ingestion, not a nice-to-have. This also replaces the reports' "text files in domain folders" approach: a domain is a metadata field, and one document can carry several.

## Details

### Storage layout
```text
data/raw/<source>/...              original files, never modified
data/raw/manifest.jsonl            one row per file: source, url, local path, sha256, bytes, retrieved_at, licence
data/registry/sources.yaml         seed corpus: what to fetch, its domain tags, and the verified source URL
data/processed/praetor.sqlite      documents, chunks, chunks_fts (FTS5, external content), ingest_runs, cache, spend
data/indexes/faiss.index           IndexIDMap2(IndexFlatIP); the FAISS id is chunks.rowid
data/indexes/index_manifest.json   embed model, dimension, normalised flag, chunk count, corpus hash, created_at
```
The API refuses to start when `index_manifest.json` disagrees with the configured embedding model or dimension.

### Document fields (`documents`)
`doc_id` (stable: sha256 of the canonical source URL or S3 key), `doc_type` (`statute`, `judgment`, `procedure` or `form`), `title`, `source_name`, `source_url`, `licence`, `retrieved_at`, `raw_path`, `raw_sha256`, `authority` (for example Parliament of India, Supreme Court of India), `jurisdiction` (`IN` for central law, ISO 3166-2 codes such as `IN-TN` or `IN-MH` for states), `language`, `script`, `is_translation`, `translation_of`, `parser_version`.

### Chunk fields (`chunks`)
Required for every chunk:
| Field | Notes |
|---|---|
| `chunk_id` | `{doc_id[:12]}:{locator_slug}:{sha1(text)[:8]}`, stable across re-runs when the text is unchanged |
| `doc_id`, `doc_type`, `title` | copied from the document so filters stay on one table |
| `source_name`, `source_url`, `licence`, `retrieved_at` | the provenance shown in citations |
| `authority`, `jurisdiction` | who issued it, and where it applies |
| `language`, `script` | BCP-47 primary tag (`en`, `hi`, `ta`, `brx`, `sat`) and ISO 15924 script (`Latn`, `Deva`, `Taml`, `Olck`) |
| `locator` | human-readable position: `s. 23`, `s. 17(1)(b)`, `paras 12-15`, `p. 4` |
| `page_start`, `page_end` | PDF pages; null for HTML |
| `text` | cleaned text shown to users and quoted in citations |
| `embed_text` | metadata header plus text; this is what gets embedded and keyword-indexed |
| `token_count` | measured with the embedding model's tokenizer |
| `status` | statutes: `in_force`, `repealed`, `partially_in_force` or `unknown`, from `data/registry/statutes.yaml`; other types: `n/a` |
| `domain_tags` | JSON list, for example `["property_land", "registration"]` |
| `text_source`, `ocr_confidence` | `layer` or `ocr`, and the mean OCR confidence when OCR was used |

Statute chunks also require `act_title`, `act_year`, `section` and `section_heading`; optionally `act_number`, `part`, `chapter`, `subsection`, `amendment_notes` (a JSON list parsed from footnotes) and `successor`.

Judgment chunks also require `case_title`, `court` and `decision_date` (ISO date); optionally `judges`, `case_number`, `citation` (the neutral or reporter citation exactly as printed in the source record), `para_start`, `para_end`, `disposal_nature` and `cnr`.

Procedure and form chunks also require `issuing_body` and `valid_as_of`; optionally `service_name` and `step_range`.

### Parsing rules
- Use the PDF text layer when it is usable. OCR a page when it holds fewer than about 50 non-space characters, or when too few characters belong to the expected script: many older Hindi and other Indic government PDFs use legacy non-Unicode fonts whose text layer extracts as Latin gibberish. OCR those pages instead of indexing garbage.
- Record per page whether text came from the layer or from OCR, the OCR confidence, and the page number.
- HTML: keep headings and list structure, drop navigation and boilerplate.
- Strip running headers and footers that repeat across pages.

### Legal-aware chunking
- **Statutes (India Code bare acts).** One chunk per section, including its sub-sections, provisos, Explanations and Illustrations. Section starts look like `23. Time for presenting documents.—`, and inserted sections carry a footnote marker and bracket, like `1[23A. ...`. Build the detector against real India Code PDFs rather than from memory, and cover it with fixture tests. When a section exceeds `MAX_CHUNK_TOKENS`, split at sub-section and then clause boundaries, never mid-sentence, repeating the header in each piece (`... s. 17 (part 2 of 3)`).
- **Amendment footnotes.** India Code PDFs record amendment history in small-font footnotes (`Subs. by Act ...`, `Ins. by ...`, `Omitted by ...`). Capture them per page — pdfplumber exposes font size — into `amendment_notes`. Best effort only; don't block Phase 1 on linking footnotes to sections.
- **Judgments.** The first chunk is the case header: parties, bench, date. Split on numbered paragraphs (lines starting `12.`), group consecutive paragraphs up to `MAX_CHUNK_TOKENS`, and record `para_start` and `para_end`. Never split a paragraph unless it alone is too long.
- **Procedures and forms.** Split by headings and numbered steps.
- **Headers come from metadata, never from an LLM.** Example header inside `embed_text`: `Registration Act, 1908 > Part IV > s. 23 — Time for presenting documents`.
- No fixed-size character windows, and no GPT-2 tokenizer: token counts use the bge-m3 tokenizer.

### Ingestion validation: reject, don't warn
- A required field that is null or empty rejects the chunk; log the `doc_id` and the field.
- Placeholder or impossible values reject the chunk: `...`, `TBD`, `N/A`, `example`, a party name of `...`, future dates, or a Supreme Court `decision_date` before 28 January 1950.
- `source_url` must start with `https://` or `s3://`.
- Duplicate `(doc_id, sha1(text))` pairs keep one row.
- Re-running ingestion over unchanged sources must add zero rows. Cover this with an idempotency test.

### Corpus profile (`praetor profile`, written to `docs/reports/corpus_profile.md`)
Apply the explore-data checklist to the chunk store: row counts by `doc_type` by `language` by domain tag; the null or empty rate per field with a completeness grade (above 99% green, 95–99% yellow, 80–95% orange, below 80% red); duplicate hashes; token count p5, p50, p95 and max; OCR share and mean confidence; `status` distribution; the top 10 and bottom 5 values of each categorical field, where junk tends to show up; and the oldest and newest `decision_date`. The Phase 1 gate is every required field green.

## Related
- [Minimum viable architecture](minimum-viable-architecture.md) — context: where this storage sits in the ingestion flow.
- [Retrieval pipeline](retrieval-pipeline.md) — consumer: filters and context headers read these fields.
- [Grounding and citations](../legal/grounding-and-citations.md) — consumer: citation cards are rendered from these fields.
- [Statute status and repeal](../legal/statute-status.md) — source of the `status` field.
- [Multilingual strategy](../data/multilingual.md) — source of `language`, `script` and the OCR rules.
- [Evaluation](../ops/evaluation.md) — the corpus profile is an evaluation gate.
