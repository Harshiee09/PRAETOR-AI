---
id: 20260922-multilingual
title: Multilingual strategy
tags: [multilingual, data]
created: 2026-09-22
updated: 2026-09-22
related: [20260922-retrieval-pipeline, 20260922-chunk-schema, 20260922-statute-status, 20260922-evaluation]
summary: "One pipeline for all 22 scheduled languages: registry, detection, normalisation, retrieval and translation."
---

# Multilingual strategy

> Summary: One pipeline for all 22 scheduled languages: registry, detection, normalisation, retrieval and translation.

## Context
The design has to extend to all 22 languages of the Eighth Schedule without becoming 22 pipelines. Per-language behaviour lives in a registry, not in code branches. The 3-day demo covers English, Hindi and one more language of the team's choosing.

## Details

### Language registry (`app/multilingual/languages.yaml`)
Seed table below. Fill `tesseract` from `tesseract --list-langs` on the dev machine, and `lid` from the language-ID model's own label set. Don't assume either.

| code | language | scripts (ISO 15924) |
|---|---|---|
| as | Assamese | Beng |
| bn | Bengali | Beng |
| brx | Bodo | Deva |
| doi | Dogri | Deva |
| gu | Gujarati | Gujr |
| hi | Hindi | Deva |
| kn | Kannada | Knda |
| ks | Kashmiri | Arab, Deva |
| kok | Konkani | Deva, also Latn and Knda |
| mai | Maithili | Deva |
| ml | Malayalam | Mlym |
| mni | Manipuri (Meitei) | Mtei, Beng |
| mr | Marathi | Deva |
| ne | Nepali | Deva |
| or | Odia | Orya |
| pa | Punjabi | Guru |
| sa | Sanskrit | Deva |
| sat | Santali | Olck |
| sd | Sindhi | Arab, Deva |
| ta | Tamil | Taml |
| te | Telugu | Telu |
| ur | Urdu | Arab |

Each entry also carries `name_native`, `tesseract` (traineddata code or null), `lid` (supported or not), `translation` (which engine, if any) and `demo_enabled`.

### Detection
1. Script first, by Unicode property through the `regex` module (for example `\p{Script=Devanagari}`), per chunk and per query. Deterministic and fast.
2. Language within a script, using a statistical model such as fastText lid.176 or GlotLID — check that it covers your demo languages. Low confidence yields `und-<Script>`, for instance `und-Deva`: retrieval still works, and the answer doesn't claim a language it isn't sure of.
3. Romanised and code-mixed input is common. For the MVP, treat Latin-script queries as English for keyword search and lean on dense retrieval, and note it as a limitation. The upgrade path is AI4Bharat IndicLID, which handles native and romanised Indic input.

### Normalisation
Always NFC. For search keys only, remove ZWJ and ZWNJ and normalise nukta and similar variants; indic-nlp-library's normalisers are one option. Display text is never altered.

### OCR
Tesseract with the needed traineddata at 300 DPI, recording confidence per page. Scripts with no model available — likely Ol Chiki and Meetei Mayek, so confirm locally — are marked `ocr: unsupported` so ingestion reports them instead of producing garbage. See the parsing rules in the chunk-schema note for legacy non-Unicode font detection, which matters most for older Hindi PDFs.

### Retrieval and generation
- bge-m3 is cross-lingual, so a Hindi query can retrieve English statute text and the reverse.
- Keyword search needs same-language terms, so non-English queries get an English rewrite.
- Generate the answer in the user's language when the configured model handles it acceptably; check this on the eval set, since hosted models are usually stronger than small local ones for Indic languages. Quotes stay in the source language, and translations are labelled unofficial.
- The upgrade path to all 22 languages is AI4Bharat IndicTrans2, which covers every scheduled language, run locally for query and answer translation. Check its licence and VRAM needs first.

### Demo target
A Hindi question retrieves English Act text, and Hindi text where it has been ingested, then answers in Hindi with citations pointing at the original sources. The gold set carries at least five queries per demo language.

## Related
- [Retrieval pipeline](../architecture/retrieval-pipeline.md) — where detection and English rewrites are used.
- [Chunk schema and provenance](../architecture/chunk-schema.md) — the `language` and `script` fields and the OCR flags.
- [Statute status and repeal](../legal/statute-status.md) — authoritative text versus translation.
- [Evaluation](../ops/evaluation.md) — per-language slices of the metrics.
