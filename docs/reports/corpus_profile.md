# Corpus profile

_Generated 2026-09-23T23:30:57+00:00 by `praetor profile` from `data/processed/praetor.sqlite`._

**Documents:** 1012 · **Chunks:** 27560

## Chunks by type, language and domain tag

| doc_type | language | domain tag | chunks |
|---|---|---|---|
| judgment | en | case_law | 23835 |
| judgment | en | civil_procedure | 5091 |
| judgment | en | consumer | 951 |
| judgment | en | contract_civil | 9267 |
| judgment | en | criminal_procedure | 16 |
| judgment | en | land_acquisition | 2289 |
| judgment | en | property_land | 6655 |
| judgment | en | registration | 514 |
| statute | en | civil_procedure | 1135 |
| statute | en | consumer | 251 |
| statute | en | contract_civil | 1693 |
| statute | en | criminal_procedure | 1353 |
| statute | en | land_acquisition | 168 |
| statute | en | property_land | 818 |
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
| statute | `part` | 45.1% |
| statute | `chapter` | 79.1% |
| statute | `amendment_notes` | 20.1% |
| statute | `page_start` | 100.0% |
| judgment | `judges` | 99.9% |
| judgment | `citation` | 100.0% |
| judgment | `para_start` | 59.9% |
| judgment | `disposal_nature` | 98.7% |
| judgment | `cnr` | 100.0% |
| judgment | `page_start` | 95.8% |

## Tokens, duplicates, OCR, status

- `token_count` (bge-m3 tokenizer): p5 65, p50 341, p95 444, max 1163; over MAX_CHUNK_TOKENS=450: 8
- duplicate `(doc_id, sha1(text))`: 0 · identical text across documents: 135
- text_source: layer 26560, metadata 1000
- OCR share: 0.0%; mean OCR confidence: n/a
- status: n/a 23835, in_force 3724, partially_in_force 1
- `decision_date`: oldest 2016-01-07, newest 2025-11-06, unparseable 0
- judgment locators: header 1000, by paragraph 14275, by page 8560

## Categorical values (top 10 / bottom 5)

