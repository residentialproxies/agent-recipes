from __future__ import annotations

import json
from types import SimpleNamespace

from fastapi.testclient import TestClient

from src.api import AppState, create_app
from src.config import settings
from src.data_store import load_agents
from src.repository import AgentRepo


def _bootstrap_app(*, tmp_path):
    # Agents JSON is still required for the existing /v1/agents routes.
    data_path = tmp_path / "agents.json"
    data_path.write_text(json.dumps([]), encoding="utf-8")

    db_path = tmp_path / "webmanus.db"
    repo = AgentRepo(str(db_path))
    repo.upsert(
        {
            "slug": "worker-a",
            "name": "Worker A",
            "tagline": "Does A",
            "pricing": "freemium",
            "labor_score": 9.0,
            "website": "https://example.com/a",
        },
        ["automation"],
    )
    repo.upsert(
        {
            "slug": "worker-b",
            "name": "Worker B",
            "tagline": "Does B",
            "pricing": "paid",
            "labor_score": 6.0,
            "website": "https://example.com/b",
        },
        ["research"],
    )

    app = create_app(agents_path=data_path, webmanus_db_path=db_path)
    snap = load_agents(path=data_path)
    app.state.state = AppState(snapshot=snap, webmanus_repo=repo)
    return app


def test_workers_list_and_detail(tmp_path):
    app = _bootstrap_app(tmp_path=tmp_path)
    client = TestClient(app)

    resp = client.get("/v1/workers", params={"limit": 10})
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 2
    slugs = [i["slug"] for i in body["items"]]
    assert slugs == ["worker-a", "worker-b"]  # sorted by labor_score desc

    # Affiliate injected from website
    assert body["items"][0]["affiliate_url"].endswith("ref=webmanus")

    # Pagination should return the full total even when the page is limited.
    resp = client.get("/v1/workers", params={"limit": 1, "offset": 0})
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 2
    assert len(body["items"]) == 1

    resp = client.get("/v1/workers/worker-a")
    assert resp.status_code == 200
    assert resp.json()["slug"] == "worker-a"

    resp = client.get("/v1/workers/does-not-exist")
    assert resp.status_code == 404


def test_capabilities_endpoint(tmp_path):
    app = _bootstrap_app(tmp_path=tmp_path)
    client = TestClient(app)
    resp = client.get("/v1/capabilities")
    assert resp.status_code == 200
    caps = resp.json()
    assert "automation" in caps
    assert "research" in caps


def test_consult_endpoint_offline_stub(tmp_path, monkeypatch):
    # Use isolated cache/budget DBs for this test
    monkeypatch.setattr(settings, "ai_cache_path", tmp_path / "ai_cache.db")
    monkeypatch.setattr(settings, "ai_budget_path", tmp_path / "ai_budget.db")

    monkeypatch.setenv("ANTHROPIC_API_KEY", "test")

    app = _bootstrap_app(tmp_path=tmp_path)
    client = TestClient(app)

    calls = {"n": 0}

    class FakeAnthropic:
        def __init__(self, api_key: str):
            self.api_key = api_key

        class messages:
            @staticmethod
            def create(*, model, max_tokens, messages, timeout):
                calls["n"] += 1
                # Include an invalid slug and a low-score slug to ensure filtering.
                payload = {
                    "recommendations": [
                        {"slug": "worker-a", "match_score": 0.92, "reason": "A helps."},
                        {"slug": "nope", "match_score": 0.99, "reason": "Should be dropped."},
                        {"slug": "worker-b", "match_score": 0.6, "reason": "Too low."},
                    ],
                    "no_match_suggestion": "Try searching for automation tools.",
                }
                return SimpleNamespace(
                    content=[SimpleNamespace(text=json.dumps(payload))],
                    usage=SimpleNamespace(input_tokens=10, output_tokens=20),
                )

    import src.api as api_mod

    monkeypatch.setattr(api_mod, "HAS_ANTHROPIC", True)
    monkeypatch.setattr(api_mod.anthropic, "Anthropic", FakeAnthropic)

    resp = client.post("/v1/consult", json={"problem": "automate emails", "max_candidates": 20})
    assert resp.status_code == 200
    assert resp.headers.get("X-Cache") == "MISS"
    body = resp.json()
    assert [r["slug"] for r in body["recommendations"]] == ["worker-a"]

    resp2 = client.post("/v1/consult", json={"problem": "automate emails", "max_candidates": 20})
    assert resp2.status_code == 200
    assert resp2.headers.get("X-Cache") == "HIT"
    assert calls["n"] == 1
