---
id: 20260922-report-validation
title: Validation of the research reports
tags: [data, legal, architecture]
created: 2026-09-22
updated: 2026-09-22
related: [20260922-data-sources, 20260922-minimum-viable-architecture, 20260922-chunk-schema, 20260922-statute-status, 20260925-deployment]
summary: Errors found in the two input reports and the correction adopted for each; read before reusing anything from them.
---

# Validation of the research reports

> Summary: Errors found in the two input reports and the correction adopted for each; read before reusing anything from them.

## Context
Reviewed on 2026-09-22: `docs/sources/research-report-1-data-manifest.md` (data manifest and blueprint) and `docs/sources/research-report-2-aws-blueprint.md` (AWS architecture blueprint). Method: every factual claim that would drive code, data or spend was checked against a primary or maintainer source. Evidence sits in `docs/DECISIONS.md`.

## Overall assessment: needs revision before use as build instructions
The direction is sound — India Code as the statute source, hybrid RAG, FAISS, local GPU work, provenance and licence tracking. The specifics contain legal-currency errors, one wrong and one placeholder case citation, sample code that doesn't run, a mismatched embedding model, and an AWS design sized for a different budget.

## Issues found

### High
1. **The architecture doesn't fit the budget** (report 2). It prototypes on OpenSearch Serverless and reaches for Kendra, SageMaker endpoints, MemoryDB or ElastiCache, VPC endpoints, WAF and MWAA. Its own "low-use" estimate is $50–100 per month, which exceeds the whole credit allowance. Correction: the minimum viable architecture note.
2. **Repealed law presented as current** (report 1). The CrPC 1973 is listed as a central Act of interest, with no model of repeal or commencement anywhere in the design. Correction: the statute registry and the temporal rule.
3. **A wrong citation and a placeholder one** (report 1). Indore Development Authority v. Manoharlal is dated 2023; the Constitution Bench decided it on 6 March 2020, reported at (2020) 8 SCC 129, and the 2023 dates belong to later orders applying it. "Rama Krishna Agarwal v. ..." is an incomplete placeholder rather than a citable case. Correction: seed cases are lookups resolved against dataset records, and ingestion rejects placeholder values.
4. **The chunking sample doesn't run as written.** `RecursiveCharacterTextSplitter(chunk_size=512, chunk_overlap=50, tokenizer=tokenizer)` passes an argument the constructor doesn't accept — the token-aware path is `from_huggingface_tokenizer` — the `langchain.text_splitter` import path is legacy, a GPT-2 tokenizer doesn't match the embedding model, and character windows ignore sections and paragraphs entirely. Correction: legal-aware chunking, and no LangChain.
5. **Embedding model mismatch.** `all-MiniLM-L6-v2` is English-only and truncates input at 256 word pieces, so with 512-token chunks the second half of every chunk would never be embedded, and Indic queries wouldn't work at all. Correction: bge-m3.
6. **Provenance discarded by design.** Chunks are written as `.txt` files in domain folders, and the index is `IndexFlatL2` with no ID map while the text describes cosine similarity. Correction: SQLite metadata plus `IndexIDMap2(IndexFlatIP)` over normalised vectors, with domain as a metadata field.
7. **Aalap used as a statute and FIR source.** The dataset is gated, English-only, partly synthetic — responses generated with GPT-4 and gpt-3.5-turbo — and licensed per source subset; the FIR material carries personal data. Correction: excluded from retrieval, usable only as inspiration for eval questions after human verification.

### Medium
8. **Indian Kanoon API as the default crawler.** It is a prepaid per-request API with its own terms. Verify what structural metadata it actually returns before designing around it. The free CC-BY Supreme Court dataset covers the MVP.
9. **`judis.nic.in` for Supreme Court judgments** — a legacy portal. Use the AWS Open Data dataset, which is sourced from eCourts.
10. **Unverified endpoint.** The Legislative Department DSpace bitstream pattern is asserted without evidence.
11. **Licensing oversimplified.** "Government texts are generally public domain" skips the conditions in s. 52(1)(q) of the Copyright Act and the editorial copyright that can attach to law reports.
12. **Textract and Comprehend for OCR and language detection.** Textract's documented languages exclude Indic scripts. Correction: local Tesseract and local language ID.
13. **Credits assumed to cover Bedrock.** Coverage of third-party models depends on the credit programme, and some charges route through AWS Marketplace. Correction: a billing check before anything depends on it.

### Low
14. Dated model references — Llama 2, `text-embedding-ada`, GPT4All. Choose current models at build time.
15. Routing on the local model's self-reported confidence is unreliable; route by task and retrieval evidence.
16. "NRCB" should read NCRB, which publishes crime statistics rather than FIR-filing procedure guides.
17. Formatting: the statutory-sources JSON is nested under the Aalap bullet, and the `landmark_cases` and `procedure_sources` fragments are not valid JSON on their own.

## Spot-checks (verified 2026-09-22, evidence in DECISIONS.md)
- Supreme Court dataset: bucket, ap-south-1, CC-BY-4.0, unsigned access, 1950–2025, per-year parquet metadata, English and regional PDFs.
- High Court dataset exists, covering 25 High Courts, and is very large.
- Indore Development Authority: 6 March 2020, (2020) 8 SCC 129.
- Aalap: gating, synthetic content, per-subset licensing.
- Indian Kanoon API pricing.
- Textract language list, from a dated AWS answer; re-check the quotas page.
- Copyright Act s. 52(1)(q)(ii) and (iv) wording.
- Claude Code memory behaviour for `CLAUDE.md` and `@path` imports.

## Required caveats
- Seed lists of Acts, cases and procedures are starting points. Every field shown to a user must come from the ingested source record.
- Licence and terms statements must be re-checked on the day of ingestion.
- Nothing here is legal advice.

## Related
- [Data sources](data-sources.md) — the corrected source registry.
- [Minimum viable architecture](../architecture/minimum-viable-architecture.md) — replacement for the blueprint.
- [Chunk schema and provenance](../architecture/chunk-schema.md) — replacement for the chunking and indexing samples.
- [Statute status and repeal](../legal/statute-status.md) — fix for the repealed-law issue.
- [Deployment](../ops/deployment.md) — AWS was dropped altogether on 2026-09-25 (DECISIONS D47).
