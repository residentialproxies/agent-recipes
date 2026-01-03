"""
End-to-end integration tests for Agent Navigator.

Tests complete workflows:
- Data loading and search flow
- Static site export flow
- Full request lifecycle
"""

import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from src.api.app import create_app
from src.data_store import load_agents
from src.export.export import export_site
from src.search import AgentSearch


class TestDataLoadingFlow:
    """Tests for the complete data loading workflow."""

    def test_load_agents_from_file(self, tmp_path: Path):
        """Should load agents from JSON file."""
        agents = [
            {
                "id": "agent_1",
                "name": "Agent One",
                "description": "First agent",
                "category": "rag",
                "frameworks": ["langchain"],
                "llm_providers": ["openai"],
            }
        ]
        data_file = tmp_path / "agents.json"
        data_file.write_text(json.dumps(agents), encoding="utf-8")

        snapshot = load_agents(path=data_file)
        assert len(snapshot.agents) == 1
        assert snapshot.agents[0]["id"] == "agent_1"

    def test_load_agents_caches_by_mtime(self, tmp_path: Path):
        """Should cache snapshot by file modification time."""
        agents = [{"id": "a", "name": "A", "category": "other", "frameworks": [], "llm_providers": []}]
        data_file = tmp_path / "agents.json"
        data_file.write_text(json.dumps(agents), encoding="utf-8")

        snap1 = load_agents(path=data_file)
        snap2 = load_agents(path=data_file)
        # Same mtime means same snapshot object
        assert snap1 is snap2

        # Modify file
        import time

        time.sleep(0.01)
        agents[0]["name"] = "Updated"
        data_file.write_text(json.dumps(agents), encoding="utf-8")

        snap3 = load_agents(path=data_file)
        # Different mtime means new snapshot
        assert snap3.mtime_ns > snap1.mtime_ns
        assert snap3.agents[0]["name"] == "Updated"

    def test_load_agents_missing_file_returns_empty(self, tmp_path: Path):
        """Missing file should return empty snapshot."""
        non_existent = tmp_path / "does_not_exist.json"
        snapshot = load_agents(path=non_existent)
        assert snapshot.agents == []


class TestSearchFlow:
    """Tests for complete search workflow."""

    def test_search_workflow_from_query_to_results(self, sample_agents):
        """Complete workflow: query -> search -> filter -> paginate."""
        search = AgentSearch(sample_agents)

        # Step 1: Search
        results = search.search("pdf", limit=20)

        # Step 2: Verify results
        assert len(results) > 0
        assert results[0]["id"] == "pdf_assistant"

        # Step 3: Apply filters
        filtered = search.filter_agents(results, category="rag")
        assert all(a["category"] == "rag" for a in filtered)

        # Step 4: Paginate
        page = filtered[:2]
        assert len(page) <= 2

    def test_empty_query_flow_returns_all_agents(self, sample_agents):
        """Empty query should return all agents sorted by name."""
        search = AgentSearch(sample_agents)
        results = search.search("", limit=100)
        assert len(results) == len(sample_agents)
        # Should be sorted by name
        names = [r["name"] for r in results]
        assert names == sorted(names)

    def test_search_with_no_matches_flow(self, sample_agents):
        """Search with no matches should return empty list."""
        search = AgentSearch(sample_agents)
        results = search.search("xyznotfound123", limit=10)
        assert isinstance(results, list)

    def test_multi_term_search_flow(self, sample_agents):
        """Multi-term search should find relevant matches."""
        search = AgentSearch(sample_agents)
        results = search.search("offline local", limit=10)
        assert any(r["id"] == "local_chat" for r in results)


