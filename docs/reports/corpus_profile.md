# Corpus profile

_Generated 2026-09-22T23:14:52+00:00 by `praetor profile` from `data/processed/praetor.sqlite`._

**Documents:** 53 · **Chunks:** 1887

## Chunks by type, language and domain tag

| doc_type | language | domain tag | chunks |
|---|---|---|---|
| judgment | en | case_law | 1321 |
| judgment | en | consumer | 288 |
| judgment | en | contract_civil | 545 |
| judgment | en | property_land | 1033 |
| judgment | en | registration | 514 |
| statute | en | consumer | 137 |
| statute | en | contract_civil | 169 |
| statute | en | property_land | 429 |
| statute | en | registration | 260 |

## Required-field completeness

| doc_type | field | filled | grade |
|---|---|---|---|
| statute | `chunk_id` | 100.0% | green |
| statute | `doc_id` | 100.0% | green |
| statute | `doc_type` | 100.0% | green |
| statute | `title` | 100.0% | green |
| statute | `source_name` | 100.0% | green |
| statute | `source_url` | 100.0% | green |
| statute | `licence` | 100.0% | green |
| statute | `retrieved_at` | 100.0% | green |
| statute | `authority` | 100.0% | green |
| statute | `jurisdiction` | 100.0% | green |
| statute | `language` | 100.0% | green |
| statute | `script` | 100.0% | green |
| statute | `locator` | 100.0% | green |
| statute | `text` | 100.0% | green |
| statute | `embed_text` | 100.0% | green |
| statute | `token_count` | 100.0% | green |
| statute | `status` | 100.0% | green |
| statute | `domain_tags` | 100.0% | green |
| statute | `text_source` | 100.0% | green |
| statute | `act_title` | 100.0% | green |
| statute | `act_year` | 100.0% | green |
| statute | `section` | 100.0% | green |
| statute | `section_heading` | 100.0% | green |
| judgment | `chunk_id` | 100.0% | green |
| judgment | `doc_id` | 100.0% | green |
| judgment | `doc_type` | 100.0% | green |
| judgment | `title` | 100.0% | green |
| judgment | `source_name` | 100.0% | green |
| judgment | `source_url` | 100.0% | green |
| judgment | `licence` | 100.0% | green |
| judgment | `retrieved_at` | 100.0% | green |
| judgment | `authority` | 100.0% | green |
| judgment | `jurisdiction` | 100.0% | green |
| judgment | `language` | 100.0% | green |
| judgment | `script` | 100.0% | green |
| judgment | `locator` | 100.0% | green |
| judgment | `text` | 100.0% | green |
| judgment | `embed_text` | 100.0% | green |
| judgment | `token_count` | 100.0% | green |
| judgment | `status` | 100.0% | green |
| judgment | `domain_tags` | 100.0% | green |
| judgment | `text_source` | 100.0% | green |
| judgment | `case_title` | 100.0% | green |
| judgment | `court` | 100.0% | green |
| judgment | `decision_date` | 100.0% | green |

## Optional fields (filled share)

| doc_type | field | filled |
|---|---|---|
| statute | `act_number` | 100.0% |
| statute | `part` | 45.8% |
| statute | `chapter` | 53.7% |
| statute | `amendment_notes` | 20.7% |
| statute | `page_start` | 100.0% |
| judgment | `judges` | 98.9% |
| judgment | `citation` | 100.0% |
| judgment | `para_start` | 68.9% |
| judgment | `disposal_nature` | 100.0% |
| judgment | `cnr` | 100.0% |
| judgment | `page_start` | 96.2% |

## Tokens, duplicates, OCR, status

- `token_count` (bge-m3 tokenizer): p5 57, p50 298, p95 442, max 734; over MAX_CHUNK_TOKENS=450: 1
- duplicate `(doc_id, sha1(text))`: 0 · identical text across documents: 0
- text_source: layer 1837, metadata 50
- OCR share: 0.0%; mean OCR confidence: n/a
- status: n/a 1321, in_force 566
- `decision_date`: oldest 2016-10-26, newest 2025-02-02, unparseable 0
- judgment locators: header 50, by paragraph 910, by page 361

## Categorical values (top 10 / bottom 5)

