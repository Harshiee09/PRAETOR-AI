"""Provider interface (docs/topics/architecture/llm-layer.md). Nothing outside app/llm/ imports a provider SDK."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass
class Message:
    role: str  # user | assistant
    content: str


@dataclass
class LLMResult:
    text: str
    model: str
    input_tokens: int
    output_tokens: int
    latency_ms: int
    cost_usd: float | None  # None for local providers


class LLMError(RuntimeError):
    """Provider unavailable, timed out, or returned nothing usable; the router falls back."""


class LLMClient(Protocol):
    name: str

    def generate(self, messages: list[Message], *, system: str, max_tokens: int,
                 temperature: float = 0.1, json_schema: dict | None = None) -> LLMResult: ...
