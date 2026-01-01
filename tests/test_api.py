"""
Tests for FastAPI backend (src.api).

These tests stay offline (no network / no LLM calls).
"""

from __future__ import annotations

import json

from fastapi.testclient import TestClient

from src.api import create_app
from src.data_store import load_agents


def test_health(sample_agents, tmp_path):
    data_path = tmp_path / "agents.json"
    data_path.write_text(json.dumps(sample_agents), encoding="utf-8")

    app = create_app(agents_path=data_path)
    # Manually set up the app state that would normally be initialized by lifespan
    from src.api import AppState
    snap = load_agents(path=data_path)
    app.state.state = AppState(snapshot=snap)

    client = TestClient(app)

    resp = client.get("/v1/health")
    assert resp.status_code == 200
    assert resp.json()["ok"] is True


def test_agents_list_and_detail(sample_agents, tmp_path):
    data_path = tmp_path / "agents.json"
    data_path.write_text(json.dumps(sample_agents), encoding="utf-8")

    app = create_app(agents_path=data_path)
    # Manually set up the app state that would normally be initialized by lifespan
    from src.api import AppState
    snap = load_agents(path=data_path)
    app.state.state = AppState(snapshot=snap)

    client = TestClient(app)

    resp = client.get("/v1/agents", params={"page_size": 2})
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == len(sample_agents)
    assert len(body["items"]) == 2

    resp = client.get("/v1/agents/pdf_assistant")
    assert resp.status_code == 200
    assert resp.json()["id"] == "pdf_assistant"


def test_invalid_agent_id_returns_400(sample_agents, tmp_path):
    data_path = tmp_path / "agents.json"
    data_path.write_text(json.dumps(sample_agents), encoding="utf-8")

    app = create_app(agents_path=data_path)
    # Manually set up the app state that would normally be initialized by lifespan
    from src.api import AppState
    snap = load_agents(path=data_path)
    app.state.state = AppState(snapshot=snap)

    client = TestClient(app)

    # FastAPI/TestClient may normalize ".." paths, so use an invalid character instead.
    resp = client.get("/v1/agents/bad$id")
    assert resp.status_code == 400