- **doc_type** (2 values): top: judgment (1321); statute (566) · bottom: —
- **title** (53 values): top: Registration Act, 1908 (260); Transfer of Property Act, 1882 (169); Consumer Protection Act, 2019 (137); NEENA ANEJA & ANR. versus JAI PRAKASH ASSOCIATES L (107); VEENA SINGH (DEAD) THROUGH LR versus THE DISTRICT  (75); MANIK MAJUMDER AND OTHERS versus DIPAK KUMAR SAHA  (67); THE SUB REGISTRAR, AMUDALAVALASA & ANR. versus M/S (60); UNION OF INDIA & ANR. versus S. NARASIMHULU NAIDU  (51); SATYA PAL ANAND versus STATE OF M.P. & ORS. (47); SMT. M. HEMALATHA DEVI & ORS. versus B. UDAYASRI (45) · bottom: VITHAL TUKARAM KADAM AND ANOTHER versus VAMANRAO S (10); SMT. BAYANABAI KAWARE versus RAJENDRA S/O BABURAO  (8); RICARDO CONSTRUCTIONS PVT. LTD. versus RAVI KUCKIA (7); KUMUD W/O MAHADEORAO SALUNKE versus SHRI PANDURANG (7); S. SAROJINI AMMA versus VELAYUDHAN PILLAI SREEKUMA (7)
- **source_name** (2 values): top: Indian Supreme Court Judgments (AWS Open Data) (1321); India Code (566) · bottom: —
- **licence** (2 values): top: CC-BY-4.0 (1321); Government of India legislative text published on  (566) · bottom: —
- **authority** (2 values): top: Supreme Court of India (1321); Parliament of India (566) · bottom: —
- **jurisdiction** (13 values): top: IN (1730); IN-OD (28); IN-KA (23); IN-UK (23); IN-KL (21); IN-UP (18); IN-TR (15); IN-RJ (9); IN-GJ (7); IN-HP (6) · bottom: IN-GJ (7); IN-HP (6); IN-AS (3); IN-HR (3); IN-WB (1)
- **language** (1 values): top: en (1887) · bottom: —
- **script** (1 values): top: Latn (1887) · bottom: —
- **status** (2 values): top: n/a (1321); in_force (566) · bottom: —
- **text_source** (2 values): top: layer (1837); metadata (50) · bottom: —
- **act_title** (4 values): top: (null) (1321); Registration Act, 1908 (260); Transfer of Property Act, 1882 (169); Consumer Protection Act, 2019 (137) · bottom: —
- **part** (16 values): top: (null) (1628); Part XI — Of the Duites and Powers of Registering  (80); Part III — Of Registrable Documents (29); Part XV — Miscellaneous (25); Part II — Of the Registration-establishment (23); Part XIII — Of the Fees for Registration, Searches (21); Part XIV — Of Penalties (14); Part VI — Of Presenting Documents for Registration (13); Part IX — Of the Deposit of Wills (13); Part V — Of the Place of Registration (11) · bottom: Part IV — Of the Time of Presentation (7); Part I — Preliminary (5); Part VII — Of Enforcing the Appearance of Executan (4); Part X — Of the Effects of Registration and Non-re (4); Part VIII — Of Presenting Wills and Authorities to (2)
- **chapter** (15 values): top: (null) (1583); Chapter IV (60); Chapter IV — Consumer Disputer Redressal Commissio (54); Chapter II — Of Transfers of Property by Act of Pa (52); Chapter I — Preliminary (21); Chapter VII — Of Gifts (20); Chapter III — Central Consumer Protection Authorit (20); Chapter VIII — Miscellaneous (20); Chapter V — Of Leases of Immoveable Property (17); Chapter III — Of Sales of Immoveable Property (9) · bottom: Chapter V — Mediation (8); Chapter II — Consumer Protection Councils (7); Chapter VI — Product Liability (6); Chapter VII — Offences and Penalties (6); Chapter VI — Of Exchanges (4)
- **court** (2 values): top: Supreme Court of India (1321); (null) (566) · bottom: —
- **disposal_nature** (8 values): top: Appeal(s) allowed (579); (null) (566); Dismissed (368); Case Partly allowed (147); Disposed off (142); Matter referred to larger bench (67); Case Allowed (11); Leave Granted & Allowed (7) · bottom: —

## Per-document parse checks

