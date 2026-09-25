"""HTTP layer of the API: contract shape, auth, request ids, errors, cache, sources.

The answer engine is replaced by a stub that returns a pipeline-shaped dict, so these tests exercise only the API
(the real pipeline is covered by tests/integration/test_api.py). Sources come from real fixture chunks.
"""

import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.api.app import create_app
from app.config import Settings
from app.store.db import connect, replace_document
from tests.unit.helpers import statute_fixture_chunks
from tests.unit.test_store_idempotency import _doc

REG = Path(__file__).parents[2] / "data" / "registry"
LOCAL = ("127.0.0.1", 50000)
REMOTE = ("203.0.113.7", 50000)  # TEST-NET-3 documentation address


class StubEngine:
    prompt_version = "answer-v3"


def _answer_stub(calls):
    def answer(engine, question, *, explain=False, mode="full", trace_id=None):
        calls.append(question)
        out = {"answer_markdown": "**Short answer:** Within four months [S1].", "language": "en", "confidence": "high",
               "abstained": False, "warnings": [], "jurisdiction_note": "Central Acts.", "disclaimer": "Not legal advice.",
               "trace_id": trace_id, "provider": "ollama", "model": "gemma4:latest",
               "classification": {"domain": "property_land", "intent": "statute_lookup", "high_stakes": False},
               "citations": [{"id": "S1", "chunk_id": "c1", "title": "Registration Act, 1908", "locator": "s. 23",
                              "authority": "Parliament of India", "jurisdiction": "IN", "status": "in_force",
                              "source_url": "https://indiacode.gov.in/handle/123456789/496068",
                              "retrieved_at": "2026-09-22", "quote": "Subject to the provisions", "section_heading": "x"}]}
        return {**out, "explain": {"gate": {}}} if explain else out
    return answer


def _client(tmp_path, client=LOCAL, **overrides):
    data = tmp_path / "data"
    if not (data / "registry").exists():
        shutil.copytree(REG, data / "registry")
    settings = Settings(_env_file=None, data_dir=data, llm_answer="extractive", ollama_model="", **overrides)
    calls = []
    app = create_app(settings, engine=StubEngine(), answer_fn=_answer_stub(calls))
    return TestClient(app, client=client), calls, settings