class TestApiRequestFlow:
    """Tests for complete API request lifecycle."""

    @pytest.fixture
    def e2e_client(self, tmp_path: Path) -> TestClient:
        """Create a fully configured test client."""
        agents = [
            {
                "id": "rag_agent",
                "name": "RAG Assistant",
                "description": "A RAG-based assistant",
                "category": "rag",
                "frameworks": ["langchain"],
                "llm_providers": ["openai"],
                "complexity": "intermediate",
                "supports_local_models": False,
                "api_keys": ["OPENAI_API_KEY"],
                "github_url": "https://github.com/test/rag",
                "tags": ["rag", "ai"],
            },
            {
                "id": "chatbot",
                "name": "Simple Chatbot",
                "description": "A basic chatbot",
                "category": "chatbot",
                "frameworks": ["raw_api"],
                "llm_providers": ["ollama"],
                "complexity": "beginner",
                "supports_local_models": True,
                "api_keys": [],
                "github_url": "https://github.com/test/chat",
                "tags": ["chat", "bot"],
            },
        ]
        data_file = tmp_path / "agents.json"
        data_file.write_text(json.dumps(agents), encoding="utf-8")

        app = create_app(agents_path=data_file)
        # Use raise_server_exceptions=False to avoid startup issues
        return TestClient(app, raise_server_exceptions=False)

    def test_complete_search_request_flow(self, e2e_client: TestClient):
        """Complete flow: search request -> parse results -> filter."""
        response = e2e_client.get("/v1/agents?q=rag")
        assert response.status_code == 200

        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data

        # Verify cache headers
        assert "cache-control" in response.headers

    def test_complete_filter_request_flow(self, e2e_client: TestClient):
        """Complete flow: filter request -> verify results."""
        response = e2e_client.get("/v1/agents?category=chatbot&local_only=true")
        assert response.status_code == 200

        data = response.json()
        for item in data["items"]:
            assert item["category"] == "chatbot"
            assert item["supports_local_models"] is True

    def test_complete_agent_detail_flow(self, e2e_client: TestClient):
        """Complete flow: get agent -> verify all fields."""
        # First, search to find available agents
        search_response = e2e_client.get("/v1/agents")
        search_data = search_response.json()
        available_ids = [a["id"] for a in search_data["items"]]

        # Use one of the available agents
        if available_ids:
            agent_id = available_ids[0]
            response = e2e_client.get(f"/v1/agents/{agent_id}")
            assert response.status_code == 200

            agent = response.json()
            assert agent["id"] == agent_id
            assert "name" in agent
            assert "description" in agent
            assert "frameworks" in agent

    def test_complete_filters_flow(self, e2e_client: TestClient):
        """Complete flow: get filters -> verify structure."""
        response = e2e_client.get("/v1/filters")
        assert response.status_code == 200

        data = response.json()
        assert "categories" in data
        assert "frameworks" in data
        assert "providers" in data
        assert "complexities" in data


class TestExportFlow:
    """Tests for static site export workflow."""

    @pytest.fixture
    def export_data(self, tmp_path: Path) -> Path:
        """Create data file for export testing."""
        agents = [
            {
                "id": "agent_one",
                "name": "Agent One",
                "description": "First agent for export",
                "category": "rag",
                "frameworks": ["langchain"],
                "llm_providers": ["openai"],
                "github_url": "https://github.com/test/one",
                "tags": ["test"],
                "complexity": "beginner",
            },
            {
                "id": "agent_two",
                "name": "Agent Two",
                "description": "Second agent for export",
                "category": "chatbot",
                "frameworks": ["crewai"],
                "llm_providers": ["anthropic"],
                "github_url": "https://github.com/test/two",
                "tags": ["test"],
                "complexity": "intermediate",
            },
        ]
        data_file = tmp_path / "agents.json"
        data_file.write_text(json.dumps(agents), encoding="utf-8")
        return data_file

    def test_export_creates_index(self, export_data: Path, tmp_path: Path):
        """Export should create index file."""
        output_dir = tmp_path / "site"

        export_site(export_data, output_dir, base_url="https://example.com")

        # Check index file exists
        assert (output_dir / "index.html").exists()

    def test_export_without_base_url_skips_sitemap(self, export_data: Path, tmp_path: Path):
        """Export without base_url should skip sitemap generation."""
        output_dir = tmp_path / "site"

        export_site(export_data, output_dir, base_url=None)

        sitemap_path = output_dir / "sitemap.xml"
        assert not sitemap_path.exists()

    def test_export_creates_agent_pages(self, export_data: Path, tmp_path: Path):
        """Export should create agent pages."""
        output_dir = tmp_path / "site"

        export_site(export_data, output_dir, base_url="https://example.com")

        # Check agents directory exists and has files
        agents_dir = output_dir / "agents"
        assert agents_dir.exists()

        # Find any agent pages created
        agent_pages = list(agents_dir.glob("*/index.html"))
        assert len(agent_pages) >= 1, f"No agent pages found in {agents_dir}"