| type | title | checks |
|---|---|---|
| judgment | A.B. GOVARDHAN versus P. RAGOTHAMAN | pages 22, units 63 (62 numbered), opinions 1, unusable pages [] |
| judgment | AMEER MINHAJ versus DIERDRE ELIZABETH (WRIGHT) ISSAR AND ORS | pages 11, units 20 (19 numbered), opinions 1, unusable pages [] |
| judgment | ANAPURNA JAISWAL versus INDIAN OIL CORPORATION LTD. AND ORS. | pages 10, units 23 (22 numbered), opinions 1, unusable pages [] |
| judgment | APPAIYA versus ANDIMUTHU @ THANGAPANDI & ORS. | pages 20, units 40 (39 numbered), opinions 1, unusable pages [] |
| judgment | BAINI PRASAD (D) THR. LRS. versus DURGA DEVI | pages 19, units 29 (28 numbered), opinions 1, unusable pages [] |
| judgment | BHIMRAO RAMCHANDRA KHALATE (DECEASED) THROUGH LRS. versus NA | pages 16, units 36 (35 numbered), opinions 1, unusable pages [] |
| judgment | BRIGADE ENTERPRISES LIMITED versus ANIL KUMAR VIRMANI & ORS. | pages 24, units 50 (49 numbered), opinions 1, unusable pages [] |
| judgment | CHANDER BHAN (D) THROUGH LR SHER SINGH versus MUKHTIAR SINGH | pages 11, units 35 (34 numbered), opinions 1, unusable pages [] |
| judgment | DR. S. KUMAR & ORS. versus S. RAMALINGAM | pages 10, units 25 (24 numbered), opinions 1, unusable pages [] |
| judgment | DUNI CHAND versus VIKRAM SINGH AND OTHERS | pages 9, units 23 (22 numbered), opinions 1, unusable pages [] |
| judgment | EIH LIMITED versus NADIAVIRJI | pages 16, units 34 (33 numbered), opinions 1, unusable pages [] |
| judgment | GODREJ PROJECTS DEVELOPMENT LIMITED versus ANIL KARLEKAR & O | pages 20, units 74 (73 numbered), opinions 1, unusable pages [] |
| judgment | GURCHARAN SINGH & ORS. versus ANGREZ KAUR & ANR. | pages 17, units 33 (32 numbered), opinions 1, unusable pages [] |
| judgment | INFRASTRUCTURE LEASING AND FINANCIAL SERVICES LTD versus HDF | pages 25, units 65 (64 numbered), opinions 1, unusable pages [] |
| judgment | K. ARUMUGA VELAIAH versus P.R. RAMASAMY AND ANR. | pages 32, units 69 (68 numbered), opinions 1, unusable pages [] |
| judgment | KAUSHIK NARSINHBHAI PATEL & ORS. versus M/S S.J.R. PRIME COR | pages 17, units 28 (27 numbered), opinions 1, unusable pages [] |
| judgment | KORUKONDA CHALAPATHI RAO & ANR. versus KORUKONDA ANNAPURNA S | pages 24, units 66 (65 numbered), opinions 1, unusable pages [] |
| judgment | KUMUD W/O MAHADEORAO SALUNKE versus SHRI PANDURANG NARAYAN G | pages 6, units 16 (15 numbered), opinions 1, unusable pages [] |
| judgment | M/S TEXCO MARKETING PVT. LTD. versus TATA AIG GENERAL INSURA | pages 32, units 81 (80 numbered), opinions 1, unusable pages [] |
| judgment | M/S. SESHASAYEE STEELS P. LTD. versus ASSISTANT COMMISSIONER | pages 11, units 30 (29 numbered), opinions 1, unusable pages [] |
| judgment | MANIK MAJUMDER AND OTHERS versus DIPAK KUMAR SAHA (DEAD) THR | pages 48, units 112 (111 numbered), opinions 1, unusable pages [] |
| judgment | MANOHAR INFRASTRUCTURE AND CONSTRUCTIONS PRIVATE LIMITED ver | pages 14, units 34 (33 numbered), opinions 1, unusable pages [] |
| judgment | MOHAMMADE YUSUF & ORS. versus RAJKUMAR & ORS. | pages 12, units 23 (22 numbered), opinions 1, unusable pages [] |
| judgment | MRS. UMADEVI NAMBIAR versus THAMARASSERI ROMAN CATHOLIC DIOC | pages 11, units 27 (26 numbered), opinions 1, unusable pages [] |
| judgment | NARAYAN DEORAO JAVLE (DECEASED) THROUGH LRS. versus KRISHNA  | pages 20, units 48 (47 numbered), opinions 1, unusable pages [] |
| judgment | NEENA ANEJA & ANR. versus JAI PRAKASH ASSOCIATES LTD. | pages 73, units 116 (114 numbered), opinions 1, unusable pages [] |
| judgment | PRAKASH (DEAD) BY LR. versus G. ARADHYA AND ORS. | pages 18, units 64 (63 numbered), opinions 1, unusable pages [] |
| judgment | R. HEMALATHA versus KASHTHURI | pages 12, units 31 (30 numbered), opinions 1, unusable pages [] |
| judgment | RAVINDER KAUR GREWAL & ORS. versus MANJIT KAUR & ORS. | pages 25, units 36 (35 numbered), opinions 1, unusable pages [] |
| judgment | RICARDO CONSTRUCTIONS PVT. LTD. versus RAVI KUCKIAN & OTHERS | pages 6, units 16 (15 numbered), opinions 1, unusable pages [] |
| judgment | RIPUDAMAN SINGH versus TIKKA MAHESHWAR CHAND | pages 11, units 27 (26 numbered), opinions 1, unusable pages [] |
| judgment | S. SAROJINI AMMA versus VELAYUDHAN PILLAI SREEKUMAR | pages 7, units 22 (21 numbered), opinions 1, unusable pages [] |
| judgment | SATYA PAL ANAND versus STATE OF M.P. & ORS. | pages 36, units 57 (56 numbered), opinions 1, unusable pages [] |
| judgment | SHYAMSUNDAR RADHESHYAM AGRAWAL & ANR. versus PUSHPABAI NILKA | pages 13, units 21 (20 numbered), opinions 1, unusable pages [] |
| judgment | SIRI CHAND (DECEASED) THR. LRS. versus SURINDER SINGH | pages 12, units 30 (29 numbered), opinions 1, unusable pages [] |
| judgment | SITA RAM BHAMA versus RAMVATAR BHAMA | pages 10, units 31 (30 numbered), opinions 1, unusable pages [] |
| judgment | SMT. BAYANABAI KAWARE versus RAJENDRA S/O BABURAO DHOTE | pages 7, units 26 (25 numbered), opinions 1, unusable pages [] |
| judgment | SMT. M. HEMALATHA DEVI & ORS. versus B. UDAYASRI | pages 31, units 68 (67 numbered), opinions 1, unusable pages [] |
| judgment | SOPAN (DEAD) THROUGH HIS L.R. versus SYED NABI | pages 10, units 17 (16 numbered), opinions 1, unusable pages [] |
| judgment | SRI MAHESH versus SANGRAM & ORS | pages 19, units 37 (36 numbered), opinions 1, unusable pages [] |
| judgment | SRIDHAR & ANR. versus N. REVANNA & ORS. | pages 13, units 41 (40 numbered), opinions 1, unusable pages [] |
| judgment | SUBHASH CHANDER & ORS. versus M/S BHARAT PETROLEUM CORPORATI | pages 13, units 33 (32 numbered), opinions 1, unusable pages [] |
| judgment | SURESH SHAH versus HIPAD TECHNOLOGY INDIA PRIVATE LIMITED | pages 14, units 29 (28 numbered), opinions 1, unusable pages [] |
| judgment | THE ANDHRA PRADESH INDUSTRIAL INFRASTRUCTURE CORPORATION LIM | pages 14, units 31 (30 numbered), opinions 1, unusable pages [] |
| judgment | THE STATE OF KERALA & ORS versus M/S JOSEPH & COMPANY | pages 22, units 43 (42 numbered), opinions 1, unusable pages [] |
| judgment | THE SUB REGISTRAR, AMUDALAVALASA & ANR. versus M/S DANKUNI S | pages 41, units 79 (78 numbered), opinions 1, unusable pages [] |
| judgment | UNION OF INDIA & ANR. versus S. NARASIMHULU NAIDU (DEAD) THR | pages 39, units 75 (74 numbered), opinions 1, unusable pages [] |
| judgment | VEENA SINGH (DEAD) THROUGH LR versus THE DISTRICT REGISTRAR/ | pages 55, units 123 (121 numbered), opinions 1, unusable pages [] |
| judgment | VITHAL TUKARAM KADAM AND ANOTHER versus VAMANRAO SAWALARAM B | pages 9, units 19 (18 numbered), opinions 1, unusable pages [] |
| judgment | YOGESH GOYANKA versus GOVIND & ORS. | pages 8, units 25 (24 numbered), opinions 1, unusable pages [] |
| statute | Consumer Protection Act, 2019 | sections 107/107 (missing []), state blocks 0, footnotes 3, unusable pages [] |
| statute | Registration Act, 1908 | sections 96/96 (missing []), state blocks 144, footnotes 68, unusable pages [] |
| statute | Transfer of Property Act, 1882 | sections 147/147 (missing []), state blocks 1, footnotes 154, unusable pages [] |

## Gate

Every required field green: **PASS**
