import json

from src.repository import AgentRepo


def test_repo_upsert_and_get_by_slug(tmp_path):
    db_path = tmp_path / "webmanus.db"
    repo = AgentRepo(str(db_path))

    agent = {
        "slug": "demo-worker",
        "name": "Demo",
        "tagline": "Does things",
        "pricing": "free",
        "labor_score": 8.5,
        "browser_native": True,
        "website": "https://example.com",
        "affiliate_url": None,
        "logo_url": None,
        "source_url": "https://github.com/example/repo",
    }
    repo.upsert(agent, ["automation", "research"])

    loaded = repo.get_by_slug("demo-worker")
    assert loaded is not None
    assert loaded["slug"] == "demo-worker"
    assert loaded["name"] == "Demo"
    assert sorted(loaded["capabilities"]) == ["automation", "research"]


def test_repo_search_filters(tmp_path):
    db_path = tmp_path / "webmanus.db"
    repo = AgentRepo(str(db_path))

    repo.upsert(
        {"slug": "a", "name": "A", "tagline": "alpha", "pricing": "free", "labor_score": 9.0},
        ["automation"],
    )
    repo.upsert(
        {"slug": "b", "name": "B", "tagline": "beta", "pricing": "paid", "labor_score": 4.0},
        ["research"],
    )

    items = repo.search(capability="automation", limit=10)
    assert [i["slug"] for i in items] == ["a"]

    items = repo.search(pricing="paid", limit=10)
    assert [i["slug"] for i in items] == ["b"]

    items = repo.search(min_score=5, limit=10)
    assert [i["slug"] for i in items] == ["a"]

    items = repo.search(q="alp", limit=10)
    assert [i["slug"] for i in items] == ["a"]


def test_repo_stores_full_json(tmp_path):
    db_path = tmp_path / "webmanus.db"
    repo = AgentRepo(str(db_path))
    repo.upsert({"slug": "x", "name": "X", "tagline": "t"}, ["general-purpose"])

    loaded = repo.get_by_slug("x")
    assert json.loads(json.dumps(loaded))["slug"] == "x"


def test_repo_search_page_returns_total(tmp_path):
    db_path = tmp_path / "webmanus.db"
    repo = AgentRepo(str(db_path))

    repo.upsert({"slug": "a", "name": "A", "tagline": "alpha", "pricing": "free", "labor_score": 9.0}, ["automation"])
    repo.upsert({"slug": "b", "name": "B", "tagline": "beta", "pricing": "paid", "labor_score": 6.0}, ["research"])

    total, items = repo.search_page(limit=1, offset=0)
    assert total == 2
    assert len(items) == 1
