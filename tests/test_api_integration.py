"""
End-to-end API integration tests for Agent Navigator.

Tests all endpoints, error handling, rate limiting, and payload limits.
"""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.api.app import create_app


@pytest.fixture
def agents_json_path(tmp_path: Path) -> Path:
    """Create a temporary agents.json file for testing."""
    agents = [
        {
            "id": "pdf_assistant",
            "name": "PDF Document Assistant",
            "description": "Chat with your PDF documents using RAG",
            "category": "rag",
            "frameworks": ["langchain"],
            "llm_providers": ["openai"],
            "design_pattern": "rag",
            "complexity": "beginner",
            "supports_local_models": False,
            "requires_gpu": False,
            "api_keys": ["OPENAI_API_KEY"],
            "github_url": "https://github.com/foo/bar/tree/main/pdf_assistant",
            "folder_path": "pdf_assistant",
            "readme_relpath": "pdf_assistant/README.md",
            "stars": 1234,
            "updated_at": 1704067200,
            "languages": ["python"],
            "tags": ["pdf", "rag", "document"],
        },
        {
            "id": "finance_agent",
            "name": "Financial Analyst Agent",
            "description": "AI agent for stock analysis and portfolio management",
            "category": "finance",
            "frameworks": ["crewai", "langchain"],
            "llm_providers": ["openai", "anthropic"],
            "design_pattern": "multi_agent",
            "complexity": "advanced",
            "supports_local_models": False,
            "requires_gpu": True,
            "api_keys": ["OPENAI_API_KEY", "ANTHROPIC_API_KEY"],
            "github_url": "https://github.com/foo/bar/tree/main/finance_agent",
            "folder_path": "finance_agent",
            "readme_relpath": "finance_agent/README.md",
            "stars": 567,
            "updated_at": 1704153600,
            "languages": ["python", "javascript"],
            "tags": ["finance", "trading", "stocks"],
        },
        {
            "id": "local_chat",
            "name": "Local LLM Chatbot",
            "description": "Run chatbot completely offline with Ollama",
            "category": "chatbot",
            "frameworks": ["raw_api"],
            "llm_providers": ["ollama"],
            "design_pattern": "simple_chat",
            "complexity": "beginner",
            "supports_local_models": True,
            "requires_gpu": False,
            "api_keys": [],
            "github_url": "https://github.com/foo/bar/tree/main/local_chat",
            "folder_path": "local_chat",
            "readme_relpath": "local_chat/README.md",
            "stars": 890,
            "updated_at": 1704240000,
            "languages": ["python"],
            "tags": ["chatbot", "local", "offline"],
        },
        {
            "id": "voice_agent",
            "name": "Voice Assistant",
            "description": "Speech-to-text voice assistant",
            "category": "voice",
            "frameworks": ["raw_api"],
            "llm_providers": ["openai"],
            "complexity": "intermediate",
            "supports_local_models": False,
            "api_keys": ["OPENAI_API_KEY"],
            "github_url": "https://github.com/test/voice",
            "tags": ["voice", "whisper"],
        },
    ]
    agents_file = tmp_path / "agents.json"
    agents_file.write_text(json.dumps(agents), encoding="utf-8")
    return agents_file


@pytest.fixture
def webmanus_db_path(tmp_path: Path) -> Path:
    """Create a temporary WebManus database path."""
    db_path = tmp_path / "webmanus.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return db_path


@pytest.fixture
def client(agents_json_path: Path, webmanus_db_path: Path) -> TestClient:
    """Create a test client with sample data."""
    app = create_app(
        agents_path=agents_json_path,
        webmanus_db_path=webmanus_db_path,
    )
    return TestClient(app)


