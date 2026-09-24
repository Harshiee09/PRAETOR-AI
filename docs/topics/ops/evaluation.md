---
id: 20260922-evaluation
title: Evaluation
tags: [evaluation, retrieval, legal]
created: 2026-09-22
updated: 2026-09-24
related: [20260922-retrieval-pipeline, 20260922-grounding-and-citations, 20260922-chunk-schema, 20260922-build-plan, 20260922-multilingual]
summary: Gold set format, metrics, data-profile gates and how to compare configurations honestly.
---

# Evaluation

> Summary: Gold set format, metrics, data-profile gates and how to compare configurations honestly.

## Context
"It answered my three test questions" is not evidence. A small human-verified gold set plus stage-level metrics tells us whether hybrid search, reranking, a model swap or Bedrock actually helps — and it gives the demo real numbers to show.

## Details

### Gold set (`evaluation/gold.jsonl`, one object per line)
```json
{"id": "reg-023-time-limit", "question": "How long do I have to present a sale deed for registration?",
 "language": "en", "domain": "property_land", "intent": "statute_lookup",
 "expected_sources": [{"act": "Registration Act, 1908", "section": "23"}],
 "must_mention": ["four months"], "should_abstain": false, "high_stakes": false,
 "verified_by": "name", "verified_on": "2026-09-24", "notes": "known-item check"}
```
- Aim for 40–60 questions by the end of Phase 2, and at least 10 in Phase 1: roughly 25 statute lookups and explanations, 8 procedures, 7 case-law questions, 5 criminal-code transition questions, at least 5 per non-English demo language, 5 out-of-corpus questions that must be abstained on, and 3 high-stakes ones.
- A person checks every expected source and `must_mention` item against the ingested text. A model may draft candidate questions; it never writes the expected answers.
- Freeze a `dev` split for tuning thresholds and a `test` split for reporting.
- Paraphrases of one question share a `group` and sit in one split; `load_gold` refuses a group split across dev and test (DECISIONS D38). A question traced by hand to design a fix moves to `dev`.
- Verification: `scripts/make_verification_sheet.py` writes `evaluation/verification_sheet.csv` (question, proposed expected sources, verbatim source excerpts and URLs, known uncertainties, blank reviewer columns). Only a person sets `verified_by` / `verified_on`.

### State of the gold set (2026-09-24, after the audit)
59 draft questions (54 answerable, 5 out-of-corpus), 30 dev / 29 test, 10 paraphrase groups; none verified by a person. Expected sources and `must_mention` phrases were copied from the ingested text; case-law items list acceptable alternatives with `"match": "any"`; the 5 Hindi phrasings need a Hindi speaker. Every question and the evidence threshold (DECISIONS D27) have been seen during development, and the D36 term expansions were chosen after seeing failures, so **all results on this set are exploratory**: a regression check, not a validated accuracy estimate. A validated number needs a fresh, frozen holdout written and verified by a person before it is run.

### Metrics (`praetor eval`, written to `evaluation/reports/<timestamp>.md` and `.json`)
| Area | Metric |
|---|---|
| Retrieval | Recall@5, Recall@10 and MRR for expected sources, as an ablation: dense, keyword, hybrid, hybrid plus rerank, plus exact lookup; "in context": expected sources among the `CONTEXT_MAX_CHUNKS` blocks the model sees (after the statute slots) |
| Reproducibility | each report's `run` block: git commit (and dirty flag), gold and registry hashes, index corpus hash, prompt version, model digest, decoding, retrieval settings; `scripts/repeat_answers.py` for run-to-run variation |
| Citations | invalid citations after validation, which must be 0; share of answers with at least one citation; unverified-authority removals; unsupported-sentence flags |
| Abstention | precision and recall against `should_abstain` |
| Legal currency | share of transition questions carrying a correct regime note |
| Language | every metric above, sliced by query language |
| Ops | p50 and p95 latency per stage, tokens and dollars per query, cache hit rate |
| Optional | LLM-as-judge groundedness on a sample, reported as indicative only and never used as a gate |

### Gates (starting targets — adjust after the first run and record why)
- Phase 1: the known-item statute questions answer with the right section cited, and the corpus profile is all green.
- Phase 2: hybrid plus rerank beats dense-only on Recall@5; Recall@5 of at least 0.8 on statute lookups; zero invalid citations; at least 4 of 5 out-of-corpus questions abstained.
- Phase 4: the scripted demo passes end to end from a fresh clone.

### Comparing configurations honestly
Use the same questions for every configuration, and report `n` next to every percentage. Don't cherry-pick examples for the demo narrative. Note small-sample uncertainty: 40 questions cannot separate two close configurations, so say so rather than claiming a winner. Tune thresholds on `dev` and report on `test`. If a result looks too good, trace a few individual questions by hand before believing it.

## Related
- [Retrieval pipeline](../architecture/retrieval-pipeline.md) — the stages the ablation measures.
- [Grounding and citations](../legal/grounding-and-citations.md) — the citation and abstention rules being measured.
- [Chunk schema and provenance](../architecture/chunk-schema.md) — the corpus profile gate.
- [3-day build plan](build-plan.md) — which gate applies in which phase.
- [Multilingual strategy](../data/multilingual.md) — per-language evaluation.
