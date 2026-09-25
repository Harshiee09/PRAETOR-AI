# PRAETOR AI knowledge base — index

## How to use this KB (for agents)
1. Read this index first, then open only the 1–3 notes the current task needs. Paths are relative to the repository root.
2. Notes are specs and decisions, not code. If code and a note disagree, stop and flag it rather than silently picking one.
3. Mention a note's `id` in plans and commit messages when it drove a decision.
4. `docs/sources/` holds the two original research reports, for traceability only. They contain errors that `20260922-report-validation` lists. Never copy from them without checking that note.

## How to update this KB (for agents)
- Same idea, new detail: edit the note in place and bump `updated`. Genuinely new idea: create a new atomic note.
- Any create, rename or delete updates this registry and the topic's `_topic.md` in the same commit.
- Use only the controlled tags below; add a tag here before using it.
- Living logs sit outside the registry: `docs/STATUS.md` (current state, rewritten freely) and `docs/DECISIONS.md` (append-only, dated).

## Controlled tags
`architecture`, `schema`, `retrieval`, `llm`, `legal`, `safety`, `data`, `licensing`, `multilingual`, `aws` (historical), `cost`, `evaluation`, `plan`

## Registry

### architecture
- `20260922-minimum-viable-architecture` — **Minimum viable architecture** — `docs/topics/architecture/minimum-viable-architecture.md` — Everything runs locally (a Vercel frontend calls the local API), the request flow, the env contract, and what was cut from the AWS blueprint and why.
- `20260922-chunk-schema` — **Chunk schema and provenance** — `docs/topics/architecture/chunk-schema.md` — Storage layout, required provenance fields, parsing and legal-aware chunking rules, and ingestion validation.
- `20260922-retrieval-pipeline` — **Retrieval pipeline** — `docs/topics/architecture/retrieval-pipeline.md` — Query side from classification through hybrid search, fusion, reranking, the evidence gate and context building.
- `20260922-llm-layer` — **LLM layer** — `docs/topics/architecture/llm-layer.md` — Provider interface, task routing, local model selection and the answer cache (local models only).
- `20260925-api` — **API contract** — `docs/topics/architecture/api.md` — The local HTTP API the frontend builds against: endpoints, fields, auth, errors, cache, latency and rendering.

### legal
- `20260922-grounding-and-citations` — **Grounding and citations** — `docs/topics/legal/grounding-and-citations.md` — Answer contract, deterministic citation validator, abstention and high-stakes handling.
- `20260922-statute-status` — **Statute status and repeal** — `docs/topics/legal/statute-status.md` — Registry of in-force and repealed Acts, the 2024 criminal-law transition, authoritative texts and amendment notes.

### data
- `20260922-data-sources` — **Data sources** — `docs/topics/data/data-sources.md` — Verified source registry, licences and terms, the MVP seed corpus and download etiquette.
- `20260922-report-validation` — **Validation of the research reports** — `docs/topics/data/report-validation.md` — Errors found in the two input reports and the correction adopted for each; read before reusing anything from them.
- `20260922-multilingual` — **Multilingual strategy** — `docs/topics/data/multilingual.md` — One pipeline for all 22 scheduled languages: registry, detection, normalisation, retrieval and translation.

### ops
- `20260925-deployment` — **Deployment** — `docs/topics/ops/deployment.md` — Local-only backend, Vercel-hosted frontend, the tunnel between them, secrets, limits and cost (AWS dropped, DECISIONS D47).
- `20260922-evaluation` — **Evaluation** — `docs/topics/ops/evaluation.md` — Gold set format, metrics, data-profile gates and how to compare configurations honestly.
- `20260922-build-plan` — **3-day build plan** — `docs/topics/ops/build-plan.md` — Phases with acceptance criteria, the session protocol, the cut list and the final report format.