def test_ask_returns_the_contract_and_echoes_the_request_id(tmp_path):
    c, _, _ = _client(tmp_path)
    with c:
        r = c.post("/v1/ask", json={"question": "How long do I have to present a sale deed?"}, headers={"X-Request-ID": "req-123"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["trace_id"] == "req-123" == r.headers["x-request-id"]
    assert body["citations"][0]["locator"] == "s. 23" and body["cached"] is False and body["explain"] is None
    assert set(body) >= {"answer_markdown", "confidence", "abstained", "warnings", "disclaimer", "latency_ms"}


def test_second_identical_question_is_served_from_the_cache(tmp_path):
    c, calls, _ = _client(tmp_path)
    with c:
        first = c.post("/v1/ask", json={"question": "How long do I have to present a sale deed?"}).json()
        second = c.post("/v1/ask", json={"question": "  how long do I have to present a SALE deed?  "}).json()
        explained = c.post("/v1/ask", json={"question": "How long do I have to present a sale deed?", "explain": True}).json()
    assert len(calls) == 2  # the explain request bypasses the cache
    assert first["cached"] is False and second["cached"] is True and second["answer_markdown"] == first["answer_markdown"]
    assert second["trace_id"] != first["trace_id"] and explained["explain"] == {"gate": {}}


def test_cache_can_be_disabled(tmp_path):
    c, calls, _ = _client(tmp_path, cache_enabled=False)
    with c:
        c.post("/v1/ask", json={"question": "q one"})
        c.post("/v1/ask", json={"question": "q one"})
    assert len(calls) == 2


def test_without_api_key_only_direct_localhost_is_served(tmp_path):
    c, _, _ = _client(tmp_path)
    with c:
        assert c.post("/v1/ask", json={"question": "q"}).status_code == 200
        # a tunnel delivers requests from localhost but adds forwarding headers
        r = c.post("/v1/ask", json={"question": "q"}, headers={"X-Forwarded-For": "198.51.100.4"})
    assert r.status_code == 401 and r.json()["error"]["code"] == "unauthorized"
    remote, _, _ = _client(tmp_path, client=REMOTE)
    with remote:
        assert remote.post("/v1/ask", json={"question": "q"}).status_code == 401


def test_with_api_key_every_call_needs_it_except_healthz(tmp_path):
    c, _, _ = _client(tmp_path, client=REMOTE, api_key="s3cret-key")
    with c:
        assert c.post("/v1/ask", json={"question": "q"}).status_code == 401
        assert c.post("/v1/ask", json={"question": "q"}, headers={"X-API-Key": "wrong"}).status_code == 401
        assert c.post("/v1/ask", json={"question": "q"}, headers={"X-API-Key": "s3cret-key"}).status_code == 200
        assert c.get("/v1/stats").status_code == 401
        assert c.get("/v1/healthz").status_code in (200, 503)  # no key needed


def test_invalid_request_uses_the_error_shape(tmp_path):
    c, _, _ = _client(tmp_path)
    with c:
        r = c.post("/v1/ask", json={"question": ""})
    assert r.status_code == 422
    err = r.json()["error"]
    assert err["code"] == "invalid_request" and "question" in err["message"] and err["request_id"] == r.headers["x-request-id"]


def test_sources_returns_the_stored_passage_or_404(tmp_path):
    c, _, settings = _client(tmp_path)
    chunks = statute_fixture_chunks("tpa_1882_s106", "tpa-1882")
    conn = connect(settings.sqlite_path)
    with conn:
        replace_document(conn, _doc(chunks[0]), chunks, "2026-09-25")
    conn.close()
    s106 = next(ch for ch in chunks if ch.locator == "s. 106")
    with c:
        ok = c.get(f"/v1/sources/{s106.chunk_id}")
        missing = c.get("/v1/sources/no-such-chunk")
    assert ok.status_code == 200 and "fifteen days" in ok.json()["text"] and ok.json()["section"] == "106"
    assert missing.status_code == 404 and missing.json()["error"]["code"] == "not_found"


def test_healthz_reports_down_without_an_index(tmp_path):
    c, _, _ = _client(tmp_path)
    with c:
        r = c.get("/v1/healthz")
    assert r.status_code == 503 and r.json()["status"] == "down" and "index" in r.json()["checks"]


def test_cors_allows_only_configured_origins(tmp_path):
    c, _, _ = _client(tmp_path, cors_origins="https://praetor-demo.vercel.app")
    pre = {"Access-Control-Request-Method": "POST", "Access-Control-Request-Headers": "content-type"}
    with c:
        ok = c.options("/v1/ask", headers={"Origin": "https://praetor-demo.vercel.app", **pre})
        bad = c.options("/v1/ask", headers={"Origin": "https://evil.example", **pre})
    assert ok.headers.get("access-control-allow-origin") == "https://praetor-demo.vercel.app"
    assert "access-control-allow-origin" not in bad.headers


def test_openapi_lists_the_four_endpoints(tmp_path):
    data = tmp_path / "data"
    spec = create_app(Settings(_env_file=None, data_dir=data), load_engine=False).openapi()
    assert {"/v1/ask", "/v1/sources/{chunk_id}", "/v1/healthz", "/v1/stats"} <= set(spec["paths"])


@pytest.mark.parametrize("host", ["0.0.0.0", "192.168.1.5"])
def test_serve_refuses_a_public_bind_without_api_key(host, monkeypatch, capsys):
    from app import cli

    monkeypatch.setattr(cli, "get_settings", lambda: Settings(_env_file=None, api_key=""))
    assert cli.main(["serve", "--host", host]) == 2
    assert "API_KEY" in capsys.readouterr().out


def test_demo_checks_catch_orphan_markers_and_missed_abstentions():
    import importlib.util

    spec = importlib.util.spec_from_file_location("demo", Path(__file__).parents[2] / "scripts" / "demo.py")
    demo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(demo)
    good = {"answer_markdown": "x [S1].", "citations": [{"id": "S1"}], "abstained": False}
    assert demo.check(good, should_abstain=False) == []
    assert demo.check({**good, "answer_markdown": "x [S1][S2]."}, False) == ["markers without a source card: ['S2']"]
    assert demo.check(good, should_abstain=True) == ["expected an abstention"]
    from app.rag.evaluate import load_gold

    assert {g for _, g, _ in demo.SCENARIOS} <= {g["id"] for g in load_gold("all")}  # real gold questions only
