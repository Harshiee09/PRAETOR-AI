"""Structured JSON logging. Queries are logged as hashes unless LOG_QUERIES=full (local debugging only)."""

from __future__ import annotations

import hashlib
import json
import logging
import sys
from datetime import datetime, timezone

_RESERVED = set(vars(logging.makeLogRecord({})).keys()) | {"message", "asctime"}


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        for key, value in record.__dict__.items():
            if key not in _RESERVED and not key.startswith("_"):
                payload[key] = value
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False, default=str)


def setup_logging(level: str = "INFO") -> None:
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers[:] = [handler]
    root.setLevel(level.upper())
    for noisy in ("httpx", "httpcore", "urllib3", "botocore", "boto3", "s3transfer", "filelock", "pdfminer"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def query_hash(query: str) -> str:
    return hashlib.sha256(query.encode("utf-8")).hexdigest()[:16]


def loggable_query(query: str, mode: str) -> dict:
    """What a log record may contain about a user query."""
    if mode == "full":
        return {"query": query, "query_hash": query_hash(query)}
    return {"query_hash": query_hash(query)}