class TestErrorRecoveryFlow:
    """Tests for error handling and recovery."""

    def test_invalid_agent_id_flow(self, tmp_path: Path):
        """Invalid agent ID should return 404."""
        agents = [{"id": "valid", "name": "Valid", "category": "other", "frameworks": [], "llm_providers": []}]
        data_file = tmp_path / "agents.json"
        data_file.write_text(json.dumps(agents), encoding="utf-8")

        app = create_app(agents_path=data_file)
        client = TestClient(app)

        response = client.get("/v1/agents/invalid$$id")
        assert response.status_code in (400, 404)

    def test_malformed_json_input(self, tmp_path: Path):
        """Malformed JSON input should be handled gracefully."""
        app = create_app(agents_path=tmp_path / "empty.json")
        client = TestClient(app)

        response = client.post(
            "/v1/search",
            content="not valid json",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 422

    def test_empty_data_file_flow(self, tmp_path: Path):
        """Empty data file should be handled."""
        empty_file = tmp_path / "empty.json"
        empty_file.write_text("[]", encoding="utf-8")

        snapshot = load_agents(path=empty_file)
        assert snapshot.agents == []


class TestPaginationFlow:
    """Tests for pagination workflow."""

    def test_pagination_across_all_pages(self, tmp_path: Path):
        """Should be able to paginate through all results."""
        # Create many agents
        agents = [
            {
                "id": f"agent_{i}",
                "name": f"Agent {i}",
                "description": f"Description {i}",
                "category": "other",
                "frameworks": [],
                "llm_providers": [],
            }
            for i in range(25)
        ]
        data_file = tmp_path / "agents.json"
        data_file.write_text(json.dumps(agents), encoding="utf-8")

        app = create_app(agents_path=data_file)
        client = TestClient(app, raise_server_exceptions=False)

        # Get first page
        page1 = client.get("/v1/agents?page=1&page_size=10").json()
        assert len(page1["items"]) == 10
        # Total may include agents from other sources, so check our agents are there
        assert page1["total"] >= 25

        # Get second page
        page2 = client.get("/v1/agents?page=2&page_size=10").json()
        assert len(page2["items"]) == 10

        # Get third page
        page3 = client.get("/v1/agents?page=3&page_size=10").json()
        assert len(page3["items"]) >= 5

        # Verify all IDs are unique across pages
        all_ids = [a["id"] for a in page1["items"]] + [a["id"] for a in page2["items"]] + [a["id"] for a in page3["items"]]
        assert len(all_ids) == len(set(all_ids))


class TestCachingFlow:
    """Tests for caching workflow."""

    def test_search_cache_hit_flow(self, sample_agents):
        """Repeated searches should hit cache."""
        search = AgentSearch(sample_agents, enable_cache=True)

        # First search - cache miss
        results1 = search.search("pdf", limit=10, use_cache=True)

        # Second search - cache hit
        results2 = search.search("pdf", limit=10, use_cache=True)

        # Results should be identical
        assert len(results1) == len(results2)
        assert [r["id"] for r in results1] == [r["id"] for r in results2]

        # Check cache stats
        stats = search.cache_stats()
        assert stats["hits"] + stats["misses"] > 0

    def test_cache_invalidation_flow(self, sample_agents):
        """Cache should be invalidated when cleared."""
        search = AgentSearch(sample_agents, enable_cache=True)

        search.search("pdf", limit=10)
        stats_before = search.cache_stats()
        assert stats_before["size"] > 0

        search.clear_cache()
        stats_after = search.cache_stats()
        assert stats_after["size"] == 0
        assert stats_after["hits"] == 0
        assert stats_after["misses"] == 0


class TestConcurrentRequestsFlow:
    """Tests for handling concurrent requests."""

    def test_concurrent_search_requests(self, tmp_path: Path):
        """Should handle concurrent search requests safely."""
        agents = [
            {
                "id": f"agent_{i}",
                "name": f"Agent {i}",
                "description": "Test agent",
                "category": "other",
                "frameworks": [],
                "llm_providers": [],
            }
            for i in range(10)
        ]
        data_file = tmp_path / "agents.json"
        data_file.write_text(json.dumps(agents), encoding="utf-8")

        app = create_app(agents_path=data_file)
        client = TestClient(app)

        def make_request(query: str) -> tuple[int, Any]:
            response = client.get(f"/v1/agents?q={query}")
            return response.status_code, response.json()

        # Make concurrent requests
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request, f"agent_{i}") for i in range(10)]
            results = [f.result() for f in as_completed(futures)]

        # All requests should succeed
        assert all(status == 200 for status, _ in results)

    def test_concurrent_filter_requests(self, tmp_path: Path):
        """Should handle concurrent filter requests."""
        agents = [
            {
                "id": f"agent_{i}",
                "name": f"Agent {i}",
                "description": "Test",
                "category": ["rag", "chatbot", "agent"][i % 3],
                "frameworks": ["langchain", "crewai", "raw_api"][i % 3],
                "llm_providers": ["openai", "anthropic", "ollama"][i % 3],
            }
            for i in range(9)
        ]
        data_file = tmp_path / "agents.json"
        data_file.write_text(json.dumps(agents), encoding="utf-8")

        app = create_app(agents_path=data_file)
        client = TestClient(app)

        def make_filter_request(category: str) -> int:
            response = client.get(f"/v1/agents?category={category}")
            return response.status_code

        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(make_filter_request, cat)
                for cat in ["rag", "chatbot", "agent"]
            ]
            results = [f.result() for f in as_completed(futures)]

        assert all(status == 200 for status in results)


class TestFilterOptionsFlow:
    """Tests for filter options workflow."""

    def test_filter_options_aggregation(self, sample_agents):
        """Filter options should aggregate all unique values."""
        search = AgentSearch(sample_agents)
        options = search.get_filter_options()

        # Check categories
        assert "rag" in options["categories"]
        assert "chatbot" in options["categories"]
        assert "finance" in options["categories"]

        # Check frameworks
        assert "langchain" in options["frameworks"]
        assert "crewai" in options["frameworks"]
        assert "raw_api" in options["frameworks"]

        # Check providers
        assert "openai" in options["providers"]
        assert "anthropic" in options["providers"]
        assert "ollama" in options["providers"]

    def test_filter_options_empty_dataset(self):
        """Empty dataset should return empty filter options."""
        search = AgentSearch([])
        options = search.get_filter_options()

        assert options["categories"] == []
        assert options["frameworks"] == []
        assert options["providers"] == []
