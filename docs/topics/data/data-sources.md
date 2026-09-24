---
id: 20260922-data-sources
title: Data sources
tags: [data, licensing]
created: 2026-09-22
updated: 2026-09-24
related: [20260922-report-validation, 20260922-chunk-schema, 20260922-statute-status, 20260922-multilingual, 20260922-aws-cost-plan]
summary: Verified source registry, licences and terms, the MVP seed corpus and download etiquette.
---

# Data sources

> Summary: Verified source registry, licences and terms, the MVP seed corpus and download etiquette.

## Context
Status legend: **OK** verified on 2026-09-22, with evidence in DECISIONS.md; **CHECK** verify before building against it; **NO** don't use as a retrieval source. Re-check licences and terms on the day you ingest, and record `licence` per document.

## Details

### Registry
| Source | Use | Access | Licence and terms | Status |
|---|---|---|---|---|
| India Code (`indiacode.gov.in`, moved from `indiacode.nic.in`) | central Acts: bare text, and Hindi versions where published | DSpace 9.1 REST API at `/server/api` (items, bundles, bitstream PDFs with MD5); IDs in `sources.yaml` (DECISIONS V11, V12) | government text, see licensing notes | OK as the authority and the access path; CHECK site terms (V15) |
| Indian Supreme Court Judgments, AWS Open Data (`s3://indian-supreme-court-judgments`, ap-south-1) | SC judgments 1950–2025, English and regional PDFs, per-year metadata parquet | `aws s3 ... --no-sign-request`, no AWS account needed | CC-BY-4.0, attribution required | OK |
| Indian High Court Judgments, AWS Open Data (`s3://indian-high-court-judgments`) | 25 High Courts, raw JSON and parquet metadata | same | CC-BY-4.0, confirm on the registry page | OK, but stretch only: roughly 17.8M judgments and 1.25 TiB |
| OpenNyAI InJudgements (`opennyaiorg/InJudgements_dataset`) | about 12k judgments with domain labels | Hugging Face `datasets` | report claims Apache-2.0; read the card | CHECK, optional, overlaps the SC dataset |
| OpenNyAI InRhetoricalRoles, InLegalNER, `en_legal_ner_trf` | enrichment: rhetorical roles and legal NER, not retrieval | Hugging Face | read each card | CHECK, post-MVP |
| Aalap instruction dataset | — | gated: login and accepted terms | a compilation, licensed per subset | NO: English-only, partly GPT-generated, and not a source of law |
| FIR texts bundled in Aalap | — | — | — | NO: personal data, and not needed |
| Indian Kanoon API | optional extra search and metadata | prepaid per request: about ₹0.50 per search, ₹0.20 per document, ₹500 free on signup, ₹10,000 monthly for verified non-commercial use | its own terms, including attribution | CHECK, optional, not needed for the MVP |
| Legislative Department (`legislative.gov.in`) | secondary source for Acts | the report claims a DSpace bitstream API; unverified | government text | CHECK before coding against it |
| Citizen charters, e-District procedure pages, legal-services forms | procedure and checklist chunks | manual curation, one URL per document | government text | CHECK: state-specific, record `issuing_body` and `valid_as_of` |
| PRS India, BareActsLive and similar | summaries and analysis | web | third-party | NO as a primary source of law |

### Licensing notes (not legal advice; get counsel before a public launch)
- Section 52(1)(q) of the Copyright Act, 1957 makes it non-infringing to reproduce judgments and orders of courts unless the court prohibits it, and to reproduce an Act when it is published together with commentary or other original matter.
- Editorial additions in law reports — headnotes, editor-inserted paragraphing, cross-references — can carry their own copyright (Eastern Book Company v. D.B. Modak, Supreme Court, 2007). Use court-published copies rather than SCC, AIR or Manupatra editions.
- CC-BY-4.0 datasets need visible attribution: in the README and in an "about the data" field of the API. For example: "Indian Supreme Court Judgments, accessed <date> from registry.opendata.aws/indian-supreme-court-judgments".
- Keep each source's licence text in `data/raw/<source>/LICENSE` and the licence name in the manifest row.

### MVP seed corpus (`data/registry/sources.yaml`)
Acts in English from India Code, grouped by demo domain:
| Domain | Acts |
|---|---|
| Property and land | Transfer of Property Act 1882 · Registration Act 1908 · RFCTLARR Act 2013 · Real Estate (Regulation and Development) Act 2016 · Limitation Act 1963 |
| Contract and civil | Indian Contract Act 1872 · Specific Relief Act 1963 · Code of Civil Procedure 1908 |
| Consumer | Consumer Protection Act 2019 |
| Criminal procedure, for transition questions | BNSS 2023 · CrPC 1973, repealed but retained |
| Constitutional, optional | Constitution of India |