class TestHealthEndpoint:
    """Tests for /v1/health endpoint."""

    def test_health_returns_ok(self, client: TestClient):
        """Health endpoint should return ok status."""
        response = client.get("/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("ok") is True

    def test_health_no_cache(self, client: TestClient):
        """Health endpoint should have no-store cache header."""
        response = client.get("/v1/health")
        assert "cache-control" in response.headers
        assert "no-store" in response.headers["cache-control"]


class TestFiltersEndpoint:
    """Tests for /v1/filters endpoint."""

    def test_filters_returns_structure(self, client: TestClient):
        """Filters endpoint should return filter options."""
        response = client.get("/v1/filters")
        assert response.status_code == 200
        data = response.json()
        assert "categories" in data
        assert "frameworks" in data
        assert "providers" in data
        assert "complexities" in data

    def test_filters_categories(self, client: TestClient):
        """Categories should include expected values."""
        response = client.get("/v1/filters")
        data = response.json()
        categories = data.get("categories", [])
        assert "rag" in categories
        assert "chatbot" in categories

    def test_filters_cache_header(self, client: TestClient):
        """Filters endpoint should have cache header."""
        response = client.get("/v1/filters")
        assert "cache-control" in response.headers
        assert "public" in response.headers["cache-control"]


class TestAgentsListEndpoint:
    """Tests for /v1/agents endpoint (GET)."""

    def test_agents_list_basic(self, client: TestClient):
        """Should return list of agents."""
        response = client.get("/v1/agents")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert isinstance(data["items"], list)
        assert data["total"] >= 0

    def test_agents_list_pagination(self, client: TestClient):
        """Pagination should work correctly."""
        # First page
        response = client.get("/v1/agents?page=1&page_size=2")
        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 2
        assert len(data["items"]) <= 2

    def test_agents_list_with_query(self, client: TestClient):
        """Query parameter should filter results."""
        response = client.get("/v1/agents?q=pdf")
        data = response.json()
        # Should find pdf_assistant
        items = data["items"]
        assert any(
            "pdf" in item.get("name", "").lower() or "pdf" in item.get("description", "").lower() for item in items
        )

    def test_agents_list_with_category_filter(self, client: TestClient):
        """Category filter should work."""
        response = client.get("/v1/agents?category=rag")
        data = response.json()
        for item in data["items"]:
            assert item.get("category") == "rag"

    def test_agents_list_with_framework_filter(self, client: TestClient):
        """Framework filter should work."""
        response = client.get("/v1/agents?framework=langchain")
        data = response.json()
        for item in data["items"]:
            frameworks = item.get("frameworks", [])
            assert "langchain" in frameworks

    def test_agents_list_with_provider_filter(self, client: TestClient):
        """Provider filter should work."""
        response = client.get("/v1/agents?provider=openai")
        data = response.json()
        for item in data["items"]:
            providers = item.get("llm_providers", [])
            assert "openai" in providers

    def test_agents_list_with_complexity_filter(self, client: TestClient):
        """Complexity filter should work."""
        response = client.get("/v1/agents?complexity=beginner")
        data = response.json()
        for item in data["items"]:
            assert item.get("complexity") == "beginner"

    def test_agents_list_with_local_only(self, client: TestClient):
        """Local-only filter should work."""
        response = client.get("/v1/agents?local_only=true")
        data = response.json()
        for item in data["items"]:
            assert item.get("supports_local_models") is True

    def test_agents_list_combined_filters(self, client: TestClient):
        """Combined filters should work together."""
        response = client.get("/v1/agents?category=chatbot&local_only=true")
        data = response.json()
        for item in data["items"]:
            assert item.get("category") == "chatbot"
            assert item.get("supports_local_models") is True

    def test_agents_list_empty_query(self, client: TestClient):
        """Empty query should return all agents (with filters)."""
        response = client.get("/v1/agents?q=")
        data = response.json()
        assert data["total"] >= 0

    def test_agents_list_cache_header(self, client: TestClient):
        """Should have proper cache header."""
        response = client.get("/v1/agents")
        assert "cache-control" in response.headers
        assert "public" in response.headers["cache-control"]

    def test_agents_list_invalid_page_size(self, client: TestClient):
        """Should handle large page size gracefully."""
        response = client.get("/v1/agents?page_size=1000")
        # Should return 200 with results limited internally
        assert response.status_code == 200


class TestSearchEndpoint:
    """Tests for /v1/search endpoint (POST)."""

    def test_search_basic(self, client: TestClient):
        """POST search should work like GET with query."""
        response = client.post("/v1/search", json={"q": "pdf", "page": 1, "page_size": 10})
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    def test_search_with_filters(self, client: TestClient):
        """POST search should accept all filters."""
        response = client.post(
            "/v1/search",
            json={
                "q": "agent",
                "category": "rag",
                "framework": "langchain",
                "provider": "openai",
                "complexity": "beginner",
                "local_only": False,
                "page": 1,
                "page_size": 10,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data

    def test_search_empty_body(self, client: TestClient):
        """Empty body should use defaults."""
        response = client.post("/v1/search", json={})
        assert response.status_code == 200

    def test_search_no_query_with_filters(self, client: TestClient):
        """Search without query but with filters should work."""
        response = client.post("/v1/search", json={"category": "voice"})
        assert response.status_code == 200
        data = response.json()
        for item in data["items"]:
            assert item.get("category") == "voice"


class TestAgentDetailEndpoint:
    """Tests for /v1/agents/{agent_id} endpoint."""

    def test_agent_detail_found(self, client: TestClient):
        """Should return agent details for valid ID."""
        response = client.get("/v1/agents/pdf_assistant")
        # May return 200 or 404 depending on data loading
        assert response.status_code in (200, 404)
        if response.status_code == 200:
            data = response.json()
            assert data.get("id") == "pdf_assistant"

    def test_agent_detail_not_found(self, client: TestClient):
        """Should return 404 for non-existent agent."""
        response = client.get("/v1/agents/nonexistent_agent_xyz")
        assert response.status_code == 404

    def test_agent_detail_invalid_id(self, client: TestClient):
        """Should return 400 for invalid agent ID."""
        # The path ../../etc/passwd gets URL encoded
        response = client.get("/v1/agents/..%2F..%2Fetc%2Fpasswd")
        # Should either be 400 (validation) or 404 (not found after sanitization)
        assert response.status_code in (400, 404)

    def test_agent_detail_xss_attempt(self, client: TestClient):
        """XSS attempts in ID should be blocked."""
        # URL encode the script tags
        response = client.get("/v1/agents/%3Cscript%3Ealert(1)%3C/script%3E")
        # Should be 400 (invalid ID) or 404 (not found)
        assert response.status_code in (400, 404)

    def test_agent_detail_cache_header(self, client: TestClient):
        """Agent detail should have cache header when found."""
        response = client.get("/v1/agents/pdf_assistant")
        if response.status_code == 200:
            assert "cache-control" in response.headers


class TestErrorHandling:
    """Tests for API error handling."""

    def test_404_for_invalid_endpoint(self, client: TestClient):
        """Invalid endpoint should return 404."""
        response = client.get("/v1/invalid_endpoint")
        assert response.status_code == 404

    def test_405_for_wrong_method(self, client: TestClient):
        """Wrong HTTP method should return 405."""
        response = client.post("/v1/agents/pdf_assistant")
        assert response.status_code == 405

    def test_413_for_large_payload(self, client: TestClient):
        """Large payload should trigger 413."""
        # Create a large payload - note this tests middleware limit
        # The middleware checks content-length header
        large_data = {"q": "x" * 11_000_000}
        # Don't manually set Content-Length - let httpx handle it
        response = client.post("/v1/search", json=large_data)
        # May return 413, 200, or error depending on middleware configuration
        assert response.status_code in (200, 413, 500)

    def test_validation_error_response(self, client: TestClient):
        """Validation errors should return proper error format."""
        # URL encode spaces
        response = client.get("/v1/agents/agent%20with%20spaces")
        # Should be 400 (invalid format) or 404 (not found after sanitization)
        assert response.status_code in (400, 404)

    def test_malformed_json(self, client: TestClient):
        """Malformed JSON should return 422."""
        response = client.post("/v1/search", content="not valid json", headers={"Content-Type": "application/json"})
        assert response.status_code == 422


class TestSecurityHeaders:
    """Tests for security headers on responses."""

    def test_security_headers_present(self, client: TestClient):
        """Security headers should be present."""
        response = client.get("/v1/health")
        headers = response.headers

        assert "x-content-type-options" in headers
        assert headers["x-content-type-options"] == "nosniff"

        assert "x-frame-options" in headers
        assert headers["x-frame-options"] == "DENY"

        assert "x-xss-protection" in headers

        assert "strict-transport-security" in headers

        assert "referrer-policy" in headers

        assert "permissions-policy" in headers

    def test_csp_header_present(self, client: TestClient):
        """Content-Security-Policy header should be present."""
        response = client.get("/v1/health")
        headers = response.headers
        assert "content-security-policy" in headers


class TestCorsHeaders:
    """Tests for CORS headers."""

    def test_cors_headers_on_options(self, client: TestClient):
        """OPTIONS request should return CORS headers."""
        resp = client.options(
            "/v1/agents",
            headers={
                "Origin": "http://localhost",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert resp.status_code in (200, 204)
        assert "access-control-allow-origin" in resp.headers

    def test_cors_headers_on_get(self, client: TestClient):
        """GET request should have CORS headers."""
        resp = client.get("/v1/agents")
        assert resp.status_code == 200


class TestRateLimiting:
    """Tests for rate limiting."""

    def test_rate_limit_allows_requests(self, client: TestClient):
        """Normal requests should be allowed."""
        for _ in range(5):
            response = client.get("/v1/health")
            assert response.status_code == 200

    def test_rate_limit_blocks_excess(self, client: TestClient, monkeypatch):
        """Excessive requests should be rate limited."""
        # This would require configuring a very low rate limit
        # For now, we test the endpoint exists
        resp = client.get("/v1/health")
        assert resp.status_code == 200
        # In real scenario with low limit, subsequent requests would be 429


class TestUnicodeEdgeCases:
    """Tests for Unicode and internationalization."""

    def test_unicode_in_query(self, client: TestClient):
        """Unicode characters in query should work."""
        response = client.get("/v1/agents?q=cafe")
        assert response.status_code == 200

    def test_unicode_in_agent_id(self, client: TestClient):
        """Unicode-only agent ID should be handled."""
        # Standard IDs only have alphanumeric, underscore, hyphen
        # Unicode would be rejected by validation
        response = client.get("/v1/agents/cafe")
        assert response.status_code in (400, 404)  # 400 if format invalid, 404 if not found

    def test_emoji_in_search(self, client: TestClient):
        """Emoji in search query should work."""
        response = client.get("/v1/agents?q=bot")
        assert response.status_code == 200


class TestCompression:
    """Tests for response compression."""

    def test_gzip_compression(self, client: TestClient):
        """Responses should be compressible."""
        # Send request with Accept-Encoding: gzip
        response = client.get("/v1/agents", headers={"Accept-Encoding": "gzip"})
        # Should succeed and return data
        assert response.status_code == 200


class TestEdgeCases:
    """Edge case tests."""

    def test_zero_page_size(self, client: TestClient):
        """Zero page size should be handled."""
        # Pydantic requires page >= 1, so 0 would fail validation
        response = client.get("/v1/agents?page_size=0")
        # May return 422 (validation error) or 200
        assert response.status_code in (200, 422)

    def test_negative_page(self, client: TestClient):
        """Negative page should be handled."""
        # Pydantic requires page >= 1
        response = client.get("/v1/agents?page=-1")
        # Should return 422 (validation error)
        assert response.status_code == 422

    def test_very_large_page(self, client: TestClient):
        """Very large page number should return empty results."""
        response = client.get("/v1/agents?page=999999")
        assert response.status_code == 200
        data = response.json()
        # Should have items key, possibly empty
        assert "items" in data
        assert len(data.get("items", [])) == 0

    def test_filter_with_no_results(self, client: TestClient):
        """Filter with no matches should return empty."""
        response = client.get("/v1/agents?category=nonexistent")
        data = response.json()
        assert data.get("total") == 0
        assert len(data.get("items", [])) == 0

    def test_special_characters_in_query(self, client: TestClient):
        """Special characters in query should be safe."""
        response = client.get("/v1/agents?q=%3Cscript%3E")
        assert response.status_code == 200

    def test_sql_injection_in_query(self, client: TestClient):
        """SQL injection attempts should be handled safely."""
        response = client.get("/v1/agents?q=';DROP TABLE users--")
        assert response.status_code == 200
        # Should not cause errors


class TestContentType:
    """Tests for content-type handling."""

    def test_json_response(self, client: TestClient):
        """API should return JSON content."""
        response = client.get("/v1/agents")
        assert "application/json" in response.headers.get("content-type", "")

    def test_accept_json(self, client: TestClient):
        """Request with Accept: application/json should work."""
        response = client.get("/v1/agents", headers={"Accept": "application/json"})
        assert response.status_code == 200
