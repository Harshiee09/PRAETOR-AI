---
id: 20260922-llm-layer
title: LLM layer
tags: [llm, architecture]
created: 2026-09-22
updated: 2026-09-25
related: [20260922-minimum-viable-architecture, 20260922-retrieval-pipeline, 20260922-grounding-and-citations, 20260922-evaluation]
summary: Provider interface, task routing, local model selection and the answer cache; local models only (no paid APIs since D47).
---

# LLM layer

> Summary: Provider interface, task routing, local model selection and the answer cache; local models only (no paid APIs since D47).

## Context
Models will be swapped repeatedly during the build — local candidates and no model at all — so nothing outside `app/llm/` may import a provider SDK. There is no training or fine-tuning in this MVP.

## Details

### Interface (`app/llm/base.py`)
```python
class LLMClient(Protocol):
    name: str
    def generate(self, messages: list[Message], *, system: str, max_tokens: int,
                 temperature: float = 0.1, json_schema: dict | None = None) -> LLMResult: ...

@dataclass
class LLMResult:
    text: str
    model: str
    input_tokens: int
    output_tokens: int
    latency_ms: int
```

### Providers
- `OllamaClient` — HTTP to `OLLAMA_BASE_URL` (`/api/chat`), using its structured-output mode for classification and rewriting.
- `ExtractiveClient` — no model at all: returns the top passages verbatim under "Relevant provisions", with their citations and a note that no generative model was used. It is an honest mode rather than a mock, and it keeps the demo alive when everything else fails.

### Routing (`app/llm/router.py`)
Per task, from the environment: `LLM_CLASSIFY` (rules or ollama), `LLM_REWRITE` (aliases or ollama), `LLM_ANSWER` (ollama or extractive), then the `LLM_FALLBACK` chain on errors or timeouts. As built, routing lives in `app/rag/pipeline.py` (`_providers`), and nothing leaves the machine: AWS and Bedrock were dropped on 2026-09-25 (DECISIONS D47). Routing never depends on a model's self-reported confidence.

### Optional local tasks
Summarising a long judgment chunk into a short case note for the context, cached and labelled as a summary — the citation still points at the underlying chunk, never at the summary. Also all privacy-sensitive preprocessing, which must happen before anything leaves the machine.

### Choosing the local model
Check what the Ollama library offers at build time. Shortlist two or three current instruct models that fit in the ~5 GB left after the embedder and reranker on the 8 GB dev GPU (2–4B class at 4-bit; see the VRAM budget in the architecture note), favouring good Hindi and Indic coverage. Candidates benchmarked on 2026-09-24: `qwen3.5:4b`, `gemma4:e2b-it-qat` and `gemma4:latest`; the pick is **`gemma4:latest`** (DECISIONS D32, with the numbers). All three fit on the 8 GB GPU next to the encoders (D33 corrects D8). Qwen 3.5 is a thinking model: send `think: false` for answers. Run the eval subset on each — answer quality, `[S#]` marker compliance, latency, VRAM — and record the pick in DECISIONS.md. Use temperature 0 to 0.2 for answers.

### Prompts
Versioned files under `app/rag/prompts/`: `answer_system.md`, `classify.md`, `rewrite.md`. The version string is part of the cache key and of every log record. Answers use inline `[S#]` markers rather than JSON, which is more robust with small local models; the validator does the strict checking afterwards.

### Cache (`cache` table in praetor.sqlite; `app/store/cache.py`, used by the API)
Key: sha256 over the normalised question and everything that changes an answer: mode, prompt version, model and its digest, decoding, the index corpus hash, the registries and the evidence gate. Entries expire after `CACHE_TTL_HOURS`; `explain` requests and transient failures (Ollama unreachable, grounding fallback) are not cached; the question itself is never stored. `praetor ask` and `praetor eval` do not use the cache (DECISIONS D48).

## Related
- [Minimum viable architecture](minimum-viable-architecture.md) — context: fallback behaviour and the env contract.
- [Retrieval pipeline](retrieval-pipeline.md) — prerequisite: produces the context an answer is built from.
- [Grounding and citations](../legal/grounding-and-citations.md) — the contract the answer prompt must meet.
- [Evaluation](../ops/evaluation.md) — how model choices get decided.
