# Architecture

How PRAETOR AI is put together: what runs where, how chunks are stored, and how a query becomes a grounded answer.

- [Minimum viable architecture](minimum-viable-architecture.md) — what runs where, request flow, env contract.
- [Chunk schema and provenance](chunk-schema.md) — storage, required fields, legal-aware chunking.
- [Retrieval pipeline](retrieval-pipeline.md) — classification, hybrid search, reranking, context.
- [LLM layer](llm-layer.md) — providers, routing, answer cache.
- [API contract](api.md) — endpoints and fields for the frontend.