Add the Hindi text of one or two of these Acts, where India Code publishes it, for the multilingual demo. Phase 1 uses only three Acts: the Registration Act, the Transfer of Property Act, and the Consumer Protection Act 2019.

Judgments come from the SC dataset, selected through the per-year metadata parquet rather than by downloading whole years blindly, since a single year's English archive can run to several GB. Phase 1 takes about 50 judgments; Phase 2 takes 300–1,000 filtered to the demo domains by title and Act mentions across recent years, plus regional-language versions of a few for the multilingual demo. Individual PDF downloads are fine for a few hundred files; for bulk, use the tar archives, as the dataset maintainers ask.

**As ingested (2026-09-24, DECISIONS D18):** 12 Acts (Registration, TPA, CPA 2019, RFCTLARR, RERA, Limitation, Contract, Specific Relief, CPC, BNSS, BNS, BSA; the CrPC is not available in current form, V23; the Constitution was skipped as optional) and 1,000 judgments 2016–2025, selected by headnote Act mentions round-robin across Acts (including judgments under repealed Acts), extracted from the English year tars. Hindi Act texts and regional-language judgments are not yet ingested (Phase 4 multilingual demo).

**Source comparison, 2026-09-24 audit (DECISIONS D42, V29–V36).** Nothing new was ingested:
| Text | Compared | Outcome |
|---|---|---|
| BNSS ss. 482, 531 | indexed India Code copy vs Gazette of India CG-DL-E-25122023-250884 (MHA copy); legacy nic.in copies returned 504 | identical apart from marginal headings: keep |
| TPA s. 106 | indexed copy vs legacy nic.in `A1882-04.pdf` (same MD5) vs legacy `tpa.pdf` | `tpa.pdf` prints the pre-2003 section: rejected as stale |
| RERA s. 18 | indexed copy vs legacy nic.in `A201616.pdf` | identical; both include the 2026 amendment of s. 68: keep |
| CrPC 1973 | India Code central repeal-register scan (as enacted), Chandigarh and Punjab items, SCLSC copy; legacy nic.in copy returned 504; Legislative Department page rendered nothing | none is the text as in force on 30 June 2024 (no s. 438(4), which the Supreme Court describes in 2024): not ingested |
| Hindi TPA, Hindi BNSS | India Code `H1882-04.pdf`, `202346.pdf` | broken font mapping / no text layer; needs OCR (Tesseract not installed): not ingested |
| State rent law | — | the eviction question names no state; not guessed |

Legacy `indiacode.nic.in` handle numbers do not resolve on `indiacode.gov.in`; find items through the new API rather than the old URLs.

Landmark cases to locate in the dataset. These are lookups, not facts: every field shown to a user comes from the dataset record, and if a case can't be found, report that rather than inventing it.
| Case | Decided | Why it's in the seed |
|---|---|---|
| Kesavananda Bharati v. State of Kerala | 1973 | basic structure doctrine |
| I.C. Golaknath v. State of Punjab | 1967 | amendment of fundamental rights; later overruled on that point by Kesavananda Bharati |
| Minerva Mills v. Union of India | 1980 | basic structure reaffirmed, parts of the 42nd Amendment struck down |
| Indore Development Authority v. Manoharlal | 6 March 2020, (2020) 8 SCC 129 | s. 24(2) RFCTLARR lapse conditions; overruled Pune Municipal Corporation (2014). The report's "2023" is wrong |

### Download etiquette
Identify the client through `HTTP_USER_AGENT` with a contact address, keep to about one request per second on government sites, cache everything with its sha256, resume rather than re-download, and never bypass logins, captchas or robots rules. If a source blocks automated access, stop and ask for the file.

## Related
- [Validation of the research reports](report-validation.md) — why several sources from the reports were dropped.
- [Chunk schema and provenance](../architecture/chunk-schema.md) — the manifest and provenance fields each source must fill.
- [Statute status and repeal](../legal/statute-status.md) — status for the seed Acts.
- [Multilingual strategy](multilingual.md) — regional-language versions and OCR.
- [AWS plan and cost controls](../ops/aws-cost-plan.md) — reading the open-data bucket costs nothing.
