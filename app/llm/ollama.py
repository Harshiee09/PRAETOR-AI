"""Local generation through Ollama's /api/chat."""

from __future__ import annotations

import time

import httpx

from app.llm.base import LLMError, LLMResult, Message


class OllamaClient:
    name = "ollama"

    def __init__(self, base_url: str, model: str, timeout_s: float = 180.0, num_ctx: int = 8192):
        if not model:
            raise LLMError("OLLAMA_MODEL is not set")
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_s = timeout_s
        self.num_ctx = num_ctx

    def generate(self, messages: list[Message], *, system: str, max_tokens: int,
                 temperature: float = 0.1, json_schema: dict | None = None) -> LLMResult:
        payload = {
            "model": self.model,
            "messages": [{"role": "system", "content": system}] + [{"role": m.role, "content": m.content} for m in messages],
            "stream": False,
            "think": False,  # thinking models (qwen3.5) must not spend the budget on hidden reasoning
            "options": {"temperature": temperature, "num_predict": max_tokens, "num_ctx": self.num_ctx},
        }
        if json_schema:
            payload["format"] = json_schema
        t0 = time.perf_counter()
        try:
            resp = httpx.post(f"{self.base_url}/api/chat", json=payload, timeout=self.timeout_s)
        except (httpx.TransportError, httpx.TimeoutException) as exc:
            raise LLMError(f"Ollama unreachable at {self.base_url}: {exc}") from exc
        if resp.status_code != 200:
            raise LLMError(f"Ollama returned {resp.status_code}: {resp.text[:300]}")
        data = resp.json()
        text = (data.get("message") or {}).get("content", "").strip()
        if not text:
            raise LLMError("Ollama returned an empty answer")
        return LLMResult(text=text, model=self.model, input_tokens=int(data.get("prompt_eval_count") or 0),
                         output_tokens=int(data.get("eval_count") or 0),
                         latency_ms=int((time.perf_counter() - t0) * 1000), cost_usd=None)