- **doc_type** (2 values): top: judgment (23835); statute (3725) · bottom: —
- **title** (1010 values): top: Code of Civil Procedure, 1908 (1135); Bharatiya Nagarik Suraksha Sanhita, 2023 (731); INDORE DEVELOPMENT AUTHORITY versus MANOHARLAL & O (480); Bharatiya Nyaya Sanhita, 2023 (425); BIKRAM CHATTERJI & ORS versus UNION OF INDIA & ORS (370); M/S N. N. GLOBAL MERCANTILE PRIVATE LIMITED versus (314); INDORE DEVELOPMENT AUTHORITY versus SHAILENDRA (DE (291); Indian Contract Act, 1872 (284); Registration Act, 1908 (260); KEDAR NATH YADAV versus STATE OF WEST BENGAL & ORS (223) · bottom: ENFORCEMENT DIRECTORATE GOVERNMENT OF INDIA versus (3); GOVERNMENT OF NCT OF DELHI AND ANR versus M/S. BEA (3); HITESH UMESHBHAI MASHRU versus THE STATE OF GUJARA (3); AJAY GUPTA versus RAJU @ RAJENDRA SINGH YADAV (3); AXIS BANK LIMITED versus NAREN SETH & ANR. (2)
- **source_name** (2 values): top: Indian Supreme Court Judgments (AWS Open Data) (23835); India Code (3725) · bottom: —
- **licence** (2 values): top: CC-BY-4.0 (23835); Government of India legislative text published on  (3725) · bottom: —
- **authority** (2 values): top: Supreme Court of India (23835); Parliament of India (3725) · bottom: —
- **jurisdiction** (16 values): top: IN (27330); IN-UP (56); IN-OD (31); IN-KA (23); IN-UK (23); IN-KL (22); IN-TR (15); IN-RJ (12); IN-AP (11); IN-MH (11) · bottom: IN-GJ (7); IN-HP (6); IN-AS (3); IN-TN (2); IN-WB (1)
- **language** (1 values): top: en (27560) · bottom: —
- **script** (1 values): top: Latn (27560) · bottom: —
- **status** (3 values): top: n/a (23835); in_force (3724); partially_in_force (1) · bottom: —
- **text_source** (2 values): top: layer (26560); metadata (1000) · bottom: —
- **act_title** (13 values): top: (null) (23835); Code of Civil Procedure, 1908 (1135); Bharatiya Nagarik Suraksha Sanhita, 2023 (731); Bharatiya Nyaya Sanhita, 2023 (425); Indian Contract Act, 1872 (284); Registration Act, 1908 (260); Bharatiya Sakshya Adhiniyam, 2023 (197); Transfer of Property Act, 1882 (169); Right to Fair Compensation and Transparency in Lan (168); Consumer Protection Act, 2019 (135) · bottom: Right to Fair Compensation and Transparency in Lan (168); Consumer Protection Act, 2019 (135); Real Estate (Regulation and Development) Act, 2016 (116); Limitation Act, 1963 (53); Specific Relief Act, 1963 (52)
- **part** (38 values): top: (null) (25881); First Schedule (748); Part XI — Miscellaneous (204); Part XI — Of the Duites and Powers of Registering  (80); Part IV — Production and Effect of Evidence (74); Part III — On Proof (60); Part II — Chapter Ii (58); Part II — Execution (56); Part II — Specific Relief (38); Part I — Suits in General (36) · bottom: Part I — Chapter I (4); Part III — Incidental Proceedings (4); Part IV — Acquisition of Ownership by Possession (3); Part VIII — Of Presenting Wills and Authorities to (2); Part VI — Supplemental Proceedings (2)
- **chapter** (167 values): top: (null) (24612); Order XXI — Execution of Decrees and Orders (130); Chapter XXXIX — Miscellaneous (125); Chapter IV (96); Chapter X — Agency (86); Chapter VI — Of Offences Affecting the Human Body (61); Chapter VI — Of the Consequences of Breach of Cont (58); Chapter IV — Consumer Disputer Redressal Commissio (54); Chapter II — Of Transfers of Property by Act of Pa (52); Chapter I — Preliminary (51) · bottom: Order L — Provincial. Small Cause Courts (2); Chapter III — Rectification of Instruments (1); Chapter XI — Of Improper Admission and Rejection o (1); Chapter XX — Repeal and Savings (1); Order LI — Presidency Small Cause Courts (1)
- **court** (2 values): top: Supreme Court of India (23835); (null) (3725) · bottom: —
- **disposal_nature** (16 values): top: Appeal(s) allowed (11111); Dismissed (4737); (null) (4044); Disposed off (3488); Case Partly allowed (1102); Reference answered (1013); Directions issued (888); Case Allowed (401); Dismissed not complying condition order (370); Matter referred to larger bench (232) · bottom: Remitted to Lower Court (39); Rejected (28); Leave Granted & Allowed (26); Hearing Adjourned (24); Transferred to High Court (12)

## Per-document parse checks

| type | title | checks |
|---|---|---|
| judgment | A. SREENIVASA REDDY versus RAKESH SHARMA AND ANR. | pages 27, units 77 (76 numbered), opinions 1, unusable pages [] |
| judgment | A. VALLIAMMAI versus K.P. MURALI AND OTHERS | pages 14, units 43 (42 numbered), opinions 1, unusable pages [] |
| judgment | A.B. GOVARDHAN versus P. RAGOTHAMAN | pages 22, units 63 (62 numbered), opinions 1, unusable pages [] |
| judgment | A.M. MOHAN versus THE STATE REPRESENTED BY SHO AND ANOTHER | pages 18, units 39 (38 numbered), opinions 1, unusable pages [] |
| judgment | A.T. MYDEEN AND ANOTHER versus THE ASSISTANT COMMISSIONER, C | pages 25, units 51 (50 numbered), opinions 1, unusable pages [] |
| judgment | AARIFABEN YUNUSBHAI PATEL & ORS. versus MUKUL THAKOREBHAI AM | pages 10, units 15 (14 numbered), opinions 1, unusable pages [] |
| judgment | ABDUL VAHAB versus STATE OF MADHYA PRADESH | pages 12, units 28 (27 numbered), opinions 1, unusable pages [] |
| judgment | ABHISHEK SAXENA versus THE STATE OF UTTAR PRADESH & ANR | pages 7, units 18 (17 numbered), opinions 1, unusable pages [] |
| judgment | ACHHAR SINGH versus STATE OF HIMACHAL PRADESH | pages 25, units 57 (55 numbered), opinions 1, unusable pages [] |
| judgment | ACHIN GUPTA versus STATE OF HARYANA & ANR. | pages 35, units 60 (59 numbered), opinions 1, unusable pages [] |
| judgment | ADITYA KHAITAN & ORS. versus IL AND FS FINANCIAL SERVICES LI | pages 12, units 39 (38 numbered), opinions 1, unusable pages [] |
| judgment | AFJAL ALI SHA @ ABJAL SHAUKAT SHA versus STATE OF WEST BENGA | pages 22, units 54 (53 numbered), opinions 1, unusable pages [] |
| judgment | AFJAL ANSARI versus STATE OF UP | pages 57, units 159 (158 numbered), opinions 2, unusable pages [] |
| judgment | AGRA DEVELOPMENT AUTHORITY, AGRA versus ANEK SINGH AND OTHER | pages 5, units 20 (19 numbered), opinions 1, unusable pages [] |
| judgment | AJAI ALIAS AJJU ETC. ETC versus THE STATE OF UTTAR PRADESH | pages 12, units 32 (31 numbered), opinions 1, unusable pages [] |
| judgment | AJANTA LLP versus CASIO KEISANKI KABUSHIKI KAISHA D/B/A CASI | pages 14, units 22 (21 numbered), opinions 1, unusable pages [] |
| judgment | AJAY DABRA versus PYARE RAM & ORS. | pages 14, units 24 (23 numbered), opinions 1, unusable pages [] |
| judgment | AJAY GUPTA versus RAJU @ RAJENDRA SINGH YADAV | pages 3, units 10 (8 numbered), opinions 1, unusable pages [] |
| judgment | AJAY KUMAR RADHEYSHYAM GOENKA versus TOURISM FINANCE CORPORA | pages 67, units 214 (213 numbered), opinions 2, unusable pages [] |
| judgment | AJAY PAL SINGH & ORS. versus STATE OF UTTAR PRADESH & ANR. | pages 14, units 32 (31 numbered), opinions 1, unusable pages [] |
| judgment | AJWAR versus NIYAJ AHMAD & ANR. | pages 11, units 32 (31 numbered), opinions 1, unusable pages [] |
| judgment | AJWAR versus WASEEM AND ANOTHER | pages 21, units 10 (9 numbered), opinions 1, unusable pages [] |
| judgment | AKHILESH SINGH @ AKHILESHWAR SINGH versus LAL BABU SINGH & O | pages 11, units 21 (20 numbered), opinions 1, unusable pages [] |
| judgment | AKKAMMA & ORS. versus VEMAVATHI & ORS. | pages 16, units 24 (23 numbered), opinions 1, unusable pages [] |
| judgment | ALAGAMMAL AND ORS. versus GANESAN AND ANR. | pages 16, units 36 (35 numbered), opinions 1, unusable pages [] |
| judgment | ALI AHMAD versus THE STATE OF BIHAR & ANR. | pages 6, units 18 (0 numbered), opinions 1, unusable pages [] |
| judgment | ALIFIYA HUSENBHAI KESHARIYA versus SIDDIQ ISMAIL SINDHI & OR | pages 10, units 32 (30 numbered), opinions 1, unusable pages [] |
| judgment | ALIGARH DEVELOPMENT AUTHORITY versus MEGH SINGH & ORS. | pages 5, units 12 (11 numbered), opinions 1, unusable pages [] |
| judgment | ALLIANZ GENERAL INSURANCE CO LTD & ANR versus THE STATE OF M | pages 33, units 88 (87 numbered), opinions 1, unusable pages [] |
| judgment | ALLOKAM PEDDABBAYYA AND ANOTHER versus ALLAHABAD BANK AND OT | pages 13, units 28 (26 numbered), opinions 1, unusable pages [] |
| judgment | ALPHA G184 OWNERS ASSOCIATION versus MAGNUM INTERNATIONAL TR | pages 18, units 51 (50 numbered), opinions 1, unusable pages [] |
| judgment | AMANDEEP SINGH SARAN versus STATE OF CHHATTISGARH | pages 22, units 35 (34 numbered), opinions 1, unusable pages [] |
| judgment | AMBADAS KHANDUJI SHINDE & ORS. versus ASHOK SADASHIV MAMURKA | pages 6, units 15 (14 numbered), opinions 1, unusable pages [] |
| judgment | AMEER MINHAJ versus DIERDRE ELIZABETH (WRIGHT) ISSAR AND ORS | pages 11, units 20 (19 numbered), opinions 1, unusable pages [] |
| judgment | AMITABHA DASGUPTA versus UNITED BANK OF INDIA & ORS. | pages 30, units 84 (83 numbered), opinions 1, unusable pages [] |
| judgment | AMOD KUMAR KANTH versus ASSOCIATION OF VICTIM OF UPHAAR TRAG | pages 26, units 44 (0 numbered), opinions 1, unusable pages [] |
| judgment | AMRITLAL versus SHANTILAL SONI & ORS. | pages 7, units 13 (0 numbered), opinions 1, unusable pages [] |
| judgment | ANANT THANUR KARMUSE versus THE STATE OF MAHARASHTRA & ORS | pages 23, units 66 (65 numbered), opinions 1, unusable pages [] |
| judgment | ANAPURNA JAISWAL versus INDIAN OIL CORPORATION LTD. AND ORS. | pages 10, units 23 (22 numbered), opinions 1, unusable pages [] |
| judgment | ANDANUR KALAMMA AND ORS. versus GANGAMMA (DEAD) BY L.RS. | pages 19, units 48 (47 numbered), opinions 1, unusable pages [] |
| judgment | ANIL AGARWAL FOUNDATION ETC. ETC. versus STATE OF ORISSA AND | pages 57, units 135 (134 numbered), opinions 1, unusable pages [] |
| judgment | ANIL KUMAR SOTI versus STATE OF UTTAR PRADESH THROUGH COLLEC | pages 5, units 10 (9 numbered), opinions 1, unusable pages [] |
| judgment | ANISH M RAWTHER @ ANEES MOHAMMED RAWTHER versus HAFEEZ UR RA | pages 4, units 7 (6 numbered), opinions 1, unusable pages [] |
| judgment | ANJU GARG & ANR versus DEEPAK KUMAR GARG | pages 10, units 21 (0 numbered), opinions 1, unusable pages [] |
| judgment | ANJUM HUSSAIN & ORS. versus INTELLICITY BUSINESS PARK PVT. L | pages 12, units 22 (21 numbered), opinions 1, unusable pages [] |
| judgment | APPAIYA versus ANDIMUTHU @ THANGAPANDI & ORS. | pages 20, units 40 (39 numbered), opinions 1, unusable pages [] |
| judgment | APPARAJU MALHAR RAO versus TULA VENKATAIAH@ VENKAT RAO (DEAD | pages 4, units 20 (19 numbered), opinions 1, unusable pages [] |
| judgment | AROON PURIE versus STATE OF NCT OF DELHI & ORS. | pages 15, units 42 (41 numbered), opinions 1, unusable pages [] |
| judgment | ARULMIGHU NELLUKADAI MARIAMMAN versus TAMILARASI (DEAD) BY L | pages 9, units 21 (20 numbered), opinions 1, unusable pages [] |
| judgment | ARUN BHATIYA versus HDFC BANK & ORS. | pages 10, units 37 (36 numbered), opinions 1, unusable pages [] |
| judgment | ARUN DEV UPADHYAYA versus INTEGRATED SALES SERVICE LTD. & AN | pages 18, units 57 (56 numbered), opinions 1, unusable pages [] |
| judgment | ASGAR & ORS. versus MOHAN VARMA & ORS. | pages 28, units 72 (71 numbered), opinions 1, unusable pages [] |
| judgment | ASHA RANI GUPTA versus SRI VINEET KUMAR | pages 28, units 56 (54 numbered), opinions 1, unusable pages [] |
| judgment | ASHATAI W/O ANAND DUPARTE versus SHRIRAM CITY UNION FINANCE  | pages 10, units 59 (58 numbered), opinions 1, unusable pages [] |
| judgment | ASHOK GULABRAO BONDRE versus VILAS MADHUKARRAO DESHMUKH AND  | pages 6, units 35 (34 numbered), opinions 1, unusable pages [] |
| judgment | ASHOK KUMAR & ANR. ETC. versus STATE OF HARYANA | pages 6, units 11 (10 numbered), opinions 1, unusable pages [] |
| judgment | ASHOK KUMAR & ORS. versus UNION OF INDIA & ANR. | pages 4, units 9 (0 numbered), opinions 1, unusable pages [] |
| judgment | ASHOK KUMAR GUPTA & ANR. versus M/S SITALAXMI SAHUWALA MEDIC | pages 18, units 39 (38 numbered), opinions 1, unusable pages [] |
| judgment | ASHOK KUMAR SINGH CHANDEL versus STATE OF U.P. | pages 78, units 237 (236 numbered), opinions 1, unusable pages [] |
| judgment | ASHOK KUMAR versus NEW INDIA ASSURANCE CO. LTD. | pages 21, units 54 (53 numbered), opinions 1, unusable pages [] |
| judgment | ASIM AKHTAR versus THE STATE OF WEST BENGAL & ANR. | pages 9, units 23 (22 numbered), opinions 1, unusable pages [] |
| judgment | ASMA LATEEF & ANR versus SHABBIR AHMAD & ORS | pages 32, units 81 (80 numbered), opinions 1, unusable pages [] |
| judgment | ASSET RECONSTRUCTION COMPANY (INDIA) LIMITED versus TULIP ST | pages 59, units 124 (123 numbered), opinions 1, unusable pages [] |
| judgment | ASSURANCE CO. LTD. versus HILLI MULTIPURPOSE COLD STORAGE PV | pages 36, units 94 (93 numbered), opinions 1, unusable pages [] |
| judgment | ATAMJIT SINGH versus STATE (NCT OF DELHI) & ANR. | pages 4, units 11 (10 numbered), opinions 1, unusable pages [] |
| judgment | ATMA RAM versus CHARANJIT SINGH | pages 10, units 15 (14 numbered), opinions 1, unusable pages [] |
| judgment | AUTHORISED OFFICER, CENTRAL BANK OF INDIA versus SHANMUGAVEL | pages 79, units 193 (192 numbered), opinions 1, unusable pages [] |
| judgment | AUTO CARS versus TRIMURTI CARGO MOVERS PVT. LTD. & ORS. | pages 15, units 58 (57 numbered), opinions 1, unusable pages [] |
| judgment | AVITEL POST STUDIOZ LIMITED & ORS. versus HSBC PI HOLDINGS ( | pages 66, units 144 (143 numbered), opinions 1, unusable pages [] |
| judgment | AVNEESH CHANDAN GADGIL & ANR. versus ORIENTAL BANK OF COMMER | pages 4, units 12 (11 numbered), opinions 1, unusable pages [] |
| judgment | AVTAR SINGH & ORS. versus BIMLA DEVI & ORS. | pages 10, units 26 (25 numbered), opinions 1, unusable pages [] |
| judgment | AXIS BANK LIMITED versus NAREN SETH & ANR. | pages 2, units 6 (5 numbered), opinions 1, unusable pages [] |
| judgment | AXIS BANK LIMITED versus NAREN SHETH & ANR. | pages 20, units 72 (70 numbered), opinions 1, unusable pages [] |
| judgment | AYAN CHATTERJEE versus FUTURE TECHNOLOGY FOUNDATION INC. & O | pages 6, units 21 (20 numbered), opinions 1, unusable pages [] |
| judgment | AYODHYA FAIZABAD DEVELOPMENT AUTHORITY AND ANR. versus RAM N | pages 5, units 18 (17 numbered), opinions 1, unusable pages [] |
| judgment | B. L. KASHYAP AND SONS LTD versus M/S JMS STEELS AND POWER C | pages 20, units 49 (48 numbered), opinions 1, unusable pages [] |
| judgment | B. R. PATIL versus TULSA Y. SAWKAR & ORS. | pages 23, units 57 (56 numbered), opinions 1, unusable pages [] |
| judgment | B. VIJAYA BHARATHI versus P. SAVITRI & ORS. | pages 8, units 20 (19 numbered), opinions 1, unusable pages [] |
| judgment | B.K. EDUCATIONAL SERVICES PRIVATE LIMITED versus PARAG GUPTA | pages 35, units 74 (73 numbered), opinions 1, unusable pages [] |
| judgment | B.R.K. AATHITHAN versus SUN GROUP & ANR. | pages 8, units 21 (20 numbered), opinions 1, unusable pages [] |
| judgment | BABULAL VARDHARJI GURJAR versus VEER GURJAR ALUMINIUM INDUST | pages 59, units 111 (110 numbered), opinions 1, unusable pages [] |
| judgment | BAINI PRASAD (D) THR. LRS. versus DURGA DEVI | pages 19, units 29 (28 numbered), opinions 1, unusable pages [] |
| judgment | BALKRISHNA DATTATRAYA GALANDE versus BALKRISHNA RAMBHAROSE G | pages 11, units 20 (19 numbered), opinions 1, unusable pages [] |
| judgment | BALVEER BATRA versus THE NEW INDIA ASSURANCE COMPANY & ANR. | pages 19, units 40 (39 numbered), opinions 1, unusable pages [] |
| judgment | BALWAN SINGH & ORS. versus LAND ACQUISITION COLLECTOR & ANR. | pages 3, units 8 (7 numbered), opinions 1, unusable pages [] |
| judgment | BANGALORE DEVELOPMENT AUTHORITY & ANR. versus STATE OF KARNA | pages 12, units 46 (44 numbered), opinions 1, unusable pages [] |
| judgment | BANGALORE DEVELOPMENT AUTHORITY versus N. NANJAPPA AND ANOTH | pages 8, units 22 (21 numbered), opinions 1, unusable pages [] |
| judgment | BANK OF BARODA versus KOTAK MAHINDRA BANK LTD. | pages 24, units 59 (58 numbered), opinions 1, unusable pages [] |
| judgment | BANK OF INDIA versus M/S. BRINDAVAN AGRO INDUSTRIES PVT. LTD | pages 11, units 27 (26 numbered), opinions 1, unusable pages [] |
| judgment | BANK OF RAJASTHAN LTD. versus VCK SHARES & STOCK BROKING SER | pages 34, units 143 (142 numbered), opinions 1, unusable pages [] |
| judgment | BANWARI AND OTHERS versus HARYANA STATE INDUSTRIAL AND INFRA | pages 15, units 41 (40 numbered), opinions 1, unusable pages [] |
| judgment | BAPUSAHEB CHIMASAHEB NAIK-NIMBALKAR (DEAD THROUGH LRS.) & AN | pages 14, units 21 (20 numbered), opinions 1, unusable pages [] |
| judgment | BAR OF INDIAN LAWYERS THROUGH ITS PRESIDENT JASBIR SINGH MAL | pages 46, units 61 (60 numbered), opinions 2, unusable pages [] |
| judgment | BASAVARAJ versus INDIRA AND OTHERS | pages 11, units 31 (30 numbered), opinions 1, unusable pages [] |
| judgment | BERNARD FRANCIS JOSEPH VAZ AND OTHERS versus GOVERNMENT OF K | pages 40, units 113 (112 numbered), opinions 1, unusable pages [] |
| judgment | BHAG SINGH ETC. versus UNION OF INDIA & ANR. | pages 7, units 20 (19 numbered), opinions 1, unusable pages [] |
| judgment | BHAGWAN SINGH versus DILIP KUMAR @ DEEPU @ DEPAK AND ANOTHER | pages 15, units 38 (37 numbered), opinions 1, unusable pages [] |
| judgment | BHAGYODAY COOPERATIVE BANK LTD. versus RAVINDRA BALKRISHNA P | pages 27, units 45 (44 numbered), opinions 1, unusable pages [] |
| judgment | BHARAT PETROLEUM CORPORATION LTD. (BPCL) & ORS versus NISAR  | pages 16, units 35 (34 numbered), opinions 1, unusable pages [] |
| judgment | BHARAT SANCHAR NIGAM LIMITED versus M/S. NEMICHAND DAMODARDA | pages 16, units 42 (41 numbered), opinions 1, unusable pages [] |
| judgment | BHARAT SHER SINGH KALSIA versus STATE OF BIHAR & ANR. | pages 14, units 39 (38 numbered), opinions 1, unusable pages [] |
| judgment | BHARATSING S/O GULABSINGH JAKHAD & ORS. versus THE STATE OF  | pages 9, units 23 (22 numbered), opinions 1, unusable pages [] |
| judgment | BHASKER & ANR. versus AYODHYA JEWELLERS | pages 13, units 34 (33 numbered), opinions 1, unusable pages [] |
| judgment | BHIKCHAND S/O DHONDIRAM MUTHA (DECEASED) THROUGH LRS. versus | pages 29, units 50 (49 numbered), opinions 1, unusable pages [] |
| judgment | BHIM RAO BASWANTH RAO PATIL versus K. MADAN MOHAN RAO AND OR | pages 22, units 50 (49 numbered), opinions 1, unusable pages [] |
| judgment | BHIMASHANKAR SAHAKARI SAKKARE KARKHANE NIYAMITA versus WALCH | pages 21, units 70 (69 numbered), opinions 1, unusable pages [] |
| judgment | BHIMRAO RAMCHANDRA KHALATE (DECEASED) THROUGH LRS. versus NA | pages 16, units 36 (35 numbered), opinions 1, unusable pages [] |
| judgment | BHISHAM LAL VERMA versus STATE OF UTTAR PRADESH AND ANOTHER | pages 7, units 15 (14 numbered), opinions 1, unusable pages [] |
| judgment | BHIVCHANDRA SHANKAR MORE versus BALU GANGARAM MORE & ORS. | pages 11, units 21 (20 numbered), opinions 1, unusable pages [] |
| judgment | BHUPATBHAI BACHUBHAI CHAVDA & ANR. versus STATE OF GUJARAT | pages 6, units 9 (8 numbered), opinions 1, unusable pages [] |
| judgment | BHUPINDER SINGH versus JOGINDER SINGH (D) BY LRS. & ORS. | pages 6, units 14 (13 numbered), opinions 1, unusable pages [] |
| judgment | BHURI BAI versus THE STATE OF MADHYA PRADESH | pages 8, units 25 (24 numbered), opinions 1, unusable pages [] |
| judgment | BIJENDER & ORS. versus STATE OF HARYANA & ANR. | pages 18, units 62 (61 numbered), opinions 1, unusable pages [] |
| judgment | BIKRAM CHATTERJI & ORS versus UNION OF INDIA & ORS. | pages 296, units 407 (406 numbered), opinions 1, unusable pages [136, 138] |
| judgment | BIR WATI & ORS. versus UNION OF INDIA & ANR. | pages 6, units 18 (17 numbered), opinions 1, unusable pages [] |
| judgment | BISWAJIT SUKUL versus DEO CHAND SARDA & ORS. | pages 6, units 26 (25 numbered), opinions 1, unusable pages [] |
| judgment | BOHATIE DEVI (DEAD) THROUGH LR versus THE STATE OF UTTAR PRA | pages 11, units 25 (24 numbered), opinions 1, unusable pages [] |
| judgment | BRIGADE ENTERPRISES LIMITED versus ANIL KUMAR VIRMANI & ORS. | pages 24, units 50 (49 numbered), opinions 1, unusable pages [] |
| judgment | BRIJESH SINGH versus STATE OF UTTAR PRADESH AND OTHERS | pages 5, units 13 (12 numbered), opinions 1, unusable pages [] |
| judgment | BUNGA DANIEL BABU versus MIS SRI VASUDEVA CONSTRUCTIONS & OR | pages 17, units 29 (28 numbered), opinions 1, unusable pages [] |
| judgment | BUREAU OF INVESTIGATION (CBI) AND ANR. versus THOMMANDRU HAN | pages 60, units 112 (110 numbered), opinions 1, unusable pages [] |
| judgment | C. HARIDASAN versus ANAPPATH PARAKKATTU VASUDEVA KURUP & OTH | pages 38, units 116 (115 numbered), opinions 2, unusable pages [] |
| judgment | C. VENKATA SWAMY versus H. N. SHIVANNA (D) BY L.R. & ANR. ET | pages 8, units 35 (34 numbered), opinions 1, unusable pages [] |
| judgment | C.S. GOPALAKRISHNAN ETC. versus THE STATE OF TAMIL NADU & OT | pages 25, units 46 (45 numbered), opinions 1, unusable pages [] |
| judgment | C.S. RAMASWAMY versus V. K. SENTHIL & ORS | pages 17, units 43 (42 numbered), opinions 1, unusable pages [] |
| judgment | C.S. VENKATESH versus MURTHY (D) BY LRS. & ORS. | pages 11, units 29 (28 numbered), opinions 1, unusable pages [] |
| judgment | CANARA BANK versus M/S UNITED INDIA INSURANCE CO. LTD. & ORS | pages 30, units 68 (67 numbered), opinions 1, unusable pages [] |
| judgment | CANARA BANK versus N. G. SUBBARAYA SETTY & ANR. | pages 43, units 81 (80 numbered), opinions 1, unusable pages [] |
| judgment | CANARA BANK versus P. SELATHAL AND ORS. ETC.ETC. | pages 20, units 46 (45 numbered), opinions 1, unusable pages [] |
| judgment | CAPTAIN MANJIT SINGH VIRDI (RETD.) versus HUSSAIN MOHAMMED S | pages 10, units 27 (26 numbered), opinions 1, unusable pages [] |
| judgment | CARDINAL MAR GEORGE ALENCHERRY versus STATE OF KERALA & ANR. | pages 23, units 34 (33 numbered), opinions 1, unusable pages [] |
| judgment | CCI PROJECTS (P) LTD. versus VRAJENDRA JOGJIVANDAS THAKKAR | pages 9, units 21 (20 numbered), opinions 1, unusable pages [] |
| judgment | CENTRAL BUREAU OF INVESTIGATION versus ARYAN SINGH ETC. | pages 5, units 16 (15 numbered), opinions 1, unusable pages [] |
| judgment | CENTRAL BUREAU OF INVESTIGATION versus ASHOK SIRPAL | pages 9, units 17 (15 numbered), opinions 1, unusable pages [] |
| judgment | CENTRAL BUREAU OF INVESTIGATION versus KAPIL WADHAWAN & ANR. | pages 20, units 32 (31 numbered), opinions 1, unusable pages [] |
| judgment | CENTRAL BUREAU OF INVESTIGATION versus NAROTTAM DHAKAD & ANR | pages 14, units 33 (32 numbered), opinions 1, unusable pages [] |
| judgment | CENTRAL BUREAU OF INVESTIGATION versus SANTOSH KARNANI & ANR | pages 22, units 61 (60 numbered), opinions 1, unusable pages [] |
| judgment | CENTRAL BUREAU OF INVESTIGATION versus VIKAS MISHRA @ VIKASH | pages 11, units 29 (28 numbered), opinions 1, unusable pages [] |
| judgment | CHAIRMAN AND MANAGING DIRECTOR,THE FERTILIZERS AND CHEMICALS | pages 11, units 40 (39 numbered), opinions 1, unusable pages [] |
| judgment | CHAIRMAN-CUM-MANAGING DIRECTOR ONGC LTD. & ORS. versus CONSU | pages 7, units 12 (11 numbered), opinions 1, unusable pages [] |
| judgment | CHANABASAPPA versus KARNATAKA NEERAVARI NIGAM LTD. & ANR. | pages 10, units 24 (23 numbered), opinions 1, unusable pages [] |
| judgment | CHANCHALPATI DAS versus THE STATE OF WEST BENGAL & ANR. | pages 14, units 28 (27 numbered), opinions 2, unusable pages [] |
| judgment | CHAND KAUR (D) THR. LRS. versus MEHAR KAUR (D) THR. LRS. | pages 4, units 15 (14 numbered), opinions 1, unusable pages [] |
| judgment | CHANDER BHAN (D) THROUGH LR SHER SINGH versus MUKHTIAR SINGH | pages 11, units 35 (34 numbered), opinions 1, unusable pages [] |
| judgment | CHANDI PULIYA versus THE STATE OF WEST BENGAL | pages 7, units 23 (22 numbered), opinions 1, unusable pages [] |
| judgment | CHANDIGARH NURSING HOME AND ANR. versus SUKHDEEP KAUR | pages 8, units 18 (17 numbered), opinions 1, unusable pages [] |
| judgment | CHANDRABHAN (DECEASED) THROUGH LRS. & ORS. versus SARASWATI  | pages 14, units 43 (42 numbered), opinions 1, unusable pages [] |
| judgment | CHHOTANBEN AND ANR. versus KIRITBHAI JALKRUSHNABHAI THAKKAR  | pages 13, units 27 (26 numbered), opinions 1, unusable pages [] |
| judgment | CHILAMKURTI BALA SUBRAHMANYAM versus SAMANTHAPUDI VIJAYA LAK | pages 10, units 30 (0 numbered), opinions 1, unusable pages [] |
| judgment | COMMISSIONER, RAJASTHAN HOUSING BOARD AND OTHERS versus HIRA | pages 10, units 20 (19 numbered), opinions 1, unusable pages [] |
| judgment | COMMITTEE OF MANAGEMENT ANJUMAN INTEZAMIA MASAJID, VARANASI  | pages 13, units 29 (28 numbered), opinions 1, unusable pages [] |
| judgment | CPL ASHISH KUMAR CHAUHAN (RETD.) versus COMMANDING OFFICER & | pages 65, units 175 (174 numbered), opinions 1, unusable pages [] |
| judgment | CUDDALORE POWERGEN CORPORATION LTD versus M/S CHEMPLAST CUDD | pages 64, units 119 (118 numbered), opinions 1, unusable pages [] |
| judgment | DAHIBEN versus ARVINDBHAI KALYANJI BHANUSALI (GAJRA) (D) THR | pages 24, units 102 (101 numbered), opinions 1, unusable pages [] |
| judgment | DALJIT SINGH versus STATE OF HARYANA & ANR. | pages 13, units 36 (35 numbered), opinions 1, unusable pages [] |
| judgment | DAMINI AND ANOTHER versus MANAGING DIRECTOR, JODHPUR VIDYUT  | pages 6, units 19 (18 numbered), opinions 1, unusable pages [] |
| judgment | DAXABEN versus THE STATE OF GUJARAT & ORS. | pages 28, units 57 (56 numbered), opinions 1, unusable pages [] |
| judgment | DEBASISH PAUL & ANR. versus AMAL BORAL | pages 9, units 28 (27 numbered), opinions 1, unusable pages [] |
| judgment | DEEPAK S/O LAXMAN DONGRE versus THE STATE OF MAHARASHTRA & O | pages 16, units 18 (17 numbered), opinions 1, unusable pages [] |
| judgment | DEEPAK YADAV versus STATE OF U.P. & ANR | pages 22, units 43 (42 numbered), opinions 1, unusable pages [] |
| judgment | DELHI ADMINISTRATION & ANR. versus KIDARNATH MOHINDERNATH &  | pages 10, units 19 (19 numbered), opinions 1, unusable pages [] |
| judgment | DELHI ADMINISTRATION THR. SECRETARY, LAND AND BUILDING DEPAR | pages 7, units 17 (16 numbered), opinions 1, unusable pages [] |
| judgment | DELHI DEVELOPMENT AUTHORITY V versus SHYAMO & ORS. | pages 6, units 18 (17 numbered), opinions 1, unusable pages [] |
| judgment | DELHI DEVELOPMENT AUTHORITY versus AMIT JAIN & ORS | pages 5, units 16 (15 numbered), opinions 1, unusable pages [] |
| judgment | DELHI DEVELOPMENT AUTHORITY versus ANITA SINGH & ORS. | pages 13, units 27 (26 numbered), opinions 1, unusable pages [] |
| judgment | DELHI DEVELOPMENT AUTHORITY versus ASHA JAIN & ORS. | pages 7, units 20 (19 numbered), opinions 1, unusable pages [] |
| judgment | DELHI DEVELOPMENT AUTHORITY versus ASHA PRAKASH | pages 6, units 16 (15 numbered), opinions 1, unusable pages [] |
| judgment | DELHI DEVELOPMENT AUTHORITY versus BATTI & ORS | pages 8, units 19 (18 numbered), opinions 1, unusable pages [] |
| judgment | DELHI DEVELOPMENT AUTHORITY versus BEENA GUPTA (D) THROUGH L | pages 6, units 23 (22 numbered), opinions 1, unusable pages [] |
| judgment | DELHI DEVELOPMENT AUTHORITY versus BHAGI SINGH AND ORS. | pages 4, units 15 (14 numbered), opinions 1, unusable pages [] |
| judgment | DELHI DEVELOPMENT AUTHORITY versus BHAGWAT SINGH & ORS. | pages 5, units 15 (14 numbered), opinions 1, unusable pages [] |
| judgment | DELHI DEVELOPMENT AUTHORITY versus BHIM SAIN GOEL AND ORS. | pages 19, units 38 (0 numbered), opinions 1, unusable pages [] |
| judgment | DELHI DEVELOPMENT AUTHORITY versus CHANDERMAL & ORS. | pages 7, units 20 (19 numbered), opinions 1, unusable pages [] |
| judgment | DELHI DEVELOPMENT AUTHORITY versus DAMINI WADHWA & ORS. | pages 8, units 18 (17 numbered), opinions 1, unusable pages [] |
| judgment | DELHI DEVELOPMENT AUTHORITY versus DAYANAND & ORS. | pages 6, units 18 (17 numbered), opinions 1, unusable pages [] |
| judgment | DELHI DEVELOPMENT AUTHORITY versus DEWAN CHAND PRUTHI & ORS | pages 6, units 18 (17 numbered), opinions 1, unusable pages [] |
| judgment | DELHI DEVELOPMENT AUTHORITY versus DIWAN CHAND ANAND & ORS | pages 29, units 90 (89 numbered), opinions 1, unusable pages [] |
| judgment | DELHI DEVELOPMENT AUTHORITY versus EMINENT MARKETING PVT. LT | pages 6, units 20 (19 numbered), opinions 1, unusable pages [] |
| judgment | DELHI DEVELOPMENT AUTHORITY versus GODFREY PHILLIPS (I) LTD  | pages 33, units 72 (71 numbered), opinions 1, unusable pages [] |
| judgment | DELHI DEVELOPMENT AUTHORITY versus ISLAMUDDIN & ORS. | pages 6, units 11 (10 numbered), opinions 1, unusable pages [] |
| judgment | DELHI DEVELOPMENT AUTHORITY versus JAGAN SINGH & ORS. | pages 5, units 20 (19 numbered), opinions 1, unusable pages [] |
| judgment | DELHI DEVELOPMENT AUTHORITY versus KENNETH BUILDERS & DEVELO | pages 27, units 63 (62 numbered), opinions 1, unusable pages [] |
| judgment | DELHI DEVELOPMENT AUTHORITY versus KRISHAN LAL ARORA & ORS. | pages 4, units 15 (14 numbered), opinions 1, unusable pages [] |
| judgment | DELHI DEVELOPMENT AUTHORITY versus KUSHAM JAIN AND ANOTHER | pages 5, units 16 (15 numbered), opinions 1, unusable pages [] |
| judgment | DELHI DEVELOPMENT AUTHORITY versus MANPREET SINGH & ORS | pages 4, units 12 (11 numbered), opinions 1, unusable pages [] |
| judgment | DELHI DEVELOPMENT AUTHORITY versus MGS (INDIA) PRIVATE LIMIT | pages 4, units 13 (12 numbered), opinions 1, unusable pages [] |
| judgment | DELHI DEVELOPMENT AUTHORITY versus NARENDRA KUMAR JAIN & ORS | pages 3, units 8 (7 numbered), opinions 1, unusable pages [] |
| judgment | DELHI DEVELOPMENT AUTHORITY versus NARVADA DEVI & ORS. | pages 6, units 21 (20 numbered), opinions 1, unusable pages [] |
| judgment | DELHI DEVELOPMENT AUTHORITY versus NEM CHAND SHARMA AND ORS. | pages 6, units 17 (16 numbered), opinions 1, unusable pages [] |
| judgment | DELHI DEVELOPMENT AUTHORITY versus RAJ SINGH & ANR. | pages 5, units 18 (17 numbered), opinions 1, unusable pages [] |
| judgment | DELHI DEVELOPMENT AUTHORITY versus RAJAN SOOD & ORS. | pages 10, units 26 (25 numbered), opinions 1, unusable pages [] |
| judgment | DELHI DEVELOPMENT AUTHORITY versus RAJENDER SINGH & ORS. | pages 5, units 17 (16 numbered), opinions 1, unusable pages [] |
| judgment | DELHI DEVELOPMENT AUTHORITY versus RAJESH DUA & ORS. | pages 6, units 18 (17 numbered), opinions 1, unusable pages [] |
| judgment | DELHI DEVELOPMENT AUTHORITY versus RAMBIR AND ORS | pages 6, units 15 (14 numbered), opinions 1, unusable pages [] |
| judgment | DELHI DEVELOPMENT AUTHORITY versus REENA SURI AND ORS. | pages 5, units 8 (7 numbered), opinions 1, unusable pages [] |
| judgment | DELHI DEVELOPMENT AUTHORITY versus SHAKUNTLA DEVI AND ORS. | pages 4, units 15 (14 numbered), opinions 1, unusable pages [] |
| judgment | DELHI DEVELOPMENT AUTHORITY versus SHIV RAJ & ORS. | pages 5, units 17 (16 numbered), opinions 1, unusable pages [] |
| judgment | DELHI DEVELOPMENT AUTHORITY versus SUNIL KHATRI & ORS. | pages 22, units 49 (48 numbered), opinions 1, unusable pages [] |
| judgment | DELHI DEVELOPMENT AUTHORITY versus SURENDER SINGH & ORS. | pages 9, units 30 (29 numbered), opinions 1, unusable pages [] |
| judgment | DELHI DEVELOPMENT AUTHORITY versus TEJPAL & ORS. | pages 94, units 357 (355 numbered), opinions 1, unusable pages [] |
| judgment | DELHI DEVELOPMENT AUTHORITY versus VIRENDER LAL BAHRI & ORS. | pages 18, units 37 (36 numbered), opinions 1, unusable pages [] |
| judgment | DELHI METRO RAIL CORPORATION LTD. versus TARUN PAL SINGH & O | pages 30, units 60 (59 numbered), opinions 1, unusable pages [] |
| judgment | DESH RAJ & ORS. versus ROHTASH SINGH | pages 20, units 63 (62 numbered), opinions 1, unusable pages [] |
| judgment | DESH RAJ versus BALKISHAN (D) THROUGH PROPOSED LR MS. ROHINI | pages 10, units 25 (24 numbered), opinions 1, unusable pages [] |
| judgment | DEVADASSAN versus THE SECOND CLASS EXECUTIVE MAGISTRATE, RAM | pages 7, units 15 (14 numbered), opinions 1, unusable pages [] |
| judgment | DEVENDRA NATH SINGH versus STATE OF BIHAR & ORS. | pages 38, units 96 (95 numbered), opinions 1, unusable pages [] |
| judgment | DHANANJAY RAI @ GUDDU RAI versus STATE OF BIHAR | pages 9, units 17 (16 numbered), opinions 1, unusable pages [] |
| judgment | DHANRAJ ASWANI versus AMAR S. MULCHANDANI & ANR. | pages 56, units 123 (121 numbered), opinions 1, unusable pages [] |
| judgment | DHARMENDRA SHARMA versus AGRA DEVELOPMENT AUTHORITY | pages 13, units 27 (26 numbered), opinions 1, unusable pages [] |
| judgment | DHARNIDHAR MISHRA (D) AND ANOTHER versus STATE OF BIHAR AND  | pages 9, units 18 (0 numbered), opinions 1, unusable pages [] |
| judgment | DHEERAJ SINGH versus GREATER NOIDA INDUSTRIAL DEVELOPMENT AU | pages 7, units 25 (23 numbered), opinions 1, unusable pages [] |
| judgment | DIAMOND EXPORTS & ANR. versus UNITED INDIA INSURANCE COMPANY | pages 16, units 39 (38 numbered), opinions 1, unusable pages [] |
| judgment | DINESH SINGH THAKUR versus SONAL THAKUR | pages 10, units 24 (23 numbered), opinions 1, unusable pages [] |
| judgment | DIPALI BISWAS & ORS. versus NIRMALENDU MUKHERJEE & ORS. | pages 18, units 43 (42 numbered), opinions 1, unusable pages [] |
| judgment | DIRECTORATE OF ENFORCEMENT versus BIBHU PRASAD ACHARYA, ETC. | pages 13, units 15 (0 numbered), opinions 1, unusable pages [] |
| judgment | DIRECTORATE OF ENFORCEMENT versus NIRAJ TYAGI & ORS | pages 15, units 32 (31 numbered), opinions 1, unusable pages [] |
| judgment | DLF HOMES PANCHKULA (P) LTD. THROUGH ITS AUTHORISED SIGNATOR | pages 10, units 21 (20 numbered), opinions 1, unusable pages [10] |
| judgment | DLF HOMES PANCHKULA PVT. LTD versus D.S. DHANDA, ETC. ETC. | pages 15, units 33 (32 numbered), opinions 1, unusable pages [] |
| judgment | DR SONIA VERMA & ANR. versus THE STATE OF HARYANA & ANR. | pages 6, units 21 (20 numbered), opinions 1, unusable pages [] |
| judgment | DR. A. SURESH KUMAR & ORS. versus AMIT AGARWAL | pages 3, units 6 (0 numbered), opinions 1, unusable pages [] |
| judgment | DR. ABRAHAM PATANI OF MUMBAI & ANR versus THE STATE OF MAHAR | pages 49, units 168 (167 numbered), opinions 1, unusable pages [] |
| judgment | DR. D.J. DE SOUZA versus MANAGING DIRECTOR CPC DIAGNOSTICS P | pages 4, units 15 (14 numbered), opinions 1, unusable pages [] |
| judgment | DR. S. K. JHUNJHUNWALA versus MRS. DHANWANTI KAUR & ANR. | pages 17, units 58 (57 numbered), opinions 1, unusable pages [] |
| judgment | DR. S. KUMAR & ORS. versus S. RAMALINGAM | pages 10, units 25 (24 numbered), opinions 1, unusable pages [] |
| judgment | DR. VIJAY DIXIT & ORS. versus PAGADAL KRISHNA MOHAN & ORS. | pages 14, units 48 (47 numbered), opinions 2, unusable pages [] |
| judgment | DUNI CHAND versus VIKRAM SINGH AND OTHERS | pages 9, units 23 (22 numbered), opinions 1, unusable pages [] |
| judgment | E.A. ABOOBACKER & ORS. versus STATE OF KERALA & ORS. | pages 19, units 36 (35 numbered), opinions 1, unusable pages [] |
| judgment | ECGC LIMITED versus MOKUL SHRIRAM EPC JV | pages 20, units 48 (47 numbered), opinions 1, unusable pages [] |
| judgment | EIH LIMITED versus NADIAVIRJI | pages 16, units 34 (33 numbered), opinions 1, unusable pages [] |
| judgment | ENFORCEMENT DIRECTORATE GOVERNMENT OF INDIA versus KAPIL WAD | pages 3, units 5 (4 numbered), opinions 1, unusable pages [] |
| judgment | ENFORCEMENT DIRECTORATE, GOVERNMENT OF INDIA versus KAPIL WA | pages 31, units 60 (59 numbered), opinions 1, unusable pages [] |
| judgment | ESSAR HOUSE PRIVATE LIMITED versus ARCELLOR MITTAL NIPPON ST | pages 19, units 55 (54 numbered), opinions 1, unusable pages [] |
| judgment | ESTATE OFFICER AND ANR. versus CHARANJIT KAUR | pages 26, units 50 (49 numbered), opinions 1, unusable pages [] |
| judgment | EXECUTIVE OFFICER, ARULMIGU CHOKKANATHA SWAMY KOIL TRUST VIR | pages 15, units 41 (40 numbered), opinions 1, unusable pages [] |
| judgment | EXPERION DEVELOPERS PVT. LTD versus SUSHMA ASHOK SHIROOR | pages 23, units 48 (47 numbered), opinions 1, unusable pages [] |
| judgment | FAIZABAD-AYODHYA DEVELOPMENT AUTHORITY, FAIZABAD versus DR.  | pages 60, units 100 (99 numbered), opinions 1, unusable pages [] |
| judgment | FARIDABAD COMPLEX ADMINISTRATION versus M/S IRON MASTER INDI | pages 5, units 25 (24 numbered), opinions 1, unusable pages [] |
| judgment | FERRODOUS ESTATES (PVT.) LTD. versus P. GOPIRATHNAM (DEAD) & | pages 59, units 100 (99 numbered), opinions 1, unusable pages [] |
| judgment | FORUM FOR PEOPLE’S COLLECTIVE EFFORTS (FPCE) & ANR. versus T | pages 178, units 190 (183 numbered), opinions 1, unusable pages [38, 40, 42, 44, 46, 48, 50, 52, 54, 56, 58, 60, 62, 64, 66, 68, 70, 72, 74, 76, 78, 80, 82, 84, 86, 88, 90, 92, 94, 96, 100] |
| judgment | G H ASHOK KUMAR KALRA versus WING CDR. SURENDRA AGNIHOTRI &  | pages 33, units 100 (99 numbered), opinions 2, unusable pages [] |
| judgment | G H PAM DEVELOPMENTS PRIVATE LTD. versus STATE OF WEST BENGA | pages 21, units 37 (36 numbered), opinions 1, unusable pages [] |
| judgment | G H RAM LAL & ORS. versus SALIG RAM & ORS. | pages 10, units 22 (21 numbered), opinions 1, unusable pages [] |
| judgment | G H SURINDER PAL SONI versus SOHAN LAL (D) THRU LRS . | pages 16, units 35 (34 numbered), opinions 1, unusable pages [] |
| judgment | G. RATNA RAJ (D) BY LRS. versus SRI MUTHUKUMARASAMY PERMANEN | pages 10, units 40 (39 numbered), opinions 1, unusable pages [] |
| judgment | G. SARASWATHI & ANR. versus RATHINAMMAL & ORS. | pages 5, units 19 (18 numbered), opinions 1, unusable pages [] |
| judgment | G.M. SHAHUL HAMEED versus JAYANTHI R. HEGDE | pages 17, units 38 (37 numbered), opinions 1, unusable pages [] |
| judgment | G.N.R. BABU @ S.N. BABU versus DR. B.C. MUTHAPPA & ORS. | pages 10, units 19 (18 numbered), opinions 1, unusable pages [] |
| judgment | GADDIPATI DIVIJA & ANR. versus PATHURI SAMRAJYAM & ORS. | pages 18, units 42 (41 numbered), opinions 1, unusable pages [] |
| judgment | GANESAN REP BY ITS POWER AGENT G. RUKMANI GANESAN versus THE | pages 41, units 127 (126 numbered), opinions 1, unusable pages [] |
| judgment | GANESH PRASAD versus RAJESHWAR PRASAD AND ORS. | pages 37, units 92 (91 numbered), opinions 1, unusable pages [] |
| judgment | GAS POINT PETROLEUM INDIA LTD. versus RAJENDRA MAROTHI & ORS | pages 10, units 29 (28 numbered), opinions 1, unusable pages [] |
| judgment | GAURAV HARGOVINDBHAI DAVE versus ASSET RECONSTRUCTION COMPAN | pages 4, units 10 (10 numbered), opinions 1, unusable pages [] |
| judgment | GEETA DEVI versus STATE OF U.P. & ORS. | pages 15, units 44 (43 numbered), opinions 1, unusable pages [] |
| judgment | GEO VARGHESE versus THE STATE OF RAJASTHAN & ANR. | pages 23, units 47 (46 numbered), opinions 1, unusable pages [] |
| judgment | GHAT TALAB KAULAN WALA versus BABA GOPAL DASS CHELA SURTI DA | pages 7, units 22 (21 numbered), opinions 1, unusable pages [] |
| judgment | GHEWARCHAND & ORS. versus M/S MAHENDRA SINGH & ORS. | pages 7, units 30 (29 numbered), opinions 1, unusable pages [] |
| judgment | GHULAM HASSAN BEIGH versus MOHAMMAD MAQBOOL MAGREY & ORS. | pages 23, units 46 (45 numbered), opinions 1, unusable pages [] |
| judgment | GIRISH GANDHI versus THE STATE OF UTTAR PRADESH & ORS. | pages 14, units 40 (39 numbered), opinions 1, unusable pages [] |
| judgment | GOA FOUNDATION & ANR. versus STATE OF GOA & ANR. | pages 20, units 46 (45 numbered), opinions 1, unusable pages [] |
| judgment | GODREJ PROJECTS DEVELOPMENT LIMITED versus ANIL KARLEKAR & O | pages 20, units 74 (73 numbered), opinions 1, unusable pages [] |
| judgment | GOVERNMENT OF INDIA versus 1.VEDANTA LIMITED (FORMERLY CAIRN | pages 101, units 199 (198 numbered), opinions 1, unusable pages [] |
| judgment | GOVERNMENT OF NCT DELHI & ORS versus JAI PAL | pages 5, units 17 (16 numbered), opinions 1, unusable pages [] |
| judgment | GOVERNMENT OF NCT DELHI & ORS. versus KRISHAN KUMAR & ORS. | pages 6, units 18 (17 numbered), opinions 1, unusable pages [] |
| judgment | GOVERNMENT OF NCT OF DELHI & ANR versus DAYANAND & ANR. | pages 6, units 18 (17 numbered), opinions 1, unusable pages [] |
| judgment | GOVERNMENT OF NCT OF DELHI & ANR versus MANJEET SINGH ANAND  | pages 6, units 18 (17 numbered), opinions 1, unusable pages [] |
| judgment | GOVERNMENT OF NCT OF DELHI & ANR. versus SH. MANISH & ANR | pages 6, units 16 (15 numbered), opinions 1, unusable pages [] |
| judgment | GOVERNMENT OF NCT OF DELHI & ANR. versus SHAKEEL AHMED & ORS | pages 6, units 16 (15 numbered), opinions 1, unusable pages [] |
| judgment | GOVERNMENT OF NCT OF DELHI AND ANR versus M/S. BEADS PROPERT | pages 3, units 10 (9 numbered), opinions 1, unusable pages [] |
| judgment | GOVERNMENT OF NCT OF DELHI AND ANR. versus KARAMPAL AND ANR. | pages 5, units 17 (16 numbered), opinions 1, unusable pages [] |
| judgment | GOVERNMENT OF NCT OF DELHI AND ANR. versus MOHD. ZUBAIR AND  | pages 5, units 16 (15 numbered), opinions 1, unusable pages [] |
| judgment | GOVERNMENT OF NCT OF DELHI AND ANR. versus SUDESH VERMA AND  | pages 5, units 16 (15 numbered), opinions 1, unusable pages [] |
| judgment | GOVERNMENT OF NCT OF DELHI versus KRISHNA SAINI & ORS. | pages 5, units 16 (15 numbered), opinions 1, unusable pages [] |
| judgment | GOVERNMENT OF NCT OF DELHI versus RATIRAM & ORS. | pages 6, units 20 (19 numbered), opinions 1, unusable pages [] |
| judgment | GOVERNMENT OF NCT OF DELHI versus RAVINDER KUMAR JAIN & ORS. | pages 11, units 16 (15 numbered), opinions 1, unusable pages [] |
| judgment | GOVERNMENT OF NCT OF DELHI versus SIDDHARTH KAPOOR & ORS. | pages 5, units 16 (15 numbered), opinions 1, unusable pages [] |
| judgment | GOVERNMENT OF NCT OF DELHI versus SUBHASH GUPTA & ORS. | pages 6, units 17 (16 numbered), opinions 1, unusable pages [] |
| judgment | GOVERNMENT OF NCT OF DELHI versus SUBHASH JAIN AND ORS. | pages 5, units 16 (15 numbered), opinions 1, unusable pages [] |
| judgment | GOVERNMENT OF NCT OF DELHI versus VIJAY GUPTA & ORS | pages 3, units 9 (8 numbered), opinions 1, unusable pages [] |
| judgment | GOVT OF NCT OF DELHI THROUGH SECRETARY, LAND AND BUILDING DE | pages 6, units 19 (18 numbered), opinions 1, unusable pages [] |
| judgment | GOVT. OF NCT DELHI & ANR versus DINESH KUMAR & ANR | pages 3, units 9 (8 numbered), opinions 1, unusable pages [] |
| judgment | GOVT. OF NCT DELHI & ORS. versus DHANNU & ANR | pages 5, units 17 (16 numbered), opinions 1, unusable pages [] |
| judgment | GOVT. OF NCT OF DELHI & ANR versus MANJEET KAUR & ANR. | pages 6, units 18 (17 numbered), opinions 1, unusable pages [] |
| judgment | GOVT. OF NCT OF DELHI & ANR. versus BHAGRATI & ANR | pages 6, units 18 (17 numbered), opinions 1, unusable pages [] |
| judgment | GOVT. OF NCT OF DELHI & ANR. versus KHAJAN SINGH & ANR. | pages 6, units 17 (16 numbered), opinions 1, unusable pages [] |
| judgment | GOVT. OF NCT OF DELHI & ANR. versus RATI RAM & ANR. | pages 6, units 20 (19 numbered), opinions 1, unusable pages [] |
| judgment | GOVT. OF NCT OF DELHI & ANR. versus SH. NARENDER & ANR. | pages 6, units 16 (15 numbered), opinions 1, unusable pages [] |
| judgment | GOVT. OF NCT OF DELHI AND ANOTHER versus MAHENDER SINGH AND  | pages 9, units 21 (20 numbered), opinions 1, unusable pages [] |
| judgment | GOVT. OF NCT OF DELHI AND ANR. versus SHIV DUTT SHARMA AND A | pages 6, units 18 (17 numbered), opinions 1, unusable pages [] |
| judgment | GOVT. OF NCT OF DELHI versus MOHD. MAQBOOL & ORS | pages 7, units 19 (18 numbered), opinions 1, unusable pages [] |
| judgment | GOVT. OF NCT OF DELHI versus SUNIL JAIN & ORS | pages 6, units 17 (16 numbered), opinions 1, unusable pages [] |
| judgment | GOVT. OF NCT OF DELHI versus SUSHIL KUMAR GUPTA & ORS. | pages 6, units 18 (17 numbered), opinions 1, unusable pages [] |
| judgment | GREATER NOLDA IND. DEV. AUTHORITY versus SAVJTRI MOHAN (DEAD | pages 11, units 26 (25 numbered), opinions 1, unusable pages [] |
| judgment | GURCHARAN SINGH & ORS. versus ANGREZ KAUR & ANR. | pages 17, units 33 (32 numbered), opinions 1, unusable pages [] |
| judgment | GURMIT SINGH BHATIA versus KIRAN KANT ROBINSON AND OTHERS | pages 13, units 19 (18 numbered), opinions 1, unusable pages [] |
| judgment | GURNAM SINGH (D) BY LRS. & ORS. versus LEHNA SINGH (D) BY LR | pages 15, units 46 (45 numbered), opinions 1, unusable pages [] |
| judgment | GURNAM SINGH (D) THR. LRS. versus GURBACHAN KAUR (D) BY LRS. | pages 8, units 25 (24 numbered), opinions 1, unusable pages [] |
| judgment | H. D. SUNDARA & ORS. versus STATE OF KARNATAKA | pages 8, units 17 (16 numbered), opinions 1, unusable pages [] |
| judgment | H. K. SINGLA versus AVTAR SINGH SAINI & ORS. | pages 4, units 14 (13 numbered), opinions 1, unusable pages [] |
| judgment | H. S. GOUTHAM versus RAMA MURTHY AND ANR. ETC. | pages 23, units 40 (39 numbered), opinions 1, unusable pages [] |
| judgment | HAMID ALI KHAN (D) THROUGH LRS. & ANR. versus STATE OF U.P.  | pages 39, units 71 (70 numbered), opinions 1, unusable pages [] |
| judgment | HAR NARAYAN TEWARI (D) THR. LRS. versus CANTONMENT BOARD, RA | pages 12, units 39 (38 numbered), opinions 1, unusable pages [] |
| judgment | HARI RAM (DECEASED) THR. HIS LRS. AND ANR. versus LAND ACQUI | pages 6, units 9 (8 numbered), opinions 1, unusable pages [] |
| judgment | HARI STEEL AND GENERAL INDUSTRIES LTD. & ANR. versus DALJIT  | pages 26, units 52 (51 numbered), opinions 1, unusable pages [] |
| judgment | HARYANA STATE INDUSTRIAL & INFRASTRUCTURE DEVELOPMENT CORPOR | pages 10, units 33 (32 numbered), opinions 1, unusable pages [] |
| judgment | HARYANA STATE INDUSTRIAL AND INFRASTRUCTURE DEVELOPEMNT CORP | pages 13, units 39 (38 numbered), opinions 2, unusable pages [] |
| judgment | HARYANA STATE INDUSTRIAL AND INFRASTRUCTURE DEVELOPMENT CORP | pages 27, units 49 (48 numbered), opinions 1, unusable pages [] |
| judgment | HARYANA STATE INDUSTRIAL AND INFRASTRUCTURE DEVELOPMENT CORP | pages 7, units 13 (12 numbered), opinions 1, unusable pages [] |
| judgment | HASMAT ALI versus AMINA BIBI & ORS. | pages 9, units 22 (21 numbered), opinions 1, unusable pages [] |
| judgment | HASMUKHLAL D. VORA & ANR. versus THE STATE OF TAMIL NADU | pages 13, units 34 (33 numbered), opinions 1, unusable pages [] |
| judgment | HEMANTHA KUMAR versus R. MAHADEVAIAH & ORS. | pages 7, units 20 (19 numbered), opinions 1, unusable pages [] |
| judgment | HEMAREDDI (D) THROUGH LRS. versus RAMACHANDRA YALLAPPA HOSMA | pages 25, units 53 (52 numbered), opinions 1, unusable pages [] |
| judgment | HEMAVATHI AND ORS. versus V. HOMBEGOWDA AND ANR. | pages 11, units 27 (0 numbered), opinions 1, unusable pages [] |
| judgment | HEMIBEN LADHABHAI BHANDERI versus SAURASHTA GRAMIN BANK & AN | pages 6, units 12 (11 numbered), opinions 1, unusable pages [] |
| judgment | HITESH UMESHBHAI MASHRU versus THE STATE OF GUJARAT & ANR. | pages 3, units 12 (11 numbered), opinions 1, unusable pages [] |
| judgment | HONNAIAH T.H. versus STATE OF KARNATAKA AND OTHERS | pages 13, units 26 (25 numbered), opinions 1, unusable pages [] |
| judgment | HUDA versus VIDYA CHETAL | pages 16, units 36 (35 numbered), opinions 1, unusable pages [] |
| judgment | HYUNDAI MOTOR INDIA LIMITED versus SHAILENDRA BHATNAGAR | pages 14, units 21 (20 numbered), opinions 1, unusable pages [] |
| judgment | IDBI TRUSTEESHIP SERVICES LTD. versus HUBTOWN LTD. | pages 40, units 73 (72 numbered), opinions 1, unusable pages [] |
| judgment | IFFCO TOKIO GENERAL INSURANCE COMPANY LTD. versus PEARL BEVE | pages 100, units 179 (178 numbered), opinions 1, unusable pages [] |
| judgment | IL AND FS ENGINEERING AND CONSTRUCTIONS COMPANY LTD. versus  | pages 5, units 9 (8 numbered), opinions 1, unusable pages [] |
| judgment | IN RE: FRAMING GUIDELINES REGARDING POTENTIAL MITIGATING CIR | pages 22, units 61 (60 numbered), opinions 1, unusable pages [] |
| judgment | IN RE: INTERPLAY BETWEEN ARBITRATION AGREEMENTS UNDER THE AR | pages 132, units 337 (335 numbered), opinions 1, unusable pages [] |
| judgment | INDIAN EVANGELICAL LUTHERAN CHURCH TRUST ASSOCIATION versus  | pages 34, units 56 (55 numbered), opinions 1, unusable pages [] |
| judgment | INDIAN MACHINERY COMPANY versus M/S. ANSAL HOUSING & CONSTRU | pages 3, units 10 (9 numbered), opinions 1, unusable pages [] |
| judgment | INDIAN OIL CORPORATION LIMITED versus STATE OF U.P. & ORS. | pages 37, units 82 (81 numbered), opinions 1, unusable pages [] |
| judgment | INDORE DEVELOPMENT AUTHORITY versus BURHANI GRIH NIRMAN SAHA | pages 35, units 81 (80 numbered), opinions 1, unusable pages [] |
| judgment | INDORE DEVELOPMENT AUTHORITY versus MANOHARLAL & ORS. ETC. | pages 328, units 596 (595 numbered), opinions 1, unusable pages [] |
| judgment | INDORE DEVELOPMENT AUTHORITY versus SHAILENDRA (DEAD) THROUG | pages 231, units 413 (412 numbered), opinions 1, unusable pages [] |
| judgment | INDRA DEVI versus STATE OF RAJASTHAN & ANR. | pages 8, units 13 (12 numbered), opinions 1, unusable pages [] |
| judgment | INFRASTRUCTURE LEASING AND FINANCIAL SERVICES LTD versus HDF | pages 25, units 65 (64 numbered), opinions 1, unusable pages [] |
| judgment | INTERNATIONAL ASSET RECONSTRUCTION COMPANY OF A INDIA LTD ve | pages 9, units 24 (23 numbered), opinions 1, unusable pages [] |
| judgment | ISHWAR (SINCE DECEASED) THR. LRS & ORS. versus BHIM SINGH &  | pages 15, units 26 (25 numbered), opinions 1, unusable pages [] |
| judgment | ISTKAR versus THE STATE OF UTTAR PRADESH & ANR. | pages 18, units 39 (38 numbered), opinions 1, unusable pages [] |
| judgment | J. BALAJI SINGH versus DIWAKAR COLE & ORS. | pages 9, units 35 (34 numbered), opinions 1, unusable pages [] |
| judgment | J. VEDHASINGH versus R.M. GOVINDAN & ORS. | pages 13, units 23 (22 numbered), opinions 1, unusable pages [] |
| judgment | JACOB PUNNEN & ANR. versus UNITED INDIA INSURANCE CO. LTD. | pages 34, units 83 (82 numbered), opinions 2, unusable pages [] |
| judgment | JAFARUDHEEN & ORS. versus STATE OF KERALA | pages 39, units 73 (72 numbered), opinions 1, unusable pages [] |
| judgment | JAGJEET SINGH & ORS versus ASHISH MISHRA @ MONU & ANR. | pages 20, units 58 (57 numbered), opinions 1, unusable pages [] |
| judgment | JAGJIWAN COOP. GROUP HOUSING SOCIETY LTD. & ORS. versus LT.  | pages 3, units 7 (6 numbered), opinions 1, unusable pages [] |
| judgment | JAHIR HAK versus THE STATE OF RAJASTHAN | pages 6, units 23 (0 numbered), opinions 1, unusable pages [] |
| judgment | JAI PARKASH ETC ETC versus UNION TERRITORY, CHANDIGARH ETC E | pages 4, units 13 (12 numbered), opinions 1, unusable pages [] |
| judgment | JAI PRAKASH TIWARI versus STATE OF MADHYA PRADESH | pages 17, units 51 (50 numbered), opinions 1, unusable pages [] |
| judgment | JAMES KUNJWAL versus STATE OF UTTARAKHAND & ANR. | pages 13, units 38 (37 numbered), opinions 1, unusable pages [] |
| judgment | JANARDAN DAS & ORS. versus DURGA PRASAD AGARWALLA & ORS. | pages 16, units 39 (38 numbered), opinions 1, unusable pages [] |
| judgment | JASPAL SINGH & OTHERS versus THE STATE OF HARYANA AND OTHERS | pages 8, units 23 (22 numbered), opinions 1, unusable pages [] |
| judgment | JASWANT SINGH & ORS versus PARK.ASH KAUR & ANR | pages 33, units 93 (92 numbered), opinions 1, unusable pages [] |
| judgment | JASWANT SINGH & ORS versus THE STATE OF CHHATTISGARH & ANR. | pages 6, units 10 (9 numbered), opinions 1, unusable pages [] |
| judgment | JASWANT SINGH versus STATE OF PUNJAB & ANR. | pages 13, units 29 (28 numbered), opinions 1, unusable pages [] |
| judgment | JASWINDER KAUR (NOW DECEASED) THROUGH . versus GURMEET SINGH | pages 14, units 30 (29 numbered), opinions 1, unusable pages [] |
| judgment | JAYAKANTHAM & OTHERS versus ABAYKUMAR | pages 10, units 23 (22 numbered), opinions 1, unusable pages [] |
| judgment | JAYANTILAL CHIMANLAL PATEL versus VADILAL PURUSHOTTAMDAS PAT | pages 7, units 17 (16 numbered), opinions 1, unusable pages [] |
| judgment | JAYAPRAKASH & ANR. versus T. S. DAVID & ORS. | pages 5, units 26 (25 numbered), opinions 1, unusable pages [] |
| judgment | JAYEDEEPSINH PRAVINSINH CHAVDA & ORS. versus STATE OF GUJARA | pages 14, units 37 (36 numbered), opinions 1, unusable pages [] |
| judgment | JIGAR @ JIMMY PRAVINCHANDRA ADATIYA versus STATE OF GUJARAT | pages 36, units 57 (33 numbered), opinions 1, unusable pages [] |
| judgment | JIGNESH SHAH & ANR. versus UNION OF INDIA & ANR. | pages 33, units 63 (62 numbered), opinions 1, unusable pages [] |
| judgment | JINI DHANRAJGIR & ANR versus SHIBU MATHEW & ANR. ETC. | pages 20, units 42 (41 numbered), opinions 1, unusable pages [] |
| judgment | JITEN K. AJMERA & ANR. versus M/S TEJAS CO-OPERATIVE HOUSING | pages 5, units 27 (26 numbered), opinions 1, unusable pages [] |
| judgment | JITENDRA NATH MISHRA versus STATE OF U.P. & ANR | pages 6, units 21 (20 numbered), opinions 1, unusable pages [] |
| judgment | JITUL JENTILAL KOTECHA versus STATE OF GUJARAT AND ORS. ETC | pages 28, units 48 (47 numbered), opinions 1, unusable pages [] |
| judgment | JOSEPH STEPHEN AND OTHERS versus SANTHANASAMY AND OTHERS | pages 16, units 36 (35 numbered), opinions 1, unusable pages [] |
| judgment | JUDGEBIR SINGH @ JASBIR SINGH SAMRA @ JASBIR & ORS. versus N | pages 55, units 152 (151 numbered), opinions 1, unusable pages [] |
| judgment | JUHRU & ORS versus KARIM & ANR. | pages 10, units 32 (31 numbered), opinions 1, unusable pages [] |
| judgment | JYOTI DEVI versus SUKET HOSPITAL & ORS. | pages 19, units 32 (31 numbered), opinions 1, unusable pages [] |
| judgment | K. ARUMUGA VELAIAH versus P.R. RAMASAMY AND ANR. | pages 32, units 69 (68 numbered), opinions 1, unusable pages [] |
| judgment | K. BHARTHI DEVI AND ANR. versus STATE OF TELANGANA AND ANR. | pages 23, units 62 (61 numbered), opinions 1, unusable pages [] |
| judgment | K. L. SUNEJA & ANR versus DR. (MRS.) MANJEET KAUR MONGA (D)  | pages 20, units 46 (45 numbered), opinions 1, unusable pages [] |
| judgment | K. N. NAGARAJAPPA & ORS. versus H. NARASIMHA REDDY | pages 11, units 23 (22 numbered), opinions 1, unusable pages [] |
| judgment | K. P. NATARAJAN & ANR. versus MUTHALAMMAL & ORS. | pages 18, units 49 (48 numbered), opinions 1, unusable pages [] |
| judgment | K. RAVI versus STATE OF TAMIL NADU & ANR. | pages 9, units 16 (15 numbered), opinions 1, unusable pages [] |
| judgment | K. SRINIVASAPPA & ORS. versus M. MALLAMMA & ORS. | pages 19, units 62 (61 numbered), opinions 1, unusable pages [] |
| judgment | K. SUBBARAYUDU AND OTHERS versus THE SPECIAL DEPUTY COLLECTO | pages 9, units 19 (18 numbered), opinions 1, unusable pages [] |
| judgment | K. VADIVEL versus K. SHANTHI & ORS. | pages 17, units 61 (60 numbered), opinions 1, unusable pages [] |
| judgment | K.B. LAL (KRISHNA BAHADUR LAL) versus GYANENDRA PRATAP & ORS | pages 8, units 14 (13 numbered), opinions 1, unusable pages [] |
| judgment | K.C. LAXMANA versus K.C. CHANDRAPPA GOWDA & ANR. | pages 11, units 25 (24 numbered), opinions 1, unusable pages [] |
| judgment | K.P. KHEMKA & ANR. versus HARYANA STATE INDUSTRIAL AND INFRA | pages 25, units 52 (51 numbered), opinions 1, unusable pages [] |
| judgment | K.S. MEHTA versus M/S MORGAN SECURITIES AND CREDITS PVT. LTD | pages 10, units 27 (26 numbered), opinions 1, unusable pages [] |
| judgment | K.S. SANJEEV (DEAD) BY LRS. ETC. ETC. versus STATE OF KERALA | pages 3, units 8 (6 numbered), opinions 1, unusable pages [] |
| judgment | KAILASH VIJAYVARGIYA versus RAJLAKSHMI CHAUDHURI AND OTHERS | pages 40, units 100 (99 numbered), opinions 1, unusable pages [] |
| judgment | KALICHARAN & ORS versus STATE OF UTTAR PRADESH | pages 17, units 41 (40 numbered), opinions 1, unusable pages [] |
| judgment | KAMAL KANT JAIN versus SURINDER SINGH (D) THR. LRS. | pages 13, units 35 (34 numbered), opinions 1, unusable pages [] |
| judgment | KANAILAL & ORS. versus RAM CHANDRA SINGH & ORS. | pages 6, units 24 (23 numbered), opinions 1, unusable pages [] |
| judgment | KANAKLATA DAS & ORS. versus NABA KUMAR DAS & ORS. | pages 8, units 31 (30 numbered), opinions 1, unusable pages [] |
| judgment | KANCHAN KUMAR versus THE STATE OF BIHAR | pages 12, units 35 (34 numbered), opinions 1, unusable pages [] |
| judgment | KANCHAN KUMARI versus THE STATE OF BIHAR & ANR. | pages 3, units 9 (8 numbered), opinions 1, unusable pages [] |
| judgment | KANCHAN UDYOG LIMITED versus UNITED SPIRITS LIMITED | pages 19, units 46 (45 numbered), opinions 1, unusable pages [] |
| judgment | KANIHYA @ KANHI (DEAD) THROUGH LRS. versus SUKHI RAM & ORS. | pages 11, units 33 (32 numbered), opinions 1, unusable pages [] |
| judgment | KANIMOZHI KARUNANIDHI versus A. SANTHANA KUMAR & ORS | pages 31, units 56 (55 numbered), opinions 1, unusable pages [] |
| judgment | KAPTAN SINGH versus THE STATE OF UTTAR PRADESH AND OTHERS | pages 14, units 29 (28 numbered), opinions 1, unusable pages [] |
| judgment | KARAN KAPOOR versus MADHURI KUMAR | pages 16, units 28 (26 numbered), opinions 1, unusable pages [] |
| judgment | KARNATAKA HOUSING BOARD versus K. A. NAGAMANI | pages 16, units 79 (78 numbered), opinions 1, unusable pages [] |
| judgment | KARUNA KANSAL versus HEMANT KANSAL & ANR. | pages 5, units 18 (17 numbered), opinions 1, unusable pages [] |
| judgment | KAUSHIK NARSINHBHAI PATEL & ORS. versus M/S S.J.R. PRIME COR | pages 17, units 28 (27 numbered), opinions 1, unusable pages [] |
| judgment | KAZI MOINUDDIN KAZI BASHIRODDIN & ORS. versus THE MAHARASHTR | pages 13, units 34 (33 numbered), opinions 1, unusable pages [] |
| judgment | KEDAR NATH YADAV versus STATE OF WEST BENGAL & ORS. | pages 156, units 417 (416 numbered), opinions 1, unusable pages [] |
| judgment | KHATEMA FIBRES LTD. versus NEW INDIA ASSURANCE COMPANY LTD.  | pages 16, units 47 (46 numbered), opinions 1, unusable pages [] |
| judgment | KHATOON & ORS. versus THE STATE OF U.P. THROUGH PRINCIPAL SE | pages 15, units 57 (56 numbered), opinions 1, unusable pages [] |
| judgment | KIM WANSOO versus STATE OF UTTAR PRADESH & ORS. | pages 11, units 20 (19 numbered), opinions 1, unusable pages [] |
| judgment | KIRPA RAM (DECEASED) THROUGH LEGAL REPRESENTATIVES & ORS. ve | pages 14, units 37 (36 numbered), opinions 1, unusable pages [] |
| judgment | KIRPAL KAUR AND ANOTHER versus RITESH AND OTHERS | pages 9, units 26 (25 numbered), opinions 1, unusable pages [] |
| judgment | KISHOR GHANSHYAMSA PARALIKAR (DEAD) versus BALAJI MANDIR SAN | pages 5, units 18 (17 numbered), opinions 1, unusable pages [] |
| judgment | KORUKONDA CHALAPATHI RAO & ANR. versus KORUKONDA ANNAPURNA S | pages 24, units 66 (65 numbered), opinions 1, unusable pages [] |
| judgment | KOTAK MAHINDRA BANK LIMITED versus KEW PRECISION PARTS PRIVA | pages 30, units 81 (80 numbered), opinions 1, unusable pages [] |
| judgment | KRISHNA DEVI @ SABITRI DEVI (RANI) M/S S.R. ENGINEERING CONS | pages 12, units 31 (30 numbered), opinions 1, unusable pages [] |
| judgment | KUM. GEETHA, D/O LATE KRISHNA & ORS. versus NANJUNDASWAMY &  | pages 11, units 27 (26 numbered), opinions 1, unusable pages [] |
| judgment | KUMER SINGH versus STATE OF RAJASTHAN & ANR | pages 23, units 65 (64 numbered), opinions 1, unusable pages [] |
| judgment | KUMUD W/O MAHADEORAO SALUNKE versus SHRI PANDURANG NARAYAN G | pages 6, units 16 (15 numbered), opinions 1, unusable pages [] |
| judgment | LAKHAN SINGH versus AMARJEET SINGH & ANR | pages 9, units 35 (33 numbered), opinions 1, unusable pages [] |
| judgment | LALDHARI MISTRI (DEAD) THR. LRS. & ANR. versus VIJAY KUMAR | pages 4, units 15 (14 numbered), opinions 1, unusable pages [] |
| judgment | LALITESHWAR PRASAD SINGH & ORS. versus S. P. SRIVASTAVA (D)  | pages 14, units 32 (30 numbered), opinions 1, unusable pages [] |
| judgment | LALU YADAV versus THE STATE OF UTTAR PRADESH & ORS. | pages 11, units 20 (19 numbered), opinions 1, unusable pages [] |
| judgment | LAND & BUILDING DEPARTMENT & ANR. versus MANISH SETHI AND OR | pages 5, units 16 (15 numbered), opinions 1, unusable pages [] |
| judgment | LAND ACQUISITION COLLECTOR & ANR. versus ASHOK KUMAR & ORS. | pages 6, units 18 (17 numbered), opinions 1, unusable pages [] |
| judgment | LAND ACQUISITION COLLECTOR (SOUTH EAST) versus DHARAMVIR AND | pages 5, units 16 (15 numbered), opinions 1, unusable pages [] |
| judgment | LAND ACQUISITION COLLECTOR (SOUTH) versus HARI CHAND AND ANR | pages 5, units 17 (16 numbered), opinions 1, unusable pages [] |
| judgment | LAND ACQUISITION COLLECTOR (SOUTH), NEW DELHI AND ANR. versu | pages 9, units 34 (33 numbered), opinions 1, unusable pages [] |
| judgment | LAND ACQUISITION COLLECTOR AND ANR. versus B. S. DHILLION &  | pages 5, units 16 (15 numbered), opinions 1, unusable pages [] |
| judgment | LAND ACQUISITION COLLECTOR versus JAI PRAKASH TYAGI & ORS. | pages 6, units 17 (16 numbered), opinions 1, unusable pages [] |
| judgment | LAND AND BUILDING DEPARTMENT THR. SECRETARY & ANR versus ATT | pages 9, units 24 (23 numbered), opinions 1, unusable pages [] |
| judgment | LAND AND BUILDING DEPARTMENT THROUGH SECRETARY, GOVERNMENT O | pages 5, units 17 (16 numbered), opinions 1, unusable pages [] |
| judgment | LIFE INSURANCE CORPORATION OF INDIA versus SANJEEV BUILDERS  | pages 45, units 120 (119 numbered), opinions 1, unusable pages [] |
| judgment | LILAVATI KIRTILAL MEHTA MEDICAL TRUST versus M/S UNIQUE SHAN | pages 16, units 33 (32 numbered), opinions 1, unusable pages [] |
| judgment | LILAWATI AGARWAL ETC. versus THE STATE OF JHARKHAND ETC. | pages 13, units 18 (17 numbered), opinions 1, unusable pages [] |
| judgment | LOONKARAN GANDHI (D) THR. LR. versus STATE OF MAHARASHTRA AN | pages 24, units 40 (39 numbered), opinions 1, unusable pages [] |
| judgment | LOOP TELECOM AND TRADING LIMITED versus UNION OF INDIA AND A | pages 60, units 124 (122 numbered), opinions 1, unusable pages [] |
| judgment | LUCKNOW DEVELOPMENT AUTHORITY versus MEHDI HASAN (DECEASED)  | pages 5, units 18 (17 numbered), opinions 1, unusable pages [] |
| judgment | LUCKOSE ZACHARIAH @ ZAK NEDUMCHIRA LUKE AND OTHERS versus JO | pages 8, units 25 (24 numbered), opinions 1, unusable pages [] |
| judgment | M.P. HOUSING BOARD & ANR. versus SATISH KUMAR BATRA AND ORS | pages 5, units 16 (15 numbered), opinions 1, unusable pages [] |
| judgment | M/S ACME CLEANTECH SOLUTIONS PRIVATE LIMITED versus M/S UNIT | pages 8, units 26 (25 numbered), opinions 1, unusable pages [] |
| judgment | M/S ACQUAINTED REALTORS LLP ETC. ETC. versus STATE OF HARYAN | pages 17, units 36 (35 numbered), opinions 1, unusable pages [] |
| judgment | M/S ALCON ELECTRONICS PVT. LTD. versus CELEM S.A. OF FOS 343 | pages 17, units 45 (44 numbered), opinions 1, unusable pages [] |
| judgment | M/S ANJANEYA JEWELLERY versus NEW INDIA ASSURANCE CO.LTD. &  | pages 3, units 19 (18 numbered), opinions 1, unusable pages [] |
| judgment | M/S ARIF AZIM CO. LTD. versus M/S APTECH LTD. | pages 54, units 77 (0 numbered), opinions 1, unusable pages [] |
| judgment | M/S BASPA ORGANICS LIMITED versus UNITED INDIA INSURANCE COM | pages 16, units 62 (61 numbered), opinions 1, unusable pages [] |
| judgment | M/S BHAGWANDAS B. RAMCHANDANI versus BRITISH AIRWAYS | pages 46, units 97 (96 numbered), opinions 1, unusable pages [] |
| judgment | M/S BHARAT PETROLEUM CORPORATION LTD. AND ANOTHER versus ATM | pages 13, units 31 (30 numbered), opinions 1, unusable pages [] |
| judgment | M/S CHAKRESHWARI CONSTRUCTION PVT. LTD. versus MANOHAR LAL | pages 7, units 26 (25 numbered), opinions 1, unusable pages [] |
| judgment | M/S DADDY’S BUILDERS PVT. LTD. & ANOTHER versus MANISHA BHAR | pages 4, units 9 (8 numbered), opinions 1, unusable pages [] |
| judgment | M/S DAIMLER CHRYSLER INDIA PVT. LTD. versus M/S CONTROLS & S | pages 27, units 47 (46 numbered), opinions 1, unusable pages [] |
| judgment | M/S DELHI AIRTECH SERVICES PVT. LTD & ANR. versus STATE OF U | pages 24, units 40 (39 numbered), opinions 1, unusable pages [] |
| judgment | M/S EXL CAREERS AND ANOTHER versus FRANKFINN AVIATION SERVIC | pages 14, units 39 (38 numbered), opinions 1, unusable pages [] |
| judgment | M/S FROST INTERNATIONAL LIMITED versus M/S MILAN DEVELOPERS  | pages 38, units 69 (68 numbered), opinions 1, unusable pages [] |
| judgment | M/S IREO PRIVATE LIMITED versus ALOKE ANAND AND OTHERS | pages 15, units 38 (37 numbered), opinions 1, unusable pages [] |
| judgment | M/S KAUSHIK COOP. BUILDING SOCIETY versus N. PARVATHAMMA & O | pages 12, units 30 (29 numbered), opinions 1, unusable pages [] |
| judgment | M/S KOHINOOR TRANSPORTERS versus STATE OF UTTAR PRADESH | pages 4, units 13 (12 numbered), opinions 1, unusable pages [] |
| judgment | M/S KOHINOOR TRANSPORTERS versus STATE OF UTTAR PRADESH | pages 4, units 13 (12 numbered), opinions 1, unusable pages [] |
| judgment | M/S MONGIA REALTY AND BUILDWELL PRIVATE LIMITED versus MANIK | pages 8, units 21 (20 numbered), opinions 1, unusable pages [] |
| judgment | M/S N. N. GLOBAL MERCANTILE PRIVATE LIMITED versus M/S INDO  | pages 208, units 603 (409 numbered), opinions 1, unusable pages [] |
| judgment | M/S NANDAN BIOMATRIX LTD. versus S.AMBIKA DEVI & ORS. | pages 16, units 42 (41 numbered), opinions 1, unusable pages [] |
| judgment | M/S NEERJA REALTORS PVT LTD versus JANGLU (DEAD) THR. LR. | pages 9, units 24 (23 numbered), opinions 1, unusable pages [] |
| judgment | M/S NEWS INDIA ASSURANCE CO. LTD. versus M/S LUXRA ENTERPRIS | pages 15, units 32 (31 numbered), opinions 1, unusable pages [] |
| judgment | M/S NORTH EASTERN CHEMICALS INDUSTRIES (P) LTD. & ANR versus | pages 20, units 52 (0 numbered), opinions 1, unusable pages [] |
| judgment | M/S PREM COTTEX versus UTTAR HARYANA BIJLI VITRAN NIGAM LTD. | pages 12, units 30 (29 numbered), opinions 1, unusable pages [] |
| judgment | M/S RAPTAKOS, BRETT & CO. LTD. versus M/S GANESH PROPERTY | pages 15, units 30 (29 numbered), opinions 1, unusable pages [] |
| judgment | M/S SCG CONTRACTS INDIA PVT. LTD. versus K. S. CHAMANKAR INF | pages 10, units 27 (26 numbered), opinions 1, unusable pages [] |
| judgment | M/S SHANTI CONDUCTORS (P) LTD. versus ASSAM STATE ELECTRICIT | pages 23, units 34 (33 numbered), opinions 1, unusable pages [] |
| judgment | M/S SUNEJA TOWERS PRIVATE LIMITED & ANR. versus ANITA MERCHA | pages 60, units 102 (100 numbered), opinions 1, unusable pages [] |
| judgment | M/S SUVARNA COOPERATIVE BANK LTD. versus STATE OF KARNATAKA  | pages 5, units 12 (11 numbered), opinions 1, unusable pages [] |
| judgment | M/S TEXCO MARKETING PVT. LTD. versus TATA AIG GENERAL INSURA | pages 32, units 81 (80 numbered), opinions 1, unusable pages [] |
| judgment | M/S TRL KROSAKI REFRACTORIES LTD versus M/S SMS ASIA PRIVATE | pages 19, units 29 (28 numbered), opinions 1, unusable pages [] |
| judgment | M/S ULTRA-TECH CEMENT LTD. versus MAST RAM & ORS. | pages 30, units 43 (42 numbered), opinions 1, unusable pages [] |
| judgment | M/S. BLS INFRASTRUCTURE LIMITED versus M/S. RAJWANT SINGH &  | pages 8, units 26 (25 numbered), opinions 1, unusable pages [] |
| judgment | M/S. BRAKEWEL AUTOMOTIVE COMPONENTS (INDIA) PVT. LTD. versus | pages 10, units 26 (0 numbered), opinions 1, unusable pages [] |
| judgment | M/S. CHEMINOVA INDIA LTD. & ANR. versus STATE OF PUNJAB & AN | pages 8, units 12 (11 numbered), opinions 1, unusable pages [] |
| judgment | M/S. CHITRALEKHA BUILDERS & ANR. THROUGH ANIL G. SHAH POWER  | pages 13, units 51 (50 numbered), opinions 1, unusable pages [] |
| judgment | M/S. EMAAR MGF LAND LIMITED versus AFTAB SINGH | pages 37, units 85 (84 numbered), opinions 1, unusable pages [] |
| judgment | M/S. FORTUNE INFRASTRUCTURE (NOW KNOWN AS M/S. HICON INFRAST | pages 14, units 35 (34 numbered), opinions 1, unusable pages [] |
| judgment | M/S. IMPERIA STRUCTURES LTD. versus ANIL PATNI AND ANOTHER | pages 38, units 56 (55 numbered), opinions 1, unusable pages [] |
| judgment | M/S. JERMYN CAPITAL LLC DUBAI versus CENTRAL BUREAU OF INVES | pages 5, units 21 (20 numbered), opinions 1, unusable pages [] |
| judgment | M/S. MAGMA FINCORP LTD. versus RAJESH KUMAR TIWARI | pages 58, units 121 (120 numbered), opinions 1, unusable pages [] |
| judgment | M/S. MEENA DEVI JINDAL MEDICAL INSTITUTE & RESEARCH CENTRE v | pages 9, units 25 (24 numbered), opinions 1, unusable pages [] |
| judgment | M/S. MODEL ECONOMIC TOWNSHIP LTD. versus LAND ACQUISITION CO | pages 9, units 18 (17 numbered), opinions 1, unusable pages [] |
| judgment | M/S. NEWTECH PROMOTERS AND DEVELOPERS PVT. LTD. versus STATE | pages 69, units 168 (167 numbered), opinions 1, unusable pages [] |
| judgment | M/S. PATEL BROTHERS versus STATE OF ASSAM AND ORS. | pages 13, units 29 (28 numbered), opinions 1, unusable pages [] |
| judgment | M/S. RADHA EXPORTS (INDIA) PVT. LIMITED versus K.P. JAYARAM  | pages 19, units 55 (54 numbered), opinions 1, unusable pages [] |
| judgment | M/S. SESHASAYEE STEELS P. LTD. versus ASSISTANT COMMISSIONER | pages 11, units 30 (29 numbered), opinions 1, unusable pages [] |
| judgment | M/S. SILPI INDUSTRIES ETC. versus KERALA STATE ROAD TRANSPOR | pages 31, units 63 (62 numbered), opinions 1, unusable pages [] |
| judgment | M/S. SONELL CLOCKS AND GIFTS LTD. versus THE NEW INDIA ASSUR | pages 15, units 39 (38 numbered), opinions 1, unusable pages [] |
| judgment | M/S. SREE SURYA DEVELOPERS AND PROMOTERS versus N. SAILESH P | pages 18, units 42 (41 numbered), opinions 1, unusable pages [] |
| judgment | M/S. SS GROUP PVT. LTD. versus AADITIYA J. GARG & ANR. | pages 4, units 15 (0 numbered), opinions 1, unusable pages [] |
| judgment | M/S. SUNDARAM FINANCE LIMITED versus NOORJAHAN BEEVI AND ANO | pages 14, units 36 (35 numbered), opinions 1, unusable pages [] |
| judgment | M/S. SUPREME BHIWANDI WADA MANOR INFRASTRUCTURE PVT. LTD. ve | pages 14, units 41 (40 numbered), opinions 1, unusable pages [] |
| judgment | M/S. SURYACHAKRA POWER CORPORATION LIMITED versus ELECTRICIT | pages 7, units 15 (14 numbered), opinions 1, unusable pages [] |
| judgment | M/S. VINAYAK HOUSE BUILDING COOPERATIVESOCIETY LTD. versus T | pages 27, units 89 (88 numbered), opinions 1, unusable pages [] |
| judgment | M/S. Z. ENGINEERS CONSTRUCTION PVT. LTD. & ANR versus BIPIN  | pages 8, units 19 (18 numbered), opinions 1, unusable pages [] |
| judgment | MADANURI SRI RAMA CHANDRA MURTHY versus SYED JALAL | pages 20, units 39 (38 numbered), opinions 1, unusable pages [] |
| judgment | MADHAV PRASAD AGGARWAL & ANR. versus AXIS BANK LTD. & ANR. | pages 13, units 23 (22 numbered), opinions 1, unusable pages [] |
| judgment | MADHUKAR NIVRUTTI JAGTAP & ORS. versus SMT. PRAMILABAI CHAND | pages 42, units 64 (63 numbered), opinions 1, unusable pages [] |
| judgment | MADHYA PRADESH ROAD DEVELOPMENT CORPORATION versus VINCENT D | pages 32, units 52 (51 numbered), opinions 1, unusable pages [] |
| judgment | MADINA BEGUM & ANR. versus SHIV MURTI PRASAD PANDEY & ORS. | pages 9, units 31 (30 numbered), opinions 1, unusable pages [] |
| judgment | MAHANADI COAL FIELDS LTD. & ANR. versus MATHIAS ORAM & ORS. | pages 53, units 107 (106 numbered), opinions 1, unusable pages [] |
| judgment | MAHANADI COAL FIELDS LTD. & ANR. versus MATHIAS ORAM & ORS. | pages 19, units 38 (37 numbered), opinions 1, unusable pages [] |
| judgment | MAHANAGAR TELEPHONE NIGAM LTD. versus M/S. APPLIED ELECTRONI | pages 17, units 34 (28 numbered), opinions 1, unusable pages [] |
| judgment | MAHANAGAR TELEPHONE NIGAM LTD. versus TATA COMMUNICATIONS LT | pages 14, units 37 (36 numbered), opinions 1, unusable pages [] |
| judgment | MAHANTH SATYANAND @ RAMJEE SINGH versus SHYAM LAL CHAUHAN AN | pages 8, units 22 (21 numbered), opinions 1, unusable pages [] |
| judgment | MAHENDRA K C versus THE STATE OF KARNATAKA & ANR. | pages 25, units 54 (53 numbered), opinions 1, unusable pages [] |
| judgment | MAHESH GOVINDJI TRIVEDI versus BAKUL MAGANLAL VYAS & ORS. | pages 28, units 60 (58 numbered), opinions 1, unusable pages [] |
| judgment | MALLURU MALLAPPA (D) THR. LRS. versus KURUVATHAPPA & ORS. | pages 9, units 26 (25 numbered), opinions 1, unusable pages [] |
| judgment | MAMIDI ANIL KUMAR REDDY versus STATE OF ANDHRA PRADESH & ANR | pages 6, units 21 (20 numbered), opinions 1, unusable pages [] |
| judgment | MAMTA & ANR versus THE STATE (NCT OF DELHI) & ANR | pages 5, units 18 (17 numbered), opinions 1, unusable pages [] |
| judgment | MANENDRA PRASAD TIWARI versus AMIT KUMAR TIWARI & ANR. | pages 22, units 42 (41 numbered), opinions 1, unusable pages [] |
| judgment | MANHARLAL SHIVLAL PANCHAL & OTHERS versus THE DEPUTY COLLECT | pages 8, units 21 (20 numbered), opinions 1, unusable pages [] |
| judgment | MANIK MAJUMDER AND OTHERS versus DIPAK KUMAR SAHA (DEAD) THR | pages 48, units 112 (111 numbered), opinions 1, unusable pages [] |
| judgment | MANIMEGALAI versus THE SPECIAL TAHSILDAR (LAND ACQUISITION O | pages 10, units 20 (19 numbered), opinions 1, unusable pages [] |
| judgment | MANISH SISODIA versus DIRECTORATE OF ENFORCEMENT | pages 25, units 74 (73 numbered), opinions 1, unusable pages [] |
| judgment | MANJEET SINGH versus NATIONAL INSURANCE COMPANY LTD. & ANR. | pages 5, units 11 (10 numbered), opinions 1, unusable pages [] |
| judgment | MANJEET SINGH versus STATE OF HARYANA & ORS. | pages 35, units 90 (89 numbered), opinions 1, unusable pages [] |
| judgment | MANJIT SINGH SODHI versus THE CUSTODIAN & ORS. | pages 13, units 38 (37 numbered), opinions 1, unusable pages [] |
| judgment | MANMOHAN NANDA versus UNITED INDIA ASSURANCE CO. LTD. & ANR | pages 43, units 106 (105 numbered), opinions 1, unusable pages [] |
| judgment | MANNO LAL JAISWAL versus THE STATE OF UTTAR PRADESH & ANR. | pages 8, units 21 (20 numbered), opinions 1, unusable pages [] |
| judgment | MANOHAR INFRASTRUCTURE AND CONSTRUCTIONS PRIVATE LIMITED ver | pages 14, units 34 (33 numbered), opinions 1, unusable pages [] |
| judgment | MANOJ KUMAR ETC. ETC. versus STATE OF HARYANA AND OTHERS ETC | pages 24, units 67 (66 numbered), opinions 1, unusable pages [] |
| judgment | MANOJ KUMAR TIWARI versus MANISH SISODIA & ORS | pages 33, units 116 (115 numbered), opinions 1, unusable pages [] |
| judgment | MANTI DEVI & ANR. versus KISHUN SAH @ KISHUN DEO SAO & ORS. | pages 4, units 14 (10 numbered), opinions 1, unusable pages [] |
| judgment | MANUBHAI SENDHABHAI BHARWAD & ANR. versus OIL AND NATURAL GA | pages 8, units 22 (21 numbered), opinions 1, unusable pages [] |
| judgment | MARINGMEI ACHAM versus M MARINGMET KHURIPOU | pages 8, units 25 (24 numbered), opinions 1, unusable pages [] |
| judgment | MARVEL OMEGA BUILDERS PVT. LTD. AND ANR.V. SHRIHARI GOKHALE  | pages 6, units 16 (15 numbered), opinions 1, unusable pages [] |
| judgment | MATHEW ALEXANDER versus MOHAMMED SHAFI AND ANR. | pages 8, units 17 (15 numbered), opinions 1, unusable pages [] |
| judgment | MAYA DEVI (D) THROUGH LRS & ORS. versus STATE OF HARYANA & A | pages 8, units 20 (19 numbered), opinions 1, unusable pages [] |
| judgment | MD. ASFAK ALAM versus THE STATE OF JHARKHAND & ANR. | pages 12, units 24 (23 numbered), opinions 1, unusable pages [] |
| judgment | MEENA DEVI versus THE STATE OF U.P. AND ANOTHER | pages 23, units 43 (42 numbered), opinions 1, unusable pages [] |
| judgment | MEENAKSHI SAXENA & ANR. versus ECGC LTD. (FORMERLY KNOWN AS  | pages 15, units 40 (39 numbered), opinions 1, unusable pages [] |
| judgment | MEHBOOB-UR-REHMAN (DEAD) THROUGH LRS. versus AHSANUL GHANI | pages 16, units 26 (25 numbered), opinions 1, unusable pages [] |
| judgment | MESSER GRIESHEIM GMBH (NOW CALLED AIR LIQUIDE DEUTSCHLAND GM | pages 15, units 36 (35 numbered), opinions 1, unusable pages [] |
| judgment | MIRZA IQBAL @ GOLU & ANR. versus STATE OF UTTAR PRADESH & AN | pages 7, units 15 (14 numbered), opinions 1, unusable pages [] |
| judgment | MITESH KUMAR J. SHA versus THE STATE OF KARNATAKA & ORS. | pages 20, units 47 (46 numbered), opinions 1, unusable pages [] |
| judgment | MITESH KUMAR RAMANBHAI PATEL & ORS. versus STATE OF GUJARAT  | pages 5, units 12 (11 numbered), opinions 1, unusable pages [] |
| judgment | MOHAMMAD LATIEF MAGREY versus THE UNION TERRITORY OF JAMMU A | pages 37, units 92 (91 numbered), opinions 1, unusable pages [] |
| judgment | MOHAMMAD WAJID AND ANR. versus STATE OF U.P. AND ORS. | pages 35, units 50 (49 numbered), opinions 1, unusable pages [] |
| judgment | MOHAMMAD YUSUF AND OTHERS ETC. ETC. versus STATE OF HARYANA  | pages 11, units 25 (24 numbered), opinions 1, unusable pages [] |
| judgment | MOHAMMADE YUSUF & ORS. versus RAJKUMAR & ORS. | pages 12, units 23 (22 numbered), opinions 1, unusable pages [] |
| judgment | MOHAMMED ZUBAIR versus STATE OF NCT OF DELHI & ORS | pages 22, units 51 (50 numbered), opinions 1, unusable pages [] |
| judgment | MOHAN @SRINIVAS @SEENA @TAILOR SEENA versus THE STATE OF KAR | pages 18, units 50 (49 numbered), opinions 1, unusable pages [] |
| judgment | MOHAR SINGH (DEAD) THROUGH LRS. & ORS. versus STATE OF UTTAR | pages 7, units 18 (17 numbered), opinions 1, unusable pages [] |
| judgment | MOHD ABAAD ALI & ANR. versus DIRECTORATE OF REVENUE PROSECUT | pages 12, units 23 (22 numbered), opinions 1, unusable pages [] |
| judgment | MOHD MUSLIM @ HUSSAIN versus STATE (NCT OF DELHI | pages 17, units 39 (38 numbered), opinions 1, unusable pages [] |
| judgment | MOHD ZAHID versus STATE THROUGH NCB | pages 17, units 33 (32 numbered), opinions 1, unusable pages [] |
| judgment | MOHD. FIROZ versus STATE OF MADHYA PRADESH | pages 34, units 54 (53 numbered), opinions 1, unusable pages [] |
| judgment | MOHD. RAZA & ANR. versus GEETA @ GEETA DEVI | pages 8, units 16 (15 numbered), opinions 1, unusable pages [] |
| judgment | MOHINDER KUMAR MEHRA versus ROOP RANI MEHRA & ORS. | pages 15, units 30 (29 numbered), opinions 1, unusable pages [] |
| judgment | MONSANTO TECHNOLOGY LLC THRU THE AUTHORISED REPRESENTATIVE M | pages 16, units 29 (28 numbered), opinions 1, unusable pages [] |
| judgment | MONU KUMAR & ORS. versus M/S. METROMAX INFRASTRUCTURE PVT. L | pages 3, units 8 (7 numbered), opinions 1, unusable pages [] |
| judgment | MR. VINAY PRAKASH SINGH versus SAMEER GEHLAUT & ORS. IN THE  | pages 11, units 22 (21 numbered), opinions 1, unusable pages [] |
| judgment | MRS. BHUMIKABEN N. MODI & ORS. versus LIFE INSURANCE CORPORA | pages 19, units 34 (33 numbered), opinions 1, unusable pages [] |
| judgment | MRS. HEMA KHATTAR & ANR. versus SHIV KHERA | pages 17, units 38 (37 numbered), opinions 1, unusable pages [] |
| judgment | MRS. UMADEVI NAMBIAR versus THAMARASSERI ROMAN CATHOLIC DIOC | pages 11, units 27 (26 numbered), opinions 1, unusable pages [] |
| judgment | MS. P XXX versus STATE OF UTTARAKHAND & ANR | pages 34, units 71 (69 numbered), opinions 1, unusable pages [] |
| judgment | MS. P versus THE STATE OF MADHYA PRADESH AND ANOTHER | pages 19, units 51 (50 numbered), opinions 1, unusable pages [] |
| judgment | MS. X versus THE STATE OF MAHARASHTRA AND ANOTHER | pages 23, units 35 (34 numbered), opinions 1, unusable pages [] |
| judgment | MUKHTAR ZAIDI versus THE STATE OF UTTAR PRADESH & ANR. | pages 9, units 16 (15 numbered), opinions 1, unusable pages [] |
| judgment | MUNIKRISHNA @ KRISHNA ETC. versus STATE BY ULSOOR PS | pages 22, units 31 (30 numbered), opinions 1, unusable pages [] |
| judgment | MUNNA LAL versus THE STATE OF UTTAR PRADESH | pages 20, units 53 (51 numbered), opinions 1, unusable pages [] |
| judgment | MUNUSAMY versus THE LAND ACQUISITION OFFICER | pages 6, units 17 (16 numbered), opinions 1, unusable pages [] |
| judgment | MURALI ALIAS DHANANJAYAN versus STATE OF KERALA | pages 5, units 24 (23 numbered), opinions 1, unusable pages [] |
| judgment | MURTI BHAWANI MATA MANDIR REP. THROUGH PUJARI GANESHI LAL (D | pages 6, units 23 (22 numbered), opinions 1, unusable pages [] |
| judgment | MURUGAN & ORS. versus KESAVA GOUNDER (DEAD) THR. LRS. AND OR | pages 26, units 57 (56 numbered), opinions 1, unusable pages [] |
| judgment | MUSKAN versus ISHAAN KHAN (SATANIYA) AND OTHERS | pages 18, units 51 (50 numbered), opinions 1, unusable pages [] |
| judgment | MUSSTT REHANA BEGUM versus STATE OF ASSAM & ANR. | pages 15, units 43 (42 numbered), opinions 1, unusable pages [] |
| judgment | N. A. L. LAYOUT RESIDENTS ASSOCIATION versus BANGALORE DEVEL | pages 36, units 99 (98 numbered), opinions 1, unusable pages [] |
| judgment | N. C. BANSAL versus UTTAR PRADESH FINANCIAL CORPORATION & AN | pages 6, units 27 (26 numbered), opinions 1, unusable pages [] |
| judgment | N. MANOGAR & ANR. versus THE INSPECTOR OF POLICE & ORS. | pages 8, units 24 (23 numbered), opinions 1, unusable pages [] |
| judgment | N. MOHAN versus R. MADHU | pages 13, units 22 (21 numbered), opinions 1, unusable pages [] |
| judgment | N. RAJENDRAN versus S. VALLI | pages 24, units 54 (53 numbered), opinions 1, unusable pages [] |
| judgment | N.C.V. AISHWARYA versus A.S. SARAVANA KARTHIK SHA | pages 4, units 14 (13 numbered), opinions 1, unusable pages [] |
| judgment | NADIMINTI SURYANARAYAN MURTHY (DEAD) THROUGH LRS. versus KOT | pages 13, units 41 (40 numbered), opinions 1, unusable pages [] |
| judgment | NAGAIAH AND ANOTHER versus SMT. CHOWDAMMA (DEAD) BY LRS. AND | pages 20, units 28 (27 numbered), opinions 1, unusable pages [] |
| judgment | NAGARPALIKA THAKURDWARA versus KHALIL AHMED & ORS. | pages 5, units 25 (24 numbered), opinions 1, unusable pages [] |
| judgment | NAHAR SINGH versus THE STATE OF UTTAR PRADESH & ANR. | pages 19, units 32 (31 numbered), opinions 1, unusable pages [] |
| judgment | NAMDEO SHANKAR GOVERDHANE (D) THR. LRS. & ORS. ETC. ETC. ver | pages 7, units 30 (29 numbered), opinions 1, unusable pages [] |
| judgment | NAND KISHORE PRASAD versus DR. MOHIB HAMIDI & OTHERS | pages 10, units 24 (23 numbered), opinions 1, unusable pages [] |
| judgment | NAND RAM (D) THROUGH LRS. & ORS. versus JAGDISH PRASAD (D) T | pages 32, units 67 (66 numbered), opinions 1, unusable pages [] |
| judgment | NANDLAL LOHARIYA versus JAGDISH CHAND PUROHIT AND ORS. | pages 4, units 10 (9 numbered), opinions 1, unusable pages [] |
| judgment | NARAYAN DEORAO JAVLE (DECEASED) THROUGH LRS. versus KRISHNA  | pages 20, units 48 (47 numbered), opinions 1, unusable pages [] |
| judgment | NARAYAN SITARAMJI BADWAIK (DEAD) THROUGH LRS versus BISARAM  | pages 7, units 25 (24 numbered), opinions 1, unusable pages [] |
| judgment | NARAYAN versus BABASAHEB & ORS. | pages 12, units 37 (36 numbered), opinions 1, unusable pages [] |
| judgment | NARAYANA GRAMANI & ORS. versus MARIAMMAL & ORS. | pages 11, units 32 (31 numbered), opinions 1, unusable pages [] |
| judgment | NARENDRA & ORS. versus AJABRAO S/O NARAYAN KATARE (D) THROUG | pages 9, units 39 (38 numbered), opinions 1, unusable pages [] |
| judgment | NARENDRA & ORS. versus STATE OF UTTAR PRADESH & ORS. | pages 13, units 29 (28 numbered), opinions 1, unusable pages [] |
| judgment | NARESH KUMAR & ANR. versus THE STATE OF KARNATAKA & ANR. | pages 7, units 10 (9 numbered), opinions 1, unusable pages [] |
| judgment | NARESH KUMAR & ORS. versus GOVT. OF NCT OF DELHI | pages 8, units 19 (18 numbered), opinions 1, unusable pages [] |
| judgment | NARESH KUMAR versus STATE OF DELHI | pages 18, units 36 (35 numbered), opinions 1, unusable pages [] |
| judgment | NASIB SINGH versus THE STATE OF PUNJAB & ANR. | pages 45, units 95 (94 numbered), opinions 1, unusable pages [] |
| judgment | NATHU SINGH versus STATE OF UTTAR PRADESH & ORS. | pages 12, units 38 (37 numbered), opinions 1, unusable pages [] |
| judgment | NATIONAL CAPITAL TERRITORY OF DELHI & ANR. versus SUBHASH CH | pages 5, units 16 (15 numbered), opinions 1, unusable pages [] |
| judgment | NATIONAL CAPITAL TERRITORY OF DELHI & ORS. versus SUBHASH CH | pages 5, units 17 (16 numbered), opinions 1, unusable pages [] |
| judgment | NATIONAL HIGHWAYS AUTHORITY OF INDIA versus SRI P. NAGARAJU  | pages 51, units 70 (69 numbered), opinions 1, unusable pages [] |
| judgment | NATIONAL INSURANCE CO. LTD. versus HARSOLIA MOTORS AND OTHER | pages 28, units 86 (85 numbered), opinions 1, unusable pages [] |
| judgment | NATIONAL INSURANCE COMPANY LTD. versus M/S. HARESHWAR ENTERP | pages 16, units 22 (21 numbered), opinions 1, unusable pages [] |
| judgment | NATIONAL INVESTIGATION AGENCY NEW DELHI versus OWAIS AMIN @  | pages 18, units 49 (48 numbered), opinions 1, unusable pages [] |
| judgment | NAUSHEY ALI & ORS. versus STATE OF U.P. & ANR. | pages 14, units 36 (35 numbered), opinions 1, unusable pages [] |
| judgment | NAVRATAN LAL SHARMA versus RADHA MOHAN SHARMA & ORS. | pages 10, units 26 (25 numbered), opinions 1, unusable pages [] |
| judgment | NAZIR MOHAMED versus J. KAMALA AND ORS. | pages 26, units 66 (65 numbered), opinions 1, unusable pages [] |
| judgment | NEENA ANEJA & ANR. versus JAI PRAKASH ASSOCIATES LTD. | pages 73, units 116 (114 numbered), opinions 1, unusable pages [] |
| judgment | NEK PAL & ORS. versus NAGAR PALIKA PARISHAD & ORS. | pages 4, units 13 (12 numbered), opinions 1, unusable pages [] |
| judgment | NELATUR SAMPOORNAMMA W/O SRINIVASULUREDDY versus SPECIAL DEP | pages 7, units 18 (17 numbered), opinions 1, unusable pages [] |
| judgment | NEPA LIMITED THROUGH ITS SENIOR MANAGER (LEGAL) versus MANOJ | pages 12, units 34 (33 numbered), opinions 1, unusable pages [] |
| judgment | NEW DELHI MUNICIPAL COUNCIL versus MINOSHA INDIA LIMITED | pages 22, units 49 (48 numbered), opinions 1, unusable pages [] |
| judgment | NEW INDIA ASSURANCE CO. LTD. & ORS versus M/S. MUDIT ROADWAY | pages 22, units 81 (80 numbered), opinions 1, unusable pages [] |
| judgment | NEW OKHLA INDUSTRIAL DEVELOPMENT AUTHORITY (NOIDA) versus YU | pages 36, units 79 (78 numbered), opinions 1, unusable pages [] |
| judgment | NEW OKHLA INDUSTRIAL DEVELOPMENT AUTHORITY versus DARSHAN LA | pages 30, units 34 (33 numbered), opinions 1, unusable pages [] |
| judgment | NEW OKHLA INDUSTRIAL DEVELOPMENT AUTHORITY versus HARKISHAN  | pages 11, units 16 (15 numbered), opinions 1, unusable pages [] |
| judgment | NEW OKHLA INDUSTRIAL DEVELOPMENT AUTHORITY versus OMVIR SING | pages 10, units 16 (15 numbered), opinions 1, unusable pages [] |
| judgment | NEW OKHLA INDUSTRIAL DEVELOPMENT AUTHORITY versus RAMESHWAR  | pages 7, units 13 (12 numbered), opinions 1, unusable pages [] |
| judgment | NINGAPPA THOTAPPA ANGADI (DEAD) THROUGH LRS. versus THE SPEC | pages 6, units 15 (14 numbered), opinions 1, unusable pages [] |
| judgment | NOORULLA KHAN versus KARNATAKA STATE POLLUTION CONTROL BOARD | pages 7, units 17 (16 numbered), opinions 1, unusable pages [] |
| judgment | NORTHERN DELHI MUNICIPAL CORPORATION versus RAM CHANDER SING | pages 8, units 24 (23 numbered), opinions 1, unusable pages [] |
| judgment | NUSLI NEVILLE WADIA versus IVORY PROPERTIES & ORS. | pages 70, units 145 (144 numbered), opinions 1, unusable pages [] |
| judgment | OM PRAKASH AHUJA versus RELIANCE GENERAL INSURANCE CO. LTD.  | pages 12, units 33 (32 numbered), opinions 1, unusable pages [] |
| judgment | OMI @ OMKAR RATHORE & ANR. versus THE STATE OF MADHYA PRADES | pages 15, units 30 (29 numbered), opinions 1, unusable pages [] |
| judgment | OMPRAKASH SAHNI versus JAI SHANKAR CHAUDHARY & ANR. ETC. | pages 24, units 79 (78 numbered), opinions 1, unusable pages [] |
| judgment | ORIENTAL INSURANCE CO. LTD. versus M/S TEJPARAS ASSOCIATES E | pages 13, units 17 (16 numbered), opinions 1, unusable pages [] |
| judgment | OWNERS AND PARTIES INTERESTED IN THE VESSEL M.V. POLARIS GAL | pages 37, units 102 (101 numbered), opinions 1, unusable pages [] |
| judgment | P MAHESH COOPERATIVE URBAN BANK SHAREHOLDERS WELFARE ASSOCIA | pages 16, units 32 (31 numbered), opinions 1, unusable pages [] |
| judgment | P. DAIVASIGAMANI versus S. SAMBANDAN | pages 22, units 34 (33 numbered), opinions 1, unusable pages [] |
| judgment | P. DHARAMARAJ versus SHANMUGAM & ORS. | pages 31, units 68 (67 numbered), opinions 1, unusable pages [] |
| judgment | P. RADHA BAI AND ORS. versus P. ASHOK KUMAR AND ANR. | pages 26, units 68 (67 numbered), opinions 1, unusable pages [] |
| judgment | P. RAMASUBBAMMA versus V. VIJAYALAKSHMI & OTHERS | pages 12, units 28 (27 numbered), opinions 1, unusable pages [] |
| judgment | P. RAVINDRANATH & ANR. versus SASIKALA & ORS. | pages 21, units 48 (47 numbered), opinions 1, unusable pages [] |
| judgment | P. SHYAMALA versus GUNDLUR MASTHAN | pages 12, units 32 (31 numbered), opinions 1, unusable pages [] |
| judgment | PANKAJBHAI RAMESHBHAI ZALAVADIYA versus JETHABHAI KALABHAI Z | pages 16, units 29 (28 numbered), opinions 1, unusable pages [] |
| judgment | PARDEEP SHARMA versus CHIEF ADMINISTRATOR HARYANA URBAN DEV. | pages 7, units 16 (15 numbered), opinions 1, unusable pages [] |
| judgment | PARSVNATH DEVELOPERS LTD. versus GAGANDEEP BRAR AND ANOTHER | pages 9, units 33 (32 numbered), opinions 1, unusable pages [] |
| judgment | PARTEEK BANSAL versus STATE OF RAJASTHAN & ORS | pages 7, units 15 (14 numbered), opinions 1, unusable pages [] |
| judgment | PARVINDER SINGH KHURANA versus DIRECTORATE OF ENFORCEMENT | pages 13, units 13 (12 numbered), opinions 1, unusable pages [] |
| judgment | PATHAPATI SUBBA REDDY (DIED) BY L.RS. & ORS. versus THE SPEC | pages 14, units 39 (38 numbered), opinions 1, unusable pages [] |
| judgment | PAWAN KUMAR versus BABULAL SINCE DECEASED THROUGH LRS. AND O | pages 12, units 38 (37 numbered), opinions 1, unusable pages [] |
| judgment | PEETHAMBARAN versus STATE OF KERALA & ANR. | pages 12, units 37 (35 numbered), opinions 1, unusable pages [] |
| judgment | PERIYAMMAL (DEAD) THROUGH LRS & ORS. versus V. RAJAMANI & AN | pages 58, units 72 (71 numbered), opinions 1, unusable pages [] |
| judgment | PHOENIX ARC PVT. LTD. versus KETULBHAI RAMUBHAI PATEL | pages 21, units 41 (40 numbered), opinions 1, unusable pages [] |
| judgment | PIMPRI CHINCHWAD NEW TOWNSHIP DEVELOPMENT AUTHORITY versus V | pages 19, units 65 (64 numbered), opinions 1, unusable pages [] |
| judgment | PIONEER URBAN LAND & INFRASTRUCTURE LTD. versus GOVINDAN RAG | pages 16, units 47 (46 numbered), opinions 1, unusable pages [] |
| judgment | PLACIDO FRANCISCO PINTO (D) BY LRS. & ANR versus JOSE FRANCI | pages 17, units 43 (42 numbered), opinions 1, unusable pages [] |
| judgment | PRABHAKARA ADIGA versus GOWRI & ORS. | pages 21, units 51 (50 numbered), opinions 1, unusable pages [] |
| judgment | PRADEEP MEHRA versus HARIJIVAN J. JETHWA (SINCE DECEASED THR | pages 12, units 29 (28 numbered), opinions 1, unusable pages [] |
| judgment | PRADEEP NIRANKARNATH SHARMA versus STATE OF GUJARAT & ORS. | pages 9, units 19 (18 numbered), opinions 1, unusable pages [] |
| judgment | PRADEEP S. WODEYAR versus THE STATE OF KARNATAKA | pages 74, units 134 (132 numbered), opinions 1, unusable pages [] |
| judgment | PRAKASH (DEAD) BY LR. versus G. ARADHYA AND ORS. | pages 18, units 64 (63 numbered), opinions 1, unusable pages [] |
| judgment | PRAKASH BANG versus GLAXO SMITHKLINE PHARMACEUTICALS LTD. &  | pages 11, units 20 (19 numbered), opinions 1, unusable pages [] |
| judgment | PRAKASH CORPORATES versus DEE VEE PROJECTS LIMITED | pages 42, units 97 (95 numbered), opinions 1, unusable pages [] |
| judgment | PRAMOD KUMAR & ANR. versus ZALAK SINGH & ORS. | pages 22, units 69 (68 numbered), opinions 1, unusable pages [] |
| judgment | PRASHANT SINGH RAJPUT versus THE STATE OF MADHYA PRADESH AND | pages 19, units 42 (41 numbered), opinions 1, unusable pages [] |
| judgment | PRATAP SINGH YADAV versus HARYANA URBAN DEVELOPMENT AUTHORIT | pages 8, units 12 (0 numbered), opinions 1, unusable pages [] |
| judgment | PRATIBHA MANCHANDA & ANR versus STATE OF HARYANA & ANR | pages 16, units 43 (42 numbered), opinions 1, unusable pages [] |
| judgment | PREM KISHORE & ORS. versus BRAHM PRAKASH & ORS | pages 34, units 63 (21 numbered), opinions 1, unusable pages [] |
| judgment | PREM SHANKAR PRASAD versus THE STATE OF BIHAR & ANR. | pages 11, units 28 (27 numbered), opinions 1, unusable pages [] |
| judgment | PRIYA INDORIA versus STATE OF KARNATAKA AND ORS. ETC. | pages 65, units 154 (152 numbered), opinions 1, unusable pages [] |
| judgment | PRIYANKA MISHRA & ORS versus THE STATE OF MADHYA PRADESH & A | pages 8, units 33 (32 numbered), opinions 1, unusable pages [] |
| judgment | PTC INDIA FINANCIAL SERVICES LIMITED versus VENKATESWARLU KA | pages 66, units 145 (141 numbered), opinions 1, unusable pages [] |
| judgment | PUNALUR PAPER MILLS LTD. versus WEST BENGAL MINERAL DEVELOPM | pages 25, units 62 (61 numbered), opinions 1, unusable pages [] |
| judgment | PUNJAB NATIONAL BANK versus MR. VIJAY SITARAM DANDNAIK & ANR | pages 11, units 28 (27 numbered), opinions 1, unusable pages [] |
| judgment | PURAN MAL versus STATE OF HARYANA & ANR. | pages 5, units 17 (16 numbered), opinions 1, unusable pages [] |
| judgment | PURNI DEVI & ANR. versus BABU RAM & ANR. | pages 11, units 25 (24 numbered), opinions 1, unusable pages [] |
| judgment | PURUSHOTHAMAN versus STATE OF TAMIL NADU | pages 5, units 15 (14 numbered), opinions 1, unusable pages [] |
| judgment | PYARELAL versus SHUBHENDRA PILANIA (MINOR) THROUGH NATURAL G | pages 14, units 38 (37 numbered), opinions 1, unusable pages [] |
| judgment | QAMAR GHANI USMANI versus THE STATE OF GUJARAT | pages 10, units 27 (26 numbered), opinions 1, unusable pages [] |
| judgment | R V PRASANNAKUMAAR & ORS. versus MANTRI CASTLES PVT. LTD & A | pages 8, units 24 (23 numbered), opinions 1, unusable pages [] |
| judgment | R. DHANASUNDARI @ R. RAJESWARI versus A.N. UMAKANTH & ORS. | pages 12, units 23 (22 numbered), opinions 1, unusable pages [] |
| judgment | R. HEMALATHA versus KASHTHURI | pages 12, units 31 (30 numbered), opinions 1, unusable pages [] |
| judgment | R. JANAKIAMMAL versus S.K. KUMARASAMY(DECEASED) THROUGH LEGA | pages 53, units 146 (145 numbered), opinions 1, unusable pages [] |
| judgment | R. KRSNA MURTII versus R. R. JAGADESAN | pages 3, units 15 (14 numbered), opinions 1, unusable pages [] |
| judgment | R. RAJASHEKAR AND ORS. versus TRINITY HOUSE BUILDING CO-OPER | pages 36, units 87 (86 numbered), opinions 1, unusable pages [] |
| judgment | R. S. ANJAYYA GUPTA versus THIPPAIAH SETTY & ORS. | pages 14, units 27 (26 numbered), opinions 1, unusable pages [] |
| judgment | RAGHUVEER SHARAN versus DISTRICT SAHAKARI KRISHI GRAMIN VIKA | pages 13, units 28 (27 numbered), opinions 1, unusable pages [] |
| judgment | RAGHWENDRA SHARAN SINGH versus RAM PRASANNA SINGH (DEAD) BY  | pages 15, units 37 (36 numbered), opinions 1, unusable pages [] |
| judgment | RAHIMAL BATHU & OTHERS versus ASHIYAL BEEVI | pages 17, units 43 (42 numbered), opinions 1, unusable pages [] |
| judgment | RAJ KUMAR @ SUMAN versus STATE (NCT OF DELHI) | pages 18, units 37 (36 numbered), opinions 1, unusable pages [] |
| judgment | RAJ KUMAR BHATIA versus SUBHASH CHANDER BHATIA | pages 9, units 21 (20 numbered), opinions 1, unusable pages [] |
| judgment | RAJ PAL SINGH versus COMMISSIONER OF INCOME-TAX, HARYANA, RO | pages 60, units 120 (119 numbered), opinions 1, unusable pages [] |
| judgment | RAJA RAM versus JAI PRAKASH SINGH AND OTHERS | pages 11, units 25 (24 numbered), opinions 1, unusable pages [] |
| judgment | RAJA VENKATESWARLU & ANR. versus MADA VENKATA SUBBAIAB & ANR | pages 3, units 9 (8 numbered), opinions 1, unusable pages [] |
| judgment | RAJALAKSHMI versus THE SPECIAL TAHSILDAR (LA) KOYILANDY & AN | pages 5, units 20 (19 numbered), opinions 1, unusable pages [] |
| judgment | RAJASTHAN HOUSING BOARD & ANR versus RATAN DEVI | pages 6, units 16 (15 numbered), opinions 1, unusable pages [] |
| judgment | RAJBIR versus SURAJ BHAN & ANR | pages 14, units 34 (33 numbered), opinions 1, unusable pages [] |
| judgment | RAJENDRA BAJORIA AND OTHERS versus HEMANT KUMAR JALAN AND OT | pages 16, units 33 (32 numbered), opinions 1, unusable pages [] |
| judgment | RAJENDRA BHAGWANJI UMRANIYA versus STATE OF GUJARAT | pages 10, units 31 (30 numbered), opinions 1, unusable pages [] |
| judgment | RAJESH KUMAR versus ANAND KUMAR & ORS. | pages 17, units 38 (37 numbered), opinions 1, unusable pages [] |
| judgment | RAJIV SHUKLA versus GOLD RUSH SALES AND SERVICES LTD. & ANR | pages 7, units 20 (19 numbered), opinions 1, unusable pages [] |
| judgment | RAJNISH SINGH @ SONI versus STATE OF U.P. AND ANOTHER | pages 14, units 42 (41 numbered), opinions 1, unusable pages [] |
| judgment | RAJO @ RAJWA @ RAJENDRA MANDAL versus THE STATE OF BIHAR & O | pages 23, units 61 (60 numbered), opinions 1, unusable pages [] |
| judgment | RAM CHAND (DECEASED) THROUGH L.RS. & ORS. versus UDAI SINGH@ | pages 5, units 22 (21 numbered), opinions 1, unusable pages [] |
| judgment | RAM CHANDER versus THE STATE OF CHHATTISGARH & ANR. | pages 25, units 53 (52 numbered), opinions 1, unusable pages [] |
| judgment | RAM PRAKASH CHADHA versus THE STATE OF UTTAR PRADESH | pages 20, units 40 (39 numbered), opinions 1, unusable pages [] |
| judgment | RAMAN (DEAD) BY LRS. versus R. NATARAJAN | pages 9, units 28 (27 numbered), opinions 1, unusable pages [] |
| judgment | RAMATHAL versus MARUTHATHAL & ORS. | pages 13, units 30 (29 numbered), opinions 1, unusable pages [] |
| judgment | RAMAYAN SINGH versus STATE OF UTTAR PRADESH & ANR. | pages 8, units 25 (24 numbered), opinions 1, unusable pages [] |
| judgment | RAMDAS WAYDHAN GADLINGE (SINCE DECEASED) THR LRS. VATSALABAI | pages 8, units 25 (24 numbered), opinions 1, unusable pages [] |
| judgment | RAMESH BHAVAN RATHOD versus VISHANBHAI HIRABHAI MAKWANA MAKW | pages 35, units 78 (77 numbered), opinions 1, unusable pages [] |
| judgment | RAMESH CHAND AND ORS. versus M/S. TANMAY DEVELOPERS PVT. LTD | pages 9, units 14 (13 numbered), opinions 1, unusable pages [] |
| judgment | RAMESH CHANDRA SHARMA & ORS. versus STATE OF UTTAR PRADESH & | pages 49, units 62 (61 numbered), opinions 1, unusable pages [] |
| judgment | RAMESH CHANDRA SRIVASTAVA versus THE STATE OF U. P. & ANR. | pages 6, units 16 (16 numbered), opinions 1, unusable pages [] |
| judgment | RAMESH KUMAR V. BHATINDA INTEGRATED COOPERATIVE COTTON SPINN | pages 13, units 30 (26 numbered), opinions 1, unusable pages [] |
| judgment | RAMESH KUMAR versus STATE OF NCT OF DELHI | pages 17, units 45 (44 numbered), opinions 1, unusable pages [] |
| judgment | RAMESHWAR & OTHERS versus STATE OF HARYANA & OTHERS | pages 82, units 119 (118 numbered), opinions 1, unusable pages [17, 27, 37, 38, 43, 44] |
| judgment | RAMESHWAR AND ORS versus STATE OF HARYANA & ORS. | pages 65, units 169 (166 numbered), opinions 1, unusable pages [] |
| judgment | RAMESHWAR DASS versus THE STATE OF PUNJAB | pages 9, units 27 (26 numbered), opinions 1, unusable pages [] |
| judgment | RAMESHWAR PRASAD SHRIVASTAVA AND ORS. versus DWARKADHIS PROJ | pages 13, units 35 (34 numbered), opinions 1, unusable pages [] |
| judgment | RAMGOPAL & ANR. versus THE STATE OF MADHYA PRADESH | pages 19, units 38 (37 numbered), opinions 1, unusable pages [] |
| judgment | RAMJI SINGH PATEL versus GYAN CHANDRA JAISWAL | pages 7, units 18 (17 numbered), opinions 1, unusable pages [] |
| judgment | RAMRAO SHANKAR TAPASE versus MAHARASHTRA INDUSTRIAL DEVELOPM | pages 19, units 43 (42 numbered), opinions 1, unusable pages [] |
| judgment | RAMSINGBHAI (RAMSANGBHAI) JERAMBHAI versus THE STATE OF GUJA | pages 3, units 8 (7 numbered), opinions 1, unusable pages [] |
| judgment | RAMVEER UPADHYAY & ANR. versus STATE OF U.P. & ANR. | pages 20, units 51 (50 numbered), opinions 1, unusable pages [] |
| judgment | RANJIT KUMAR KARMAKAR @ DULAL KARMAKAR versus HARI SHANKAR D | pages 4, units 17 (16 numbered), opinions 1, unusable pages [] |
| judgment | RATHISH BABU UNNIKRISHNAN versus THE STATE (GOVT. OF NCT OF  | pages 13, units 21 (20 numbered), opinions 1, unusable pages [] |
| judgment | RATNAGIRI NAGAR PARISHAD versus GANGARAM NARAYAN AMBEKAR & O | pages 29, units 43 (42 numbered), opinions 1, unusable pages [] |
| judgment | RATNAMBAR KAUSHIK versus UNION OF INDIA | pages 4, units 10 (9 numbered), opinions 1, unusable pages [] |
| judgment | RAVI SETIA versus MADAN LAL AND OTHERS | pages 11, units 22 (21 numbered), opinions 1, unusable pages [] |
| judgment | RAVI SHARMA versus STATE (GOVERNMENT OF NCT OF DELHI) AND AN | pages 18, units 40 (39 numbered), opinions 1, unusable pages [] |
| judgment | RAVINDER KAUR GREWAL & ORS versus MANJIT KAUR & ORS. | pages 61, units 138 (137 numbered), opinions 1, unusable pages [] |
| judgment | RAVINDER KAUR GREWAL & ORS. versus MANJIT KAUR & ORS. | pages 25, units 36 (35 numbered), opinions 1, unusable pages [] |
| judgment | RAVINDER KUMAR GOEL versus THE STATE OF HARYANA & ORS. | pages 18, units 26 (25 numbered), opinions 1, unusable pages [] |
| judgment | RAVINDER SINGH versus THE STATE GOVT. OF NCT OF DELHI | pages 13, units 22 (21 numbered), opinions 1, unusable pages [] |
| judgment | RB DEALERS PRIVATE LIMITED versus THE METRO RAILWAY, KOLKATA | pages 11, units 18 (17 numbered), opinions 1, unusable pages [] |
| judgment | REDDY VEERANA versus STATE OF UTTAR PRADESH AND OTHERS | pages 35, units 57 (56 numbered), opinions 1, unusable pages [] |
| judgment | REHAN AHMED (D) THR. LRS. versus AKHTAR UN NISA (D) THR. LRS | pages 13, units 22 (21 numbered), opinions 1, unusable pages [] |
| judgment | RELIANCE LIFE INSURANCE CO LTD & ANR. versus REKHABEN NARESH | pages 29, units 75 (74 numbered), opinions 1, unusable pages [] |
| judgment | RICARDO CONSTRUCTIONS PVT. LTD. versus RAVI KUCKIAN & OTHERS | pages 6, units 16 (15 numbered), opinions 1, unusable pages [] |
| judgment | RICHARD LEE versus GIRISH SONI AND ANR. | pages 5, units 15 (13 numbered), opinions 1, unusable pages [] |
| judgment | RINA KUMARI @ RINA DEVI @ REENA versus DINESH KUMAR MAHTO @  | pages 22, units 49 (48 numbered), opinions 1, unusable pages [] |
| judgment | RIPUDAMAN SINGH versus TIKKA MAHESHWAR CHAND | pages 11, units 27 (26 numbered), opinions 1, unusable pages [] |
| judgment | RITU CHHABARIA versus UNION OF INDIA & ORS. | pages 18, units 33 (32 numbered), opinions 1, unusable pages [] |
| judgment | ROHIT BISHNOI versus THE STATE OF RAJASTHAN & ANR | pages 15, units 43 (0 numbered), opinions 1, unusable pages [] |
| judgment | ROHIT CHAUDHARY & ANR. versus M/S VIPUL LTD. | pages 18, units 22 (0 numbered), opinions 1, unusable pages [] |
| judgment | RUCHI RAWAT versus PRINCIPAL JUDGE, FAMILY COURT ETAH & ANR. | pages 3, units 11 (9 numbered), opinions 1, unusable pages [] |
| judgment | S. MURALI SUNDARAM versus JOTHIBAI KANNAN & ORS | pages 9, units 31 (30 numbered), opinions 1, unusable pages [] |
| judgment | S. NARAHARI AND ORS versus S.R. KUMAR AND ORS. | pages 11, units 46 (45 numbered), opinions 1, unusable pages [] |
| judgment | S. SAROJINI AMMA versus VELAYUDHAN PILLAI SREEKUMAR | pages 7, units 22 (21 numbered), opinions 1, unusable pages [] |
| judgment | S. SHANKARAIAH THR. GPA HOLDER & ORS versus THE LAND ACQUISI | pages 7, units 19 (18 numbered), opinions 1, unusable pages [] |
| judgment | SABARMATI GAS LIMITED versus SHAH ALLOYS LIMITED | pages 32, units 62 (61 numbered), opinions 1, unusable pages [] |
| judgment | SACHIN GARG versus STATE OF U.P & ANR. | pages 17, units 28 (27 numbered), opinions 1, unusable pages [] |
| judgment | SADHNA CHAUDHARY versus THE STATE OF RAJASTHAN & ANR. | pages 11, units 26 (25 numbered), opinions 1, unusable pages [] |
| judgment | SAKHARAM SINCE DECEASED THROUGH LRS & ANR. versus KISHANRAO | pages 4, units 12 (11 numbered), opinions 1, unusable pages [] |
| judgment | SAKINA SULTANALI SUNESARA (MOMIN) versus SHIA IMAMI ISMAILI  | pages 15, units 49 (48 numbered), opinions 1, unusable pages [] |
| judgment | SALIB @ SHALU @ SALIM versus STATE OF U.P. AND ORS. | pages 18, units 29 (28 numbered), opinions 1, unusable pages [] |
| judgment | SALIM D. AGBOATWALA AND ORS. versus SHAMALJI ODDHAVJI THAKKA | pages 14, units 32 (31 numbered), opinions 1, unusable pages [] |
| judgment | SALIMBHAI HAMIDBHAI MEMON versus NITESHKUMAR MAGANBHAI PATEL | pages 16, units 51 (50 numbered), opinions 1, unusable pages [] |
| judgment | SAMAR KUMAR ROY (D) THROUGH LR (MOTHER) versus JHARNA BERA | pages 13, units 24 (23 numbered), opinions 1, unusable pages [] |
| judgment | SAMRUDDHI CO-OPERATIVE HOUSING SOCIETY LTD. versus MUMBAI MA | pages 18, units 35 (32 numbered), opinions 1, unusable pages [] |
| judgment | SANDEEP ALIAS KALA versus SUPREME COURT OF INDIA | pages 26, units 72 (71 numbered), opinions 1, unusable pages [] |
| judgment | SANDEEP KUMAR versus STATE OF HARYANA & ANR | pages 8, units 17 (16 numbered), opinions 1, unusable pages [] |
| judgment | SANGHI INDUSTRIES LIMITED versus RAVIN CABLES LTD., AND ANR | pages 4, units 9 (8 numbered), opinions 1, unusable pages [] |
| judgment | SANJAY KUMAR AGARWAL versus STATE TAX OFFICER (1) & ANR. | pages 16, units 34 (33 numbered), opinions 1, unusable pages [] |
| judgment | SANJAY KUMAR RAI versus STATE OF UTTAR PRADESH & ANR. | pages 10, units 25 (24 numbered), opinions 1, unusable pages [] |
| judgment | SARANGA ANILKUMAR AGGARWAL versus BHAVESH DHIRAJLAL SHETH &  | pages 16, units 43 (42 numbered), opinions 1, unusable pages [] |
| judgment | SARANPAL KAUR ANAND versus PRADUMAN SINGH CHANDHOK AND OTHER | pages 49, units 91 (86 numbered), opinions 1, unusable pages [] |
| judgment | SARANYA versus BHARATHI AND ANOTHER | pages 12, units 34 (33 numbered), opinions 1, unusable pages [] |
| judgment | SARDAR RAVI INDER SINGH & ANR. versus STATE OF JHARKHAND & A | pages 9, units 21 (20 numbered), opinions 1, unusable pages [] |
| judgment | SATBIR SINGH versus STATE OF HARYANA & ORS. | pages 8, units 24 (23 numbered), opinions 1, unusable pages [] |
| judgment | SATENDER KUMAR ANTIL versus CENTRAL BUREAU OF INVESTIGATION  | pages 97, units 160 (158 numbered), opinions 1, unusable pages [] |
| judgment | SATENDER KUMAR ANTIL versus CENTRAL BUREAU OF INVESTIGATION  | pages 49, units 147 (145 numbered), opinions 1, unusable pages [] |
| judgment | SATHYANATH & ANR. versus SAROJAMANI | pages 22, units 61 (60 numbered), opinions 1, unusable pages [] |
| judgment | SATISH CHAND SURANA versus RAJ KUMAR MESHRAM | pages 3, units 12 (0 numbered), opinions 1, unusable pages [] |
| judgment | SATISH KUMAR JATAV versus THE STATE OF U.P. & ORS. | pages 6, units 18 (17 numbered), opinions 1, unusable pages [] |
| judgment | SATISH KUMAR versus KARAN SINGH AND ANOTHER | pages 7, units 19 (17 numbered), opinions 1, unusable pages [] |
| judgment | SATYA PAL ANAND versus STATE OF M.P. & ORS. | pages 36, units 57 (56 numbered), opinions 1, unusable pages [] |
| judgment | SATYA PRAKASH DWIVEDI versus MUNNA ALIAS CHANDRABHAN YADAV A | pages 9, units 22 (21 numbered), opinions 1, unusable pages [] |
| judgment | SATYENDER AND ORS. versus SAROJ AND ORS | pages 15, units 23 (22 numbered), opinions 1, unusable pages [] |
| judgment | SAU RAJANI versus SAU SMITA & ANR | pages 13, units 38 (37 numbered), opinions 1, unusable pages [] |
| judgment | SAURAV DAS versus UNION OF INDIA & ORS. | pages 6, units 20 (19 numbered), opinions 1, unusable pages [] |
| judgment | SAYYED AYAZ ALI versus PRAKASH G GOYAL & ORS. | pages 12, units 30 (29 numbered), opinions 1, unusable pages [] |
| judgment | SECUNDERABAD CANTONMENT BOARD versus M/S B. RAMACHANDRAIAH & | pages 19, units 53 (52 numbered), opinions 1, unusable pages [] |
| judgment | SEETHAKATHI TRUST MADRAS versus KRISHNAVENI | pages 12, units 36 (35 numbered), opinions 1, unusable pages [] |
| judgment | SEJAL GLASS LTD. versus NAVILAN MERCHANTS PVT. LTD. | pages 8, units 25 (24 numbered), opinions 1, unusable pages [] |
| judgment | SERIOUS FRAUD INVESTIGATION OFFICE versus RAHUL MODI & ORS. | pages 12, units 19 (18 numbered), opinions 1, unusable pages [] |
| judgment | SGS INDIA LTD. versus DOLPHIN INTERNATIONAL LTD. | pages 12, units 33 (32 numbered), opinions 1, unusable pages [] |
| judgment | SH. RAM CHANDER (DEAD) THR LRS versus UNION OF INDIA | pages 8, units 11 (10 numbered), opinions 1, unusable pages [] |
| judgment | SHABBIR MOHAMMAD SAYED versus MRS. NOOR JEHAN MUSHTER SHAIKH | pages 15, units 45 (44 numbered), opinions 1, unusable pages [] |
| judgment | SHAH NEWAZ KHAN & ORS. versus STATE OF NAGALAND & ORS | pages 29, units 83 (82 numbered), opinions 1, unusable pages [] |
| judgment | SHAILNDRA KUMAR JAIN AND OTHERS versus MAYA PRAKASH JAIN AND | pages 7, units 18 (17 numbered), opinions 1, unusable pages [] |
| judgment | SHAKTI BHOG FOOD INDUSTRIES LTD. versus THE CENTRAL BANK OF  | pages 26, units 40 (39 numbered), opinions 1, unusable pages [] |
| judgment | SHAKUNTLA DEVI versus STATE OF H.P. AND OTHERS | pages 6, units 15 (14 numbered), opinions 1, unusable pages [] |
| judgment | SHAMSHER SINGH & ANR. versus LT. COL. NAHAR SINGH (D) THR. L | pages 20, units 42 (41 numbered), opinions 1, unusable pages [] |
| judgment | SHANKAR versus THE STATE OF UTTAR PRADESH & ORS. | pages 10, units 37 (36 numbered), opinions 1, unusable pages [] |
| judgment | SHANKARRAO BHAGWANTRAO PATIL ETC. versus THE STATE OF MAHARA | pages 12, units 25 (24 numbered), opinions 1, unusable pages [] |
| judgment | SHANTABEN BHURABHAI BHURIYA versus ANAND ATHABHAI CHAUDHARI  | pages 24, units 41 (40 numbered), opinions 1, unusable pages [] |
| judgment | SHARIF AHMED AND ANOTHER versus STATE OF UTTAR PRADESH AND A | pages 43, units 79 (78 numbered), opinions 1, unusable pages [] |
| judgment | SHIV KUMAR & ANR. versus UNION OF INDIA & ORS. | pages 26, units 49 (48 numbered), opinions 1, unusable pages [] |
| judgment | SHIV SINGH & ORS. versus STATE OF HIMACHAL PRADESH & ORS. | pages 4, units 16 (15 numbered), opinions 1, unusable pages [] |
| judgment | SHIVAJI YALLAPPA PATIL versus SRI RANAJEET APPASAHEB PATIL & | pages 10, units 25 (24 numbered), opinions 1, unusable pages [] |
| judgment | SHIVANI TYAGI versus STATE OF U.P. & ANR. | pages 20, units 53 (52 numbered), opinions 2, unusable pages [] |
| judgment | SHIVNARAYAN (D) BY LRS. versus MANIKLAL (D) THR. LRS. & ORS. | pages 23, units 47 (46 numbered), opinions 1, unusable pages [] |
| judgment | SHODA DEVI versus DDU/RIPON HOSPITAL SHIMLA AND ORS. | pages 12, units 27 (26 numbered), opinions 1, unusable pages [] |
| judgment | SHRACHI BURDWAN DEVELOPERS PRIVATE LIMITED versus THE STATE  | pages 17, units 42 (41 numbered), opinions 1, unusable pages [] |
| judgment | SHRI BADRU (SINCE DECEASED) THROUGH L.R.HARI RAM ETC. versus | pages 8, units 28 (27 numbered), opinions 1, unusable pages [] |
| judgment | SHRI NASHIK PANCHAVATI PANJARPOL TRUST AND ORS. versus THE C | pages 8, units 15 (14 numbered), opinions 1, unusable pages [] |
| judgment | SHRI RAJENDRA LALITKUMAR AGRAWAL versus SMT. RATNA ASHOK MUR | pages 5, units 19 (18 numbered), opinions 1, unusable pages [] |
| judgment | SHRI RAM SAHU (DEAD) THROUGH LRS. versus VINOD KUMAR RAWAT & | pages 31, units 92 (91 numbered), opinions 1, unusable pages [] |
| judgment | SHRI SUKHBIR SINGH BADAL versus BALWANT SINGH KHERA AND ORS. | pages 19, units 62 (61 numbered), opinions 1, unusable pages [] |
| judgment | SHRIKANT G. MANTRI versus PUNJAB NATIONAL BANK | pages 25, units 61 (60 numbered), opinions 1, unusable pages [] |
| judgment | SHRIPATI LAKHU MANE versus THE MEMBER SECRETARY, MAHARASHTRA | pages 11, units 40 (39 numbered), opinions 1, unusable pages [] |
| judgment | SHRIRAM CHITS (INDIA) PRIVATE LIMITED EARLIER KNOWN AS SHRIR | pages 13, units 29 (28 numbered), opinions 1, unusable pages [] |
| judgment | SHYAM SEL AND POWER LIMITED AND versus SHYAM STEEL INDUSTRIE | pages 28, units 57 (56 numbered), opinions 1, unusable pages [] |
| judgment | SHYAMSUNDAR RADHESHYAM AGRAWAL & ANR. versus PUSHPABAI NILKA | pages 13, units 21 (20 numbered), opinions 1, unusable pages [] |
| judgment | SIDDAGANGAIAH (D) THR. LRS. versus N.K. GIRIRAJA SHETTY (D)  | pages 22, units 56 (55 numbered), opinions 1, unusable pages [] |
| judgment | SIDDALINGAYYA versus GURI. LINGAPPA & ORS. | pages 6, units 28 (27 numbered), opinions 1, unusable pages [] |
| judgment | SIDDHARTH MUKESH BHANDARI versus THE STATE OF GUJARAT AND AN | pages 7, units 11 (10 numbered), opinions 1, unusable pages [] |
| judgment | SIRAJUDHEEN versus ZEENATH & ORS | pages 19, units 44 (43 numbered), opinions 1, unusable pages [] |
| judgment | SIRI CHAND (DECEASED) THR. LRS. versus SURINDER SINGH | pages 12, units 30 (29 numbered), opinions 1, unusable pages [] |
| judgment | SITA RAM BHAMA versus RAMVATAR BHAMA | pages 10, units 31 (30 numbered), opinions 1, unusable pages [] |
| judgment | SK. BHIKAN S/O SK NOOR MOHD. versus MEHAMOODABEE W/O SK. AFZ | pages 6, units 27 (26 numbered), opinions 1, unusable pages [] |
| judgment | SMT. BAYANABAI KAWARE versus RAJENDRA S/O BABURAO DHOTE | pages 7, units 26 (25 numbered), opinions 1, unusable pages [] |
| judgment | SMT. KATTA SUJATHA REDDY & ANR. versus SIDDAMSETTY INFRA PRO | pages 35, units 106 (105 numbered), opinions 1, unusable pages [] |
| judgment | SMT. M. HEMALATHA DEVI & ORS. versus B. UDAYASRI | pages 31, units 68 (67 numbered), opinions 1, unusable pages [] |
| judgment | SMT. REKHA JAIN AND ANR. versus THE STATE OF UTTAR PRADESH A | pages 5, units 15 (14 numbered), opinions 1, unusable pages [] |
| judgment | SMT. VED KUMARI (DEAD THROUGH HER LEGAL REPRESENTATIVE) DR.  | pages 11, units 32 (31 numbered), opinions 1, unusable pages [] |
| judgment | SNEH LATA GOEL versus PUSHPLATA & ORS. | pages 14, units 38 (37 numbered), opinions 1, unusable pages [] |
| judgment | SOBHA HIBISCUS CONDOMINIUM versus MANAGING DIRECTOR, M/S. SO | pages 9, units 19 (18 numbered), opinions 1, unusable pages [] |
| judgment | SOBHA SINGH AND SONS PVT. LTD. versus SHASHI MOHAN KAPUR (DE | pages 20, units 67 (66 numbered), opinions 1, unusable pages [] |
| judgment | SOLOMON SELVARAJ & ORS. versus INDIRANI BHAGAWAN SINGH & ORS | pages 8, units 20 (19 numbered), opinions 1, unusable pages [] |
| judgment | SOMAKKA (DEAD) BY LRS versus K.P. BASAVARAJ (DEAD) BY LRS | pages 13, units 45 (44 numbered), opinions 1, unusable pages [] |
| judgment | SOMESH CHAURASIA versus STATE OF M.P. & ANR. | pages 31, units 75 (74 numbered), opinions 1, unusable pages [] |
| judgment | SOMJEET MALLICK versus STATE OF JHARKHAND & OTHERS | pages 8, units 16 (15 numbered), opinions 1, unusable pages [] |
| judgment | SOPAN (DEAD) THROUGH HIS L.R. versus SYED NABI | pages 10, units 17 (16 numbered), opinions 1, unusable pages [] |
| judgment | SOPANRAO & ANR. versus SYED MEHMOOD & ORS. | pages 10, units 18 (17 numbered), opinions 1, unusable pages [] |
| judgment | SPECIAL LAND ACQUISITION OFFICER AND ORS. versus N. SAVITHA | pages 6, units 13 (12 numbered), opinions 1, unusable pages [] |
| judgment | SRI BISWANATH BANIK & ANR. versus SMT. SULANGA BOSE & ORS. | pages 9, units 25 (24 numbered), opinions 1, unusable pages [] |
| judgment | SRI MAHESH versus SANGRAM & ORS | pages 19, units 37 (36 numbered), opinions 1, unusable pages [] |
| judgment | SRI NARENDRA KUMAR A. BALDOTA versus THE STATE OF KARNATAKA | pages 21, units 49 (48 numbered), opinions 1, unusable pages [] |
| judgment | SRI PRABODH CH. DAS AND ANR. versus MAHAMAYA DAS AND ORS. | pages 5, units 16 (15 numbered), opinions 1, unusable pages [] |
| judgment | SRI SHIVAJI BALARAM HAIBAITL versus SRI AVINASH MARUTHI PAWA | pages 9, units 35 (34 numbered), opinions 1, unusable pages [] |
| judgment | SRI SRINIVASAIAH versus H. R. CHANNABASAPPA (SINCE DEAD) BY  | pages 17, units 44 (43 numbered), opinions 1, unusable pages [] |
| judgment | SRI V.N. KRISHNA MURTHY & ANR. ETC. ETC. versus SRI RAVIKUMA | pages 10, units 28 (27 numbered), opinions 1, unusable pages [] |
| judgment | SRIDEVI DATLA versus UNION OF INDIA AND ORS. | pages 17, units 42 (41 numbered), opinions 1, unusable pages [] |
| judgment | SRIDHAR & ANR. versus N. REVANNA & ORS. | pages 13, units 41 (40 numbered), opinions 1, unusable pages [] |
| judgment | SRIHARI HANUMANDAS TOTALA versus HEMANT VITHAL KAMAT & ORS. | pages 21, units 49 (48 numbered), opinions 1, unusable pages [] |
| judgment | SRIKANT UPADHYAY & ORS versus STATE OF BIHAR & ANR. | pages 17, units 29 (28 numbered), opinions 1, unusable pages [] |
| judgment | STAR INDIA (P) LTD. versus SOCIETY OF CATALYSTS & ANR. | pages 15, units 36 (35 numbered), opinions 1, unusable pages [] |
| judgment | STATE BANK OF INDIA versus KRISHIDHAN SEEDS PRIVATE LIMITED | pages 9, units 25 (24 numbered), opinions 1, unusable pages [] |
| judgment | STATE BY THE INSPECTOR OF POLICE versus B. RAMU | pages 7, units 21 (20 numbered), opinions 1, unusable pages [] |
| judgment | STATE OF ANDHRA PRADESH & ORS. versus B. RANGA REDDY (D) BY  | pages 32, units 69 (68 numbered), opinions 1, unusable pages [] |
| judgment | STATE OF ASSAM versus UNION OF INDIA AND ORS. | pages 4, units 11 (10 numbered), opinions 1, unusable pages [] |
| judgment | STATE OF GUJARAT AND ORS. versus JAYANTIBHAI ISHWARBHAI PATE | pages 17, units 45 (44 numbered), opinions 1, unusable pages [] |
| judgment | STATE OF GUJARAT versus DILIPSINH KISHORSINH RAO | pages 14, units 25 (24 numbered), opinions 1, unusable pages [] |
| judgment | STATE OF HARYANA & ANR. versus SUBHASH CHANDER & ORS. | pages 6, units 17 (16 numbered), opinions 1, unusable pages [] |
| judgment | STATE OF HARYANA versus DHARAMRAJ | pages 10, units 24 (23 numbered), opinions 1, unusable pages [] |
| judgment | STATE OF HARYANA versus DR. RITU SINGH AND ANOTHER | pages 5, units 14 (13 numbered), opinions 1, unusable pages [] |
| judgment | STATE OF HARYANA versus EROS CITY DEVELOPERS PVT. LTD. AND O | pages 8, units 25 (24 numbered), opinions 1, unusable pages [] |
| judgment | STATE OF HIMACHAL PRADESH & ORS versus RAJIV AND ANR. | pages 6, units 23 (22 numbered), opinions 1, unusable pages [] |
| judgment | STATE OF HIMACHAL PRADESH & ORS. versus KANSHI RAM & ORS. | pages 8, units 16 (15 numbered), opinions 1, unusable pages [] |
| judgment | STATE OF KARNATAKA versus T. NASEER @ NASIR @ THANDIANTAVIDA | pages 10, units 26 (25 numbered), opinions 1, unusable pages [] |
| judgment | STATE OF MADHYA PRADESH & ANR. versus RADHESHYAM & ORS | pages 17, units 50 (49 numbered), opinions 1, unusable pages [] |
| judgment | STATE OF MAHARASHTRA & ORS. versus RELIANCE INDUSTRIES LTD.  | pages 60, units 122 (121 numbered), opinions 1, unusable pages [] |
| judgment | STATE OF NCT OF DELHI versus RAJ KUMAR @ LOVEPREET @LOVELY | pages 8, units 21 (20 numbered), opinions 1, unusable pages [] |
| judgment | STATE OF ODISHA versus PRATIMA MOHANTY ETC. | pages 16, units 32 (31 numbered), opinions 1, unusable pages [] |
| judgment | STATE OF RAJASTHAN & ORS. versus GRAM VIKAS SAMITI, SHIVDASP | pages 4, units 21 (20 numbered), opinions 1, unusable pages [] |
| judgment | STATE OF RAJASTHAN & ORS. versus SHIV DAYAL & ANR. | pages 8, units 40 (39 numbered), opinions 1, unusable pages [] |
| judgment | STATE OF RAJASTHAN versus ASHARAM @ ASHUMAL | pages 17, units 30 (28 numbered), opinions 1, unusable pages [] |
| judgment | STATE OF U P AND ORS versus ALL U P CONSUMER PROTECTION BAR  | pages 22, units 58 (51 numbered), opinions 1, unusable pages [] |
| judgment | STATE OF U P THROUGH PRINCIPAL SECRETARY & ORS. versus ALL U | pages 7, units 14 (12 numbered), opinions 1, unusable pages [] |
| judgment | STATE OF UTTAR PRADESH & ANR. versus AKHIL SHARDA & ORS. | pages 13, units 39 (38 numbered), opinions 1, unusable pages [] |
| judgment | STATE OF UTTAR PRADESH THROUGH PRINICIPAL SECRETARY & ORS ve | pages 18, units 48 (47 numbered), opinions 1, unusable pages [] |
| judgment | STATE OF UTTARAKHAND & ORS. versus RAJIV BERRY & ORS. | pages 11, units 24 (23 numbered), opinions 1, unusable pages [] |
| judgment | STATE THROUGH CENTRAL BUREAU OF INVESTIGATION versus HEMENDH | pages 51, units 150 (149 numbered), opinions 1, unusable pages [] |
| judgment | STATE THROUGH DEPUTY SUPERINTENDENT OF POLICE versus R. SOUN | pages 56, units 124 (123 numbered), opinions 1, unusable pages [] |
| judgment | SUBHASH CHANDER & ORS. versus M/S BHARAT PETROLEUM CORPORATI | pages 13, units 33 (32 numbered), opinions 1, unusable pages [] |
| judgment | SUBHECHHA WELFARE SOCIETY versus M/S. EARTH INFRASTRUCTURE P | pages 4, units 11 (10 numbered), opinions 1, unusable pages [] |
| judgment | SUBODH KUMAR versus SHAMIM AHMED | pages 24, units 58 (57 numbered), opinions 1, unusable pages [] |
| judgment | SUBRATA ROY SAHARA versus PRAMOD KUMAR SAINI & ORS. | pages 4, units 22 (21 numbered), opinions 1, unusable pages [] |
| judgment | SUCHA SINGH SODHI (D) THR. LRS. versus BALDEV RAJ WALIA & AN | pages 13, units 53 (52 numbered), opinions 1, unusable pages [] |
| judgment | SUDAM KISAN GAVANE (D) THR. LRS. & ORS. versus MANIK ANANTA  | pages 5, units 13 (12 numbered), opinions 1, unusable pages [] |
| judgment | SUDEEP CHATTERJEE versus STATE OF BIHAR & ANR. | pages 8, units 14 (13 numbered), opinions 1, unusable pages [] |
| judgment | SUDHIR KUMAR @ S. BALIYAN versus VINAY KUMAR G.B. | pages 19, units 39 (38 numbered), opinions 1, unusable pages [] |
| judgment | SUDHIR RANJAN PATRA (DEAD) THR. LRS. & ANR. versus HIMANSU S | pages 8, units 18 (17 numbered), opinions 1, unusable pages [] |
| judgment | SUDIN DILIP TALAULIKAR versus POLYCAP WIRES PVT. LTD. AND OT | pages 10, units 22 (21 numbered), opinions 1, unusable pages [] |
| judgment | SUGHAR SINGH versus HARI SINGH (DEAD) THROUGH LRS. & ORS. | pages 22, units 54 (53 numbered), opinions 1, unusable pages [] |
| judgment | SUKHBIR versus AJIT SINGH | pages 11, units 27 (26 numbered), opinions 1, unusable pages [] |
| judgment | SUKHBIRI DEVI & ORS versus UNION OF INDIA & ORS. | pages 20, units 38 (37 numbered), opinions 1, unusable pages [] |
| judgment | SUKHPAL SINGH KHAIRA versus THE STATE OF PUNJAB | pages 34, units 53 (52 numbered), opinions 1, unusable pages [] |
| judgment | SUKHPAL SINGH versus NCT OF DELHI | pages 22, units 55 (54 numbered), opinions 1, unusable pages [] |
| judgment | SUKHWINDER SINGH versus JAGROOP SINGH & ANR. | pages 11, units 16 (15 numbered), opinions 1, unusable pages [] |
| judgment | SUMAN DEVI versus MANISHA DEVI AND ORS. | pages 9, units 16 (15 numbered), opinions 1, unusable pages [] |
| judgment | SUMAN MISHRA & ORS. versus THE STATE OF UTTAR PRADESH & ANR. | pages 10, units 28 (27 numbered), opinions 1, unusable pages [] |
| judgment | SUMIT KUMAR SAHA versus RELIANCE GENERAL INSURANCE COMPANY L | pages 16, units 25 (24 numbered), opinions 1, unusable pages [] |
| judgment | SUMITRABEN SINGABHAI GAMIT versus STATE OF GUJARAT & ORS. | pages 5, units 15 (14 numbered), opinions 1, unusable pages [] |
| judgment | SUNIL KUMAR MAITY versus STATE BANK OF INDIA AND ANR. | pages 11, units 15 (14 numbered), opinions 1, unusable pages [] |
| judgment | SUNIL TODI & ORS. versus STATE OF GUJARAT & ANR. | pages 37, units 76 (75 numbered), opinions 1, unusable pages [] |
| judgment | SUNITA PALITA & OTHERS versus M/S PANCHAMI STONE QUARRY | pages 20, units 56 (54 numbered), opinions 1, unusable pages [] |
| judgment | SURAT SINGH (DEAD) versus SIRI BHAGWAN & ORS. | pages 13, units 42 (41 numbered), opinions 1, unusable pages [] |
| judgment | SURENDER SINGH versus STATE OF HARYANA & ORS. | pages 13, units 49 (48 numbered), opinions 1, unusable pages [] |
| judgment | SURESH KUMAR WADHWA versus STATE OF M.P. & ORS. | pages 16, units 56 (55 numbered), opinions 1, unusable pages [] |
| judgment | SURESH LATARUJI RAMTEKE versus SAU. SUMANBAI PANDURANG PETKA | pages 17, units 41 (40 numbered), opinions 1, unusable pages [] |
| judgment | SURESH SHAH versus HIPAD TECHNOLOGY INDIA PRIVATE LIMITED | pages 14, units 29 (28 numbered), opinions 1, unusable pages [] |
| judgment | SURINDER KAUR (D) THR. LR. JASINDERJIT SINGH (D) THR. LRS. v | pages 9, units 16 (15 numbered), opinions 1, unusable pages [] |
| judgment | SUSHIL KUMAR AGARWAL versus MEENAKSHI SADHU & ORS. | pages 25, units 51 (50 numbered), opinions 1, unusable pages [] |
| judgment | SUSHIL THOMAS ABRAHAM versus M/S. SKYLINE BUILD. THR. ITS PA | pages 9, units 38 (37 numbered), opinions 1, unusable pages [] |
| judgment | SWAMI SHIVSHANKARGIRI CHELLA SWAMI & ANR. versus SATYA GYAN  | pages 14, units 35 (34 numbered), opinions 1, unusable pages [] |
| judgment | SYEDA RAHIMUNNISA versus MALAN BL (DEAD) BY L.RS. & ANR. ETC | pages 19, units 60 (59 numbered), opinions 1, unusable pages [] |
| judgment | TALAT SANVI versus STATE OF JHARKHAND & ANR. | pages 4, units 16 (15 numbered), opinions 1, unusable pages [] |
| judgment | TAMIL NADU HOUSING BOARD versus ABDUL SALAM SARKAR (DEAD) AN | pages 6, units 15 (14 numbered), opinions 1, unusable pages [] |
| judgment | TANUKU TALUK VILLAGE OFFICERS’ ASSOCIATION versus TANUKU MUN | pages 6, units 26 (25 numbered), opinions 1, unusable pages [] |
| judgment | TARINA SEN versus UNION OF INDIA & ANR. | pages 8, units 32 (31 numbered), opinions 1, unusable pages [] |
| judgment | TEK SINGH versus SHASHI VERMA AND ANR. | pages 6, units 17 (16 numbered), opinions 1, unusable pages [] |
| judgment | THAKORE UMEDSING NATHUSING versus STATE OF GUJARAT | pages 18, units 27 (26 numbered), opinions 1, unusable pages [] |
| judgment | THE AGRICULTURAL PRODUCE MARKETING COMMITTEE BANGALORE versu | pages 20, units 60 (59 numbered), opinions 1, unusable pages [] |
| judgment | THE ANDHRA PRADESH INDUSTRIAL INFRASTRUCTURE CORPORATION LIM | pages 14, units 31 (30 numbered), opinions 1, unusable pages [] |
| judgment | THE BRANCH MANAGER NATIONAL INSURANCE CO. LTD. versus SMT. M | pages 15, units 45 (44 numbered), opinions 1, unusable pages [] |
| judgment | THE CENTRAL PROVIDENT FUND COMMISSIONER, NEW DELHI AND ORS.  | pages 2, units 12 (11 numbered), opinions 1, unusable pages [] |
| judgment | THE CENTRAL WAREHOUSING CORPORATION versus THAKUR DWARA KALA | pages 9, units 34 (33 numbered), opinions 1, unusable pages [] |
| judgment | THE CHAIRMAN & MANAGING DIRECTOR, CITY UNION BANK LTD. & ANR | pages 9, units 16 (15 numbered), opinions 1, unusable pages [] |
| judgment | THE COMMISSIONER, MYSORE URBAN DEVELOPMENT AUTHORITY versus  | pages 8, units 27 (26 numbered), opinions 1, unusable pages [] |
| judgment | THE CORPORATION OF MADRAS & ANR. versus M. PARTHASARATHY & O | pages 6, units 25 (24 numbered), opinions 1, unusable pages [] |
| judgment | THE EXECUTIVE ENGINEER, GOSIKHURD PROJECT AMBADI, BHANDARA,  | pages 39, units 65 (64 numbered), opinions 1, unusable pages [] |
| judgment | THE EXECUTIVE ENGINEER, KNNL versus SUBHASHCHANDRA & ORS. | pages 12, units 22 (21 numbered), opinions 1, unusable pages [] |
| judgment | THE EXECUTIVE ENGINEER, M.I.W. versus VITTHAL DAMODAR PATIL  | pages 12, units 25 (24 numbered), opinions 1, unusable pages [] |
| judgment | THE HIGH COURT OF JUDICATURE AT MADRAS REP. BY ITS REGISTRAR | pages 14, units 33 (32 numbered), opinions 1, unusable pages [] |
| judgment | THE JAMIA MASJID versus SRI K V RUDRAPPA (SINCE DEAD) BY LRS | pages 48, units 76 (0 numbered), opinions 1, unusable pages [] |
| judgment | THE JOINT LABOUR COMMISSIONER AND REGISTERING OFFICER & ANR. | pages 25, units 44 (43 numbered), opinions 1, unusable pages [] |
| judgment | THE KOLHAPUR MUNICIPAL CORPORATION & ORS. versus VASANT MAHA | pages 41, units 91 (90 numbered), opinions 1, unusable pages [] |
| judgment | THE MADHYA PRADESH MADHYA KSHETRA VIDYUT VITRAN COMPANY LIMI | pages 25, units 30 (0 numbered), opinions 1, unusable pages [] |
| judgment | THE MANAGING DIRECTOR (SHRI GRISH BATRA) M/S. PADMINI INFRAS | pages 14, units 52 (51 numbered), opinions 1, unusable pages [] |
| judgment | THE REVENUE DIVISIONAL OFFICER & ANR. versus ISMAIL BHAI AND | pages 10, units 20 (19 numbered), opinions 1, unusable pages [] |
| judgment | THE SECRETARY, LAND & BUILDING DEPT. GOVT. OF NCT OF DELHI & | pages 6, units 20 (19 numbered), opinions 1, unusable pages [] |
| judgment | THE SECRETARY, MINISTRY OF COMMERCE & ORS. versus M/S VINOD  | pages 10, units 27 (26 numbered), opinions 1, unusable pages [] |
| judgment | THE SECRETARY, THE DEPARTMENT OF LAND AND BUILDING AND ORS.  | pages 8, units 22 (21 numbered), opinions 1, unusable pages [] |
| judgment | THE SPECIAL AGRICULTURAL PRODUCE MARKET COMMITTEE FOR FRUITS | pages 4, units 13 (12 numbered), opinions 1, unusable pages [] |
| judgment | THE STATE OF ANDHRA PRADESH & ANR versus VIJAYANAGARAM CHINN | pages 5, units 16 (0 numbered), opinions 1, unusable pages [] |
| judgment | THE STATE OF ARUNACHAL PRADESH versus KAMAL AGARWAL & ORS. E | pages 9, units 24 (23 numbered), opinions 1, unusable pages [] |
| judgment | THE STATE OF BIHAR & ORS. versus MODERN TENT HOUSE & ANR. | pages 3, units 11 (10 numbered), opinions 1, unusable pages [] |
| judgment | THE STATE OF HARYANA & ORS versus RAJ KUMAR @ BITTU | pages 25, units 43 (42 numbered), opinions 1, unusable pages [11] |
| judgment | THE STATE OF HARYANA & ORS. versus SUSHILA & ORS. | pages 6, units 14 (13 numbered), opinions 1, unusable pages [] |
| judgment | THE STATE OF HIMACHAL PRADESH & ORS. versus CHANDERVIR SINGH | pages 5, units 15 (14 numbered), opinions 1, unusable pages [] |
| judgment | THE STATE OF JHARKHAND versus SURENDRA KUMAR SRIVASTAVA & OR | pages 14, units 65 (64 numbered), opinions 1, unusable pages [] |
| judgment | THE STATE OF KERALA & ORS versus M/S JOSEPH & COMPANY | pages 22, units 43 (42 numbered), opinions 1, unusable pages [] |
| judgment | THE STATE OF KERALA versus K. AJITH & ORS. | pages 76, units 160 (158 numbered), opinions 1, unusable pages [] |
| judgment | THE STATE OF MAHARASHTRA & ANR. versus DR. MAROTI S/O KASHIN | pages 16, units 32 (31 numbered), opinions 1, unusable pages [] |
| judgment | THE STATE OF MAHARASHTRA AND OTHERS versus M/S MOTI RATAN ES | pages 18, units 39 (38 numbered), opinions 1, unusable pages [] |
| judgment | THE STATE OF PUNJAB AND ORS. versus BHAGWANTPAL SINGH ALIAS  | pages 15, units 40 (39 numbered), opinions 1, unusable pages [] |
| judgment | THE STATE OF TAMIL NADU versus DR. VASANTHI VEERASEKARAN | pages 16, units 34 (33 numbered), opinions 1, unusable pages [] |
| judgment | THE STATE OF TELANGANA & ORS. versus MOHD. ABDUL QASIM (DIED | pages 62, units 88 (87 numbered), opinions 1, unusable pages [] |
| judgment | THE STATE THROUGH CENTRAL BUREAU OF INVESTIGATION versus T.  | pages 24, units 57 (56 numbered), opinions 1, unusable pages [] |
| judgment | THE SUB REGISTRAR, AMUDALAVALASA & ANR. versus M/S DANKUNI S | pages 41, units 79 (78 numbered), opinions 1, unusable pages [] |
| judgment | THULASIDHARA & ANOTHER versus NARAYANAPPA & OTHERS | pages 22, units 61 (60 numbered), opinions 1, unusable pages [] |
| judgment | TRILOKI NATH SINGH versus ANIRUDH SINGH (D) THR. LRS. & ORS. | pages 14, units 35 (34 numbered), opinions 1, unusable pages [] |
| judgment | TUKARAM S/O SADASHIV CHAUDHARI versus THE EXECUTIVE ENGINEER | pages 6, units 22 (21 numbered), opinions 1, unusable pages [] |
| judgment | U. SUDHEERA & OTHERS versus C. YASHODA & OTHERS | pages 18, units 37 (36 numbered), opinions 1, unusable pages [] |
| judgment | U.N. KRISHNAMURTHY (SINCE DECEASED) THR. LRS. versus A. M. K | pages 24, units 56 (55 numbered), opinions 1, unusable pages [] |
| judgment | U.P. AVAS EVAM VIKAS PARISHAD THROUGH HOUSING COMMISSIONER & | pages 14, units 32 (31 numbered), opinions 1, unusable pages [] |
| judgment | U.P. AWAS EVAM VIKAS PARISHAD THROUGH HOUSING COMMISSIONER v | pages 26, units 53 (52 numbered), opinions 1, unusable pages [] |
| judgment | U.P. AWAS EVAM VIKASH PARISHAD versus ASHA RAM (D) THR. LRS  | pages 25, units 58 (57 numbered), opinions 1, unusable pages [] |
| judgment | UDDAR GAGAN PROPERTIES LTD. versus SANT SINGH & ORS. | pages 29, units 42 (40 numbered), opinions 1, unusable pages [] |
| judgment | UMA PANDEY & ANR. versus MUNNA PANDEY & ORS. | pages 6, units 26 (25 numbered), opinions 1, unusable pages [] |
| judgment | UMA SHANKAR & ORS. versus R. HANUMAIAH SINCE DECEASED THROUG | pages 9, units 21 (20 numbered), opinions 1, unusable pages [] |
| judgment | UMMER versus POTTENGAL SUBIDA & ORS. | pages 5, units 22 (21 numbered), opinions 1, unusable pages [] |
| judgment | UNION OF INDIA & ANR. versus BALWANT SINGH & ORS. | pages 3, units 8 (7 numbered), opinions 1, unusable pages [] |
| judgment | UNION OF INDIA & ANR. versus M/S INDUSIND BANK LTD. & ANR. | pages 23, units 50 (48 numbered), opinions 1, unusable pages [] |
| judgment | UNION OF INDIA & ANR. versus M/S. K.C. SHARMA & CO. & ORS. | pages 11, units 18 (17 numbered), opinions 1, unusable pages [] |
| judgment | UNION OF INDIA & ANR. versus N. R. SRIVASTA & ORS. | pages 7, units 19 (18 numbered), opinions 1, unusable pages [] |
| judgment | UNION OF INDIA & ANR. versus PUSHPAVATHI & ORS. ETC. | pages 17, units 65 (64 numbered), opinions 1, unusable pages [] |
| judgment | UNION OF INDIA & ANR. versus S. NARASIMHULU NAIDU (DEAD) THR | pages 39, units 75 (74 numbered), opinions 1, unusable pages [] |
| judgment | UNION OF INDIA & ANR. versus SUBHASH CHANDER SEHGAL & ORS. | pages 5, units 19 (18 numbered), opinions 1, unusable pages [] |
| judgment | UNION OF INDIA & ANR. versus TARSEM SINGH & ORS. | pages 12, units 25 (24 numbered), opinions 1, unusable pages [] |
| judgment | UNION OF INDIA & ORS. versus GOPALDAS BHAGWAN DAS & ORS. | pages 11, units 24 (23 numbered), opinions 1, unusable pages [] |
| judgment | UNION OF INDIA AND ANOTHER versus MOHIUDDIN MASOOD AND OTHER | pages 11, units 30 (29 numbered), opinions 1, unusable pages [] |
| judgment | UNION OF INDIA THROUGH LAND ACQUISITION COLLECTOR versus RAJ | pages 5, units 16 (15 numbered), opinions 1, unusable pages [] |
| judgment | UNION OF INDIA versus RAMCHANDRA & ORS. | pages 19, units 45 (44 numbered), opinions 1, unusable pages [] |
| judgment | URMILA DEVI AND OTHERS versus THE DEITY, MANDIR SHREE CHAMUN | pages 9, units 24 (23 numbered), opinions 1, unusable pages [] |
| judgment | URVASHIBEN & ANR. versus KRISHNAKANT MANUPRASAD TRIVEDI | pages 11, units 18 (17 numbered), opinions 1, unusable pages [] |
| judgment | UTTARADI MUTT versus RAGHAVENDRA SWAMY MUTT | pages 17, units 35 (34 numbered), opinions 1, unusable pages [] |
| judgment | V NAGARAJAN versus SKS ISPAT AND POWER LTD.& ORS. | pages 31, units 51 (49 numbered), opinions 1, unusable pages [] |
| judgment | V. PRABHAKARA versus BASAVARAJ K. (DEAD) BY LR. & ANR. | pages 19, units 57 (56 numbered), opinions 1, unusable pages [] |
| judgment | V. RAJENDRAN AND ANR. versus ANNASAMY PANDLAN (D) THR. LRS.  | pages 8, units 18 (17 numbered), opinions 1, unusable pages [] |
| judgment | VAISHNO DEVI CONSTRUCTION REP. THR. SOLE PROPRIETOR (D) THR. | pages 13, units 41 (40 numbered), opinions 1, unusable pages [] |
| judgment | VARADARAJAN versus KANAKAVALLI & ORS. | pages 13, units 26 (25 numbered), opinions 1, unusable pages [] |
| judgment | VARSHA GARG versus THE STATE OF MADHYA PRADESH & ORS. | pages 24, units 75 (74 numbered), opinions 1, unusable pages [] |
| judgment | VARUN PAHWA versus MRS. RENU CHAUDHARY | pages 7, units 17 (16 numbered), opinions 1, unusable pages [] |
| judgment | VASANTHI versus VENUGOPAL (D) THR. LRS. | pages 15, units 40 (39 numbered), opinions 1, unusable pages [] |
| judgment | VASHDEO R BHOJWANI versus ABHYUDAYA CO-OPERATIVE BANK LTD &  | pages 3, units 7 (6 numbered), opinions 1, unusable pages [] |
| judgment | VED & ANR. versus STATE OF HARYANA & ANR. | pages 13, units 22 (21 numbered), opinions 1, unusable pages [] |
| judgment | VED PAL (D) THROUGH LRS & ORS. versus PREM DEVI (D) THROUGH  | pages 4, units 15 (14 numbered), opinions 1, unusable pages [] |
| judgment | VEENA SINGH (DEAD) THROUGH LR versus THE DISTRICT REGISTRAR/ | pages 55, units 123 (121 numbered), opinions 1, unusable pages [] |
| judgment | VIBHA BAKSHI GOKHALE & ANR. versus M/S. GRUHASHILP CONSTRUCT | pages 4, units 10 (6 numbered), opinions 1, unusable pages [] |
| judgment | VIJAY ARJUN BHAGAT & ORS. versus NANA LAXMAN TAPKIRE & ORS. | pages 9, units 35 (34 numbered), opinions 1, unusable pages [] |
| judgment | VIJAY KUMAR GHAI & ORS. versus THE STATE OF WEST BENGAL & OR | pages 29, units 56 (55 numbered), opinions 1, unusable pages [] |
| judgment | VIJAY LATKA & ANR. versus STATE OF HARYANA & ORS. | pages 4, units 14 (13 numbered), opinions 1, unusable pages [] |
| judgment | VIJAY MAHADEORAO KUBADE versus STATE OF MAHARASHTRA THROUGH  | pages 7, units 20 (19 numbered), opinions 1, unusable pages [] |
| judgment | VIJAY RAJMOHAN versus STATE REPRESENTED BY THE INSPECTOR OF  | pages 20, units 55 (54 numbered), opinions 1, unusable pages [] |
| judgment | VIKAS RATHI versus THE STATE OF U.P. & ANR. | pages 6, units 21 (20 numbered), opinions 1, unusable pages [] |
| judgment | VINAYAK PURSHOTTAM DUBE (DECEASED), THROUGH LRS. versus JAYA | pages 19, units 51 (50 numbered), opinions 1, unusable pages [] |
| judgment | VINOD JAIN versus SANTOKBA DURLABHJI MEMORIAL HOSPITAL & ANR | pages 11, units 25 (24 numbered), opinions 1, unusable pages [] |
| judgment | VIRENDER KHULLAR versus AMERICAN CONSOLIDATION SERVICES LTD. | pages 9, units 25 (24 numbered), opinions 1, unusable pages [] |
| judgment | VISAKHAPATNAM URBAN DEVELOPMENT AUTHORITY versus S.S. NAIDU  | pages 6, units 16 (15 numbered), opinions 1, unusable pages [] |
| judgment | VISHNOO MITTAL versus M/S SHAKTI TRADING COMPANY | pages 9, units 22 (21 numbered), opinions 1, unusable pages [] |
| judgment | VISHNU KUMAR SHUKLA & ANR versus THE STATE OF UTTAR PRADESH  | pages 19, units 49 (48 numbered), opinions 1, unusable pages [] |
| judgment | VISHWABANDHU versus SRI KRISHNA AND ANR. | pages 8, units 25 (24 numbered), opinions 1, unusable pages [] |
| judgment | VITHAL RAO & ANR. ETC. versus THE SPECIAL LAND ACQUISITION O | pages 12, units 47 (45 numbered), opinions 1, unusable pages [] |
| judgment | VITHAL TUKARAM KADAM AND ANOTHER versus VAMANRAO SAWALARAM B | pages 9, units 19 (18 numbered), opinions 1, unusable pages [] |
| judgment | VURIMI PULLARAO S/O SATYANARAYANA versus VEMARI VYANKATA RAD | pages 19, units 31 (30 numbered), opinions 1, unusable pages [] |
| judgment | WAHEED-UR-REHMAN PARRA versus UNION TERRITORY OF JAMMU & KAS | pages 12, units 42 (41 numbered), opinions 1, unusable pages [] |
| judgment | WALCHANDNAGAR INDUSTRIES LTD. versus THE STATE OF MAHARASHTR | pages 35, units 86 (85 numbered), opinions 1, unusable pages [] |
| judgment | WAZIR & ANR. versus STATE OF HARYANA | pages 30, units 49 (48 numbered), opinions 1, unusable pages [] |
| judgment | WEST INTERNATIONAL CITY PVT LTD versus DEVASIS RUDRA | pages 6, units 19 (18 numbered), opinions 1, unusable pages [] |
| judgment | WG. CDR. ARIFUR RAHMAN KHAN AND ALEYA SULTANA AND ORS. versu | pages 49, units 93 (92 numbered), opinions 1, unusable pages [] |
| judgment | WYETH LIMITED & ORS. versus STATE OF BIHAR & ANR. | pages 6, units 21 (20 numbered), opinions 1, unusable pages [] |
| judgment | X versus STATE OF RAJASTHAN & ANR. | pages 6, units 24 (23 numbered), opinions 1, unusable pages [] |
| judgment | Y. P. LELE versus MAHARASHTRA STATE ELECTRICITY DISTRIBUTION | pages 9, units 32 (31 numbered), opinions 1, unusable pages [] |
| judgment | Y. SAVARIMUTHU versus STATE OF TAMIL NADU & ORS. | pages 15, units 29 (28 numbered), opinions 1, unusable pages [] |
| judgment | YAMUNA EXPRESSWAY INDUSTRIAL DEVELOPMENT AUTHORITY ETC. vers | pages 38, units 121 (120 numbered), opinions 1, unusable pages [] |
| judgment | YASHODHAN SINGH & ORS. versus THE STATE OF UTTAR PRADESH & A | pages 25, units 81 (80 numbered), opinions 1, unusable pages [] |
| judgment | YERUVA SAYIREDDY versus THE STATE OF ANDHRA PRADESH & ANR. | pages 2, units 5 (0 numbered), opinions 1, unusable pages [] |
| judgment | YOGESH GOYANKA versus GOVIND & ORS. | pages 8, units 25 (24 numbered), opinions 1, unusable pages [] |
| judgment | YOGESH UPADHYAY AND ANR. versus ATLANTA LIMITED | pages 8, units 16 (15 numbered), opinions 1, unusable pages [] |
| judgment | YUVRAJ LAXMILAL KANTHER & ANR. versus STATE OF MAHARASHTRA | pages 14, units 50 (49 numbered), opinions 1, unusable pages [] |
| statute | Bharatiya Nagarik Suraksha Sanhita, 2023 | sections 531/531 (missing []), state blocks 0, footnotes 1, unusable pages [] |
| statute | Bharatiya Nyaya Sanhita, 2023 | sections 358/358 (missing []), state blocks 0, footnotes 1, unusable pages [] |
| statute | Bharatiya Sakshya Adhiniyam, 2023 | sections 170/170 (missing []), state blocks 0, footnotes 1, unusable pages [] |
| statute | Code of Civil Procedure, 1908 | sections 171/171 (missing []), state blocks 50, footnotes 624, unusable pages [334, 335] |
| statute | Consumer Protection Act, 2019 | sections 107/107 (missing []), state blocks 0, footnotes 3, unusable pages [] |
| statute | Indian Contract Act, 1872 | sections 268/268 (missing []), state blocks 2, footnotes 54, unusable pages [] |
| statute | Limitation Act, 1963 | sections 32/32 (missing []), state blocks 1, footnotes 0, unusable pages [] |
| statute | Real Estate (Regulation and Development) Act, 2016 | sections 92/92 (missing []), state blocks 0, footnotes 13, unusable pages [] |
| statute | Registration Act, 1908 | sections 96/96 (missing []), state blocks 144, footnotes 68, unusable pages [] |
| statute | Right to Fair Compensation and Transparency in Land Acquisit | sections 114/114 (missing []), state blocks 27, footnotes 2, unusable pages [] |
| statute | Specific Relief Act, 1963 | sections 46/48 (missing ['43', '44']), state blocks 0, footnotes 20, unusable pages [] |
| statute | Transfer of Property Act, 1882 | sections 147/147 (missing []), state blocks 1, footnotes 154, unusable pages [] |

## Gate

Every required field green: **PASS**
