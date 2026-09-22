import json
import logging

from app.config.logs import JsonFormatter, loggable_query, query_hash
from app.config.settings import REPO_ROOT, Settings


def test_defaults_follow_env_contract(monkeypatch):
    monkeypatch.delenv("DATA_DIR", raising=False)
    s = Settings(_env_file=None)
    assert s.embed_model == "BAAI/bge-m3"
    assert s.max_chunk_tokens == 450
    assert s.rrf_k == 60
    assert s.log_queries == "hash"
    assert s.data_dir == REPO_ROOT / "data"
    assert s.sqlite_path == REPO_ROOT / "data" / "processed" / "praetor.sqlite"
    assert s.faiss_path.name == "faiss.index"


def test_env_overrides_and_relative_paths(monkeypatch):
    monkeypatch.setenv("DATA_DIR", "./somewhere")
    monkeypatch.setenv("EMBED_DEVICE", "cpu")
    s = Settings(_env_file=None)
    assert s.data_dir == (REPO_ROOT / "somewhere").resolve()
    assert s.embed_device == "cpu"


def test_query_logging_hashes_by_default():
    q = "my neighbour's plot, Aadhaar 1234 5678 9012"
    rec = loggable_query(q, "hash")
    assert rec == {"query_hash": query_hash(q)}
    assert q not in json.dumps(rec)


def test_json_formatter_includes_extras():
    record = logging.makeLogRecord({"msg": "hello", "levelname": "INFO", "name": "t", "trace_id": "abc"})
    out = json.loads(JsonFormatter().format(record))
    assert out["msg"] == "hello" and out["trace_id"] == "abc"
