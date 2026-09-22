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
    min_evidence_score: float = 0.30  # reranker-score gate (Phase 2)
    # Phase 1 gate on the top dense cosine, until the reranker gate exists. Provisional: in-corpus known items
    # scored ~0.70 and out-of-corpus questions <= 0.55 on 2026-09-23 (n=7, DECISIONS D11); calibrate in Phase 2.
    min_dense_score: float = 0.60

    # --- LLM routing
    llm_classify: Literal["rules", "ollama"] = "rules"
    llm_rewrite: Literal["aliases", "ollama"] = "aliases"
    llm_answer: Literal["ollama", "bedrock", "extractive"] = "ollama"
    llm_fallback: str = "extractive"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = ""
    ollama_timeout_s: float = 180.0
    privacy_mode: Literal["standard", "strict"] = "standard"
    cache_enabled: bool = True
    cache_ttl_hours: int = 72

    # --- AWS
    aws_profile: str = "praetor"
    aws_region: str = "ap-south-1"
    s3_bucket: str = ""
    bedrock_model_id: str = ""
    bedrock_daily_budget_usd: float = 2.00
    prices_file: Path = Field(default=REPO_ROOT / "app" / "config" / "prices.yaml")

    # --- API and ops
    api_key: str = ""
    log_level: str = "INFO"
    log_queries: Literal["hash", "full"] = "hash"
    http_user_agent: str = "PRAETOR-AI-MVP/0.1 (informational legal RAG research prototype)"
    hf_token: str = ""

    @field_validator("data_dir", "prices_file", mode="after")
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
