"""Runtime configuration. Everything comes from environment variables (or a local `.env`), never from code.

The field list mirrors the env contract in docs/topics/architecture/minimum-viable-architecture.md.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=REPO_ROOT / ".env", env_file_encoding="utf-8", extra="ignore", case_sensitive=False
    )

    # --- paths and models
    data_dir: Path = Field(default=REPO_ROOT / "data")
    embed_model: str = "BAAI/bge-m3"
    embed_device: Literal["cuda", "cpu"] = "cuda"
    embed_batch_size: int = 16
    rerank_model: str = "BAAI/bge-reranker-v2-m3"
    rerank_device: Literal["cuda", "cpu"] = "cuda"
    max_chunk_tokens: int = 450

    # --- retrieval
    top_k_dense: int = 50
    top_k_keyword: int = 50
    rrf_k: int = 60
    rerank_top_n: int = 30
    context_max_chunks: int = 8
    context_max_tokens: int = 6000
    # reranker-score evidence gate; 0.10 chosen on 2026-09-24 from the 50-question draft gold set (DECISIONS D27)
    min_evidence_score: float = 0.10
    # Phase 1 gate on the top dense cosine, until the reranker gate exists. Provisional: in-corpus known items
    # scored ~0.70 and out-of-corpus questions <= 0.55 on 2026-09-23 (n=7, DECISIONS D11); calibrate in Phase 2.
    min_dense_score: float = 0.60

    # --- LLM routing
    llm_classify: Literal["rules", "ollama"] = "rules"
    llm_rewrite: Literal["aliases", "ollama"] = "aliases"
    llm_answer: Literal["ollama", "bedrock", "extractive"] = "ollama"
    # cloud deployment (DECISIONS D58): Amazon Bedrock; credentials from the instance role or AWS CLI profile
    bedrock_model_id: str = "apac.amazon.nova-pro-v1:0"
    aws_region: str = "ap-south-1"
    llm_fallback: str = "extractive"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = ""
    ollama_timeout_s: float = 180.0
    # Answer decoding. Temperature 0 (greedy) with a fixed seed makes repeated runs comparable; the model's own
    # defaults (gemma4: temperature 1, top_k 64, top_p 0.95) sampled differently each run (DECISIONS D37).
    llm_temperature: float = 0.0
    llm_seed: int = 42
    # Answer cache (SQLite `cache` table), used by the API for non-explain answers; the key includes the prompt,
    # model, decoding and index versions, so any change misses the cache.
    cache_enabled: bool = True
    cache_ttl_hours: int = 72

    # --- uploaded documents (DECISIONS D50): held in memory only, never indexed, cached or written to disk
    doc_max_mb: float = 10.0
    doc_max_pages: int = 80
    doc_ttl_minutes: int = 60
    doc_max_open: int = 20
    # model window for document analyses and the passage budget inside it (prompt ~0.8k + law passages + 1.2k output
    # must fit; the estimate runs ~30% above gemma4's real count on English text, V46); corpus answers keep 8192
    doc_num_ctx: int = 16384
    doc_context_tokens: int = 14000
    doc_law_passages: int = 3
    # scanned pages read with the Windows OCR engine per upload (~0.5 s a page; D55)
    doc_ocr_max_pages: int = 40

    # --- API (local only; the Vercel frontend reaches it through a tunnel, DECISIONS D47)
    # Required for any request that is not a direct localhost call (tunnels arrive as localhost with forwarding
    # headers, so those need the key too). `praetor serve` refuses a non-localhost bind without it.
    api_key: str = ""
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    # comma-separated origins allowed to call the API from a browser, e.g. your Vercel URL
    cors_origins: str = "http://localhost:3000,http://localhost:5173"
    log_level: str = "INFO"
    log_queries: Literal["hash", "full"] = "hash"
    http_user_agent: str = "PRAETOR-AI-MVP/0.1 (informational legal RAG research prototype)"
    hf_token: str = ""

    @field_validator("data_dir", mode="after")
    @classmethod
    def _absolute(cls, v: Path) -> Path:
        return v if v.is_absolute() else (REPO_ROOT / v).resolve()

    # --- derived paths (layout from docs/topics/architecture/chunk-schema.md)
    @property
    def raw_dir(self) -> Path:
        return self.data_dir / "raw"

    @property
    def manifest_path(self) -> Path:
        return self.raw_dir / "manifest.jsonl"

    @property
    def registry_dir(self) -> Path:
        return self.data_dir / "registry"

    @property
    def processed_dir(self) -> Path:
        return self.data_dir / "processed"

    @property
    def sqlite_path(self) -> Path:
        return self.processed_dir / "praetor.sqlite"

    @property
    def index_dir(self) -> Path:
        return self.data_dir / "indexes"

    @property
    def faiss_path(self) -> Path:
        return self.index_dir / "faiss.index"

    @property
    def index_manifest_path(self) -> Path:
        return self.index_dir / "index_manifest.json"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
