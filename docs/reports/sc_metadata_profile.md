# SC judgments metadata profile

_Generated 2026-09-22T22:36:52+00:00 from `metadata/parquet/year=YYYY/metadata.parquet`, years 2016–2025._

**Rows:** 7997 · **Columns:** 18

| year | rows |
|---|---|
| 2016 | 588 |
| 2017 | 733 |
| 2018 | 794 |
| 2019 | 1051 |
| 2020 | 571 |
| 2021 | 708 |
| 2022 | 1017 |
| 2023 | 856 |
| 2024 | 782 |
| 2025 | 897 |

| column | dtype | null or empty | distinct | example |
|---|---|---|---|---|
| `title` | string | 0.0% | 7923 | NABAM REBIA, AND BAMANG FELIX versus DEPUTY SPEAKER AND OTHE |
| `petitioner` | string | 0.2% | 7004 | NABAM REBIA, AND BAMANG FELIX |
| `respondent` | string | 0.2% | 5674 | DEPUTY SPEAKER AND OTHERS |
| `description` | string | 88.5% | 919 |  |
| `judge` | string | 0.1% | 429 | J.S. KHEHAR |
| `author_judge` | object | 100.0% | 0 |  |
| `citation` | string | 0.0% | 7995 | [2016] 6 S.C.R. 1 |
| `case_id` | string | 0.8% | 7853 | 2016 INSC 526 |
| `cnr` | string | 0.0% | 7995 | ESCR010004292016 |
| `decision_date` | string | 0.0% | 1840 | 13-07-2016 |
| `disposal_nature` | string | 3.0% | 25 | Appeal(s) allowed |
| `court` | string | 0.0% | 1 | Supreme Court of India |
| `available_languages` | string | 11.5% | 104 | ENG,HIN,PUN |
| `raw_html` | string | 0.0% | 7997 |  |
| `path` | string | 0.0% | 7995 | 2016_6_1_294 |
| `nc_display` | string | 0.8% | 7853 | 2016INSC526 |
| `scraped_at` | string | 0.0% | 7997 | 2025-06-12T21:50:55.239007 |
| `year` | string | 0.0% | 10 | 2016 |

## Checks
- `decision_date` unparseable (expected DD-MM-YYYY): 0
- `decision_date` range: 2015-10-07 to 2025-12-12
- `decision_date` before 1950-01-28 or in the future: 0
- duplicate `cnr`: 2 · duplicate `path`: 2
- rows with English available (`ENG` in `available_languages`): 7077

## Top values

**disposal_nature**: Appeal(s) allowed (3383); Dismissed (1905); Disposed off (1472); Case Partly allowed (441); (empty) (239); Directions issued (215); Case Allowed (78); Matter referred to larger bench (67)

**available_languages**: ENG,HIN,PUN (4844); (empty) (920); ENG,PUN (500); ENG,HIN,PUN,TAM (359); ENG,GUJ,HIN,PUN (230); ENG,HIN,PUN,TEL (151); ENG,HIN,MAL,PUN (113); ENG,HIN,MAR,PUN (112)

**court**: Supreme Court of India (7997)

## Notes
- `raw_html` holds the listing card: coram (author marked `*`) and the Editorial Section's headnotes. Headnotes are used only to select judgments, never indexed.
- `author_judge` is always empty and `description` mostly empty; the bench and author come from the coram in `raw_html`.
- Rows with empty `available_languages` are excluded from selection (English availability unknown).
