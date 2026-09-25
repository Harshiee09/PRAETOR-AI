"""The API over the real index, models and Ollama (Phase 3 acceptance; needs the GPU)."""

import re

import pytest
from fastapi.testclient import TestClient

from app.api.app import create_app
from app.config import get_settings

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def client():
    s = get_settings()
    if not s.faiss_path.exists():
        pytest.skip("index missing: run `praetor index`")
    with TestClient(create_app(s), client=("127.0.0.1", 50000)) as c:
        yield c


def test_health_is_ok_with_the_real_index(client):
    r = client.get("/v1/healthz")
    assert r.status_code == 200 and r.json()["checks"]["index"] == "ok" and r.json()["checks"]["engine"] == "ok"


def test_known_item_question_is_answered_with_its_section_and_resolvable_sources(client):
    r = client.post("/v1/ask", json={"question": "What is the time limit for presenting a document for registration?",
                                     "use_cache": False})
    assert r.status_code == 200, r.text
    body = r.json()
    assert not body["abstained"] and body["citations"]
    assert any(c["title"] == "Registration Act, 1908" and c["locator"] == "s. 23" for c in body["citations"])
    ids = {c["id"] for c in body["citations"]}
    assert set(re.findall(r"\[(S\d+)\]", body["answer_markdown"])) <= ids  # every marker has a card
    src = client.get(f"/v1/sources/{body['citations'][0]['chunk_id']}")
    assert src.status_code == 200 and body["citations"][0]["quote"][:60] in " ".join(src.json()["text"].split())


def test_out_of_corpus_question_abstains_without_citations(client):
    r = client.post("/v1/ask", json={"question": "What documents do I need to apply for a Schengen visa?", "use_cache": False})
    body = r.json()
    assert r.status_code == 200 and body["abstained"] and body["citations"] == [] and body["provider"] is None
