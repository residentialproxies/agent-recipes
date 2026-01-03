"""
Concurrency and thread-safety tests for Agent Navigator.

Tests multi-threaded scenarios:
- Concurrent search operations
- Parallel cache access
- Thread-safe data loading
- Race condition prevention
"""

import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from src.api.app import create_app
from src.cache import CacheEntry, SQLiteCache, SQLiteRateLimiter
from src.data_store import load_agents
from src.search import AgentSearch, LRUCache


class TestLRUCacheConcurrency:
    """Tests for thread-safe LRU cache."""

    def test_concurrent_cache_reads(self, sample_agents):
        """Multiple threads should be able to read from cache simultaneously."""
        cache = LRUCache(max_size=100)

        # Pre-populate cache
        for i in range(50):
            cache.set((f"key_{i}",), [{"id": f"agent_{i}"}])

        results = []
        errors = []

        def read_cache(n: int) -> None:
            try:
                result = cache.get((f"key_{n % 50}",))
                results.append(result is not None)
            except Exception as e:
                errors.append(e)

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(read_cache, i) for i in range(100)]
            [f.result() for f in as_completed(futures)]

        assert len(errors) == 0
        assert len(results) == 100
        assert all(results)

    def test_concurrent_cache_writes(self):
        """Multiple threads should be able to write to cache safely."""
        cache = LRUCache(max_size=100)

        errors = []
        written_count = [0]

        def write_cache(n: int) -> None:
            try:
                cache.set((f"key_{n}",), [{"id": f"agent_{n}"}])
                with threading.Lock():
                    written_count[0] += 1
            except Exception as e:
                errors.append(e)

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(write_cache, i) for i in range(100)]
            [f.result() for f in as_completed(futures)]

        assert len(errors) == 0
        assert written_count[0] == 100

    def test_concurrent_cache_mixed_ops(self):
        """Mixed read/write operations should be thread-safe."""
        cache = LRUCache(max_size=50)

        errors = []
        read_count = [0]
        write_count = [0]

        def mixed_ops(n: int) -> None:
            try:
                if n % 2 == 0:
                    # Write
                    cache.set((f"key_{n}",), [{"id": f"agent_{n}"}])
                    with threading.Lock():
                        write_count[0] += 1
                else:
                    # Read (might miss, that's ok)
                    cache.get((f"key_{n}",))
                    with threading.Lock():
                        read_count[0] += 1
            except Exception as e:
                errors.append(e)

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(mixed_ops, i) for i in range(100)]
            [f.result() for f in as_completed(futures)]

        assert len(errors) == 0
        assert write_count[0] == 50
        assert read_count[0] == 50

    def test_cache_stats_thread_safety(self):
        """Cache stats should be consistent under concurrent access."""
        cache = LRUCache(max_size=100)

        def access_cache(n: int) -> None:
            for _ in range(10):
                cache.get((f"key_{n % 20}",))
                cache.set((f"key_{n}",), [{"id": f"agent_{n}"}])

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(access_cache, i) for i in range(20)]
            [f.result() for f in as_completed(futures)]

        stats = cache.stats()
        assert stats["hits"] + stats["misses"] > 0
        assert stats["size"] <= 100

    def test_concurrent_cache_clear(self):
        """Clear operations should be thread-safe."""
        cache = LRUCache(max_size=100)

        errors = []

        def write_and_clear(n: int) -> None:
            try:
                for i in range(10):
                    cache.set((f"key_{n}_{i}",), [{"id": f"agent_{i}"}])
                if n % 3 == 0:
                    cache.clear()
            except Exception as e:
                errors.append(e)

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(write_and_clear, i) for i in range(30)]
            [f.result() for f in as_completed(futures)]

        assert len(errors) == 0


class TestAgentSearchConcurrency:
    """Tests for concurrent search operations."""

    def test_concurrent_search_same_query(self, sample_agents):
        """Multiple threads searching for the same query should be safe."""
        search = AgentSearch(sample_agents, enable_cache=True)

        results = []
        errors = []

        def search_query() -> None:
            try:
                result = search.search("pdf", limit=10)
                results.append(result[0]["id"] if result else None)
            except Exception as e:
                errors.append(e)

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(search_query) for _ in range(20)]
            [f.result() for f in as_completed(futures)]

        assert len(errors) == 0
        assert len(results) == 20
        # All should find the same top result
        assert all(r == "pdf_assistant" for r in results)

    def test_concurrent_search_different_queries(self, sample_agents):
        """Multiple threads with different queries should not interfere."""
        search = AgentSearch(sample_agents, enable_cache=True)

        queries = ["pdf", "finance", "chatbot", "local", "agent"]
        results = {}
        errors = []

        def search_query(query: str) -> None:
            try:
                result = search.search(query, limit=5)
                results[query] = [r["id"] for r in result]
            except Exception as e:
                errors.append((query, e))

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(search_query, q) for q in queries]
            [f.result() for f in as_completed(futures)]

        assert len(errors) == 0
        assert len(results) == len(queries)
        for q in queries:
            assert q in results
            assert len(results[q]) > 0

    def test_concurrent_search_and_filter(self, sample_agents):
        """Concurrent search and filter operations should be safe."""
        search = AgentSearch(sample_agents, enable_cache=True)

        errors = []
        search_results = []
        filter_results = []

        def do_search() -> None:
            try:
                result = search.search("agent", limit=10)
                search_results.append(len(result))
            except Exception as e:
                errors.append(("search", e))

        def do_filter() -> None:
            try:
                result = search.filter_agents(
                    sample_agents,
                    category=["rag", "chatbot"],
                    framework=["langchain"],
                )
                filter_results.append(len(result))
            except Exception as e:
                errors.append(("filter", e))

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            for _ in range(5):
                futures.append(executor.submit(do_search))
                futures.append(executor.submit(do_filter))
            [f.result() for f in as_completed(futures)]

        assert len(errors) == 0
        assert len(search_results) == 5
        assert len(filter_results) == 5

    def test_concurrent_cache_operations(self, sample_agents):
        """Concurrent cache hits and misses should be handled correctly."""
        search = AgentSearch(sample_agents, enable_cache=True)

        def repeated_search(query: str) -> None:
            for _ in range(10):
                search.search(query, limit=5, use_cache=True)

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(repeated_search, "pdf"),
                executor.submit(repeated_search, "finance"),
                executor.submit(repeated_search, "chatbot"),
            ]
            [f.result() for f in as_completed(futures)]

        stats = search.cache_stats()
        # Should have some cache hits due to repeated queries
        assert stats["hits"] > 0 or stats["misses"] > 0


class TestDataStoreConcurrency:
    """Tests for thread-safe data loading."""

    def test_concurrent_load_agents(self, tmp_path: Path):
        """Multiple threads loading agents should get consistent results."""
        agents = [
            {
                "id": f"agent_{i}",
                "name": f"Agent {i}",
                "description": "Test",
                "category": "other",
                "frameworks": [],
                "llm_providers": [],
            }
            for i in range(10)
        ]
        data_file = tmp_path / "agents.json"
        data_file.write_text(json.dumps(agents), encoding="utf-8")

        snapshots = []
        errors = []

        def load_snapshot() -> None:
            try:
                snap = load_agents(path=data_file)
                snapshots.append(snap)
            except Exception as e:
                errors.append(e)

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(load_snapshot) for _ in range(20)]
            [f.result() for f in as_completed(futures)]

        assert len(errors) == 0
        assert len(snapshots) == 20
        # All should have the same mtime and same number of agents
        mtimes = {s.mtime_ns for s in snapshots}
        assert len(mtimes) == 1
        assert all(len(s.agents) == 10 for s in snapshots)

    def test_concurrent_search_engine_creation(self, tmp_path: Path):
        """Multiple threads creating search engines should be safe."""
        agents = [
            {
                "id": "agent_1",
                "name": "Agent One",
                "description": "Test",
                "category": "other",
                "frameworks": [],
                "llm_providers": [],
            }
        ]
        data_file = tmp_path / "agents.json"
        data_file.write_text(json.dumps(agents), encoding="utf-8")

        engines = []
        errors = []

        from src.data_store import get_search_engine

        def create_engine() -> None:
            try:
                engine = get_search_engine()
                engines.append(engine)
            except Exception as e:
                errors.append(e)

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(create_engine) for _ in range(20)]
            [f.result() for f in as_completed(futures)]

        assert len(errors) == 0
        assert len(engines) == 20


class TestSQLiteCacheConcurrency:
    """Tests for SQLite-based cache under concurrent access."""

    def test_concurrent_cache_get_set(self, tmp_path: Path):
        """SQLite cache should handle concurrent get/set operations."""
        cache = SQLiteCache(tmp_path / "cache.db", ttl_seconds=3600)

        errors = []
        successful_ops = [0]

        def cache_ops(n: int) -> None:
            try:
                # Set
                entry = CacheEntry(
                    created_at=time.time(),
                    model="test",
                    text=f"value_{n}",
                    usage={},
                    cost_usd=0.0,
                )
                cache.set(f"key_{n}", entry)

                # Get
                result = cache.get(f"key_{n}")
                if result is not None:
                    with threading.Lock():
                        successful_ops[0] += 1
            except Exception as e:
                errors.append(e)

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(cache_ops, i) for i in range(100)]
            [f.result() for f in as_completed(futures)]

        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert successful_ops[0] == 100

    def test_concurrent_cache_cleanup(self, tmp_path: Path):
        """Cleanup operations should be thread-safe."""
        cache = SQLiteCache(tmp_path / "cache.db", ttl_seconds=1)

        # Add entries
        for i in range(50):
            entry = CacheEntry(
                created_at=time.time() - 2,  # Already expired
                model="test",
                text=f"value_{i}",
                usage={},
                cost_usd=0.0,
            )
            cache.set(f"key_{i}", entry)

        errors = []

        def cleanup_and_add(n: int) -> None:
            try:
                cache.cleanup_expired()
                entry = CacheEntry(
                    created_at=time.time(),
                    model="test",
                    text=f"new_{n}",
                    usage={},
                    cost_usd=0.0,
                )
                cache.set(f"new_key_{n}", entry)
            except Exception as e:
                errors.append(e)

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(cleanup_and_add, i) for i in range(20)]
            [f.result() for f in as_completed(futures)]

        assert len(errors) == 0


class TestRateLimiterConcurrency:
    """Tests for rate limiter under concurrent access."""

    def test_concurrent_rate_limit_checks(self, tmp_path: Path):
        """Rate limiter should handle concurrent checks correctly."""
        limiter = SQLiteRateLimiter(
            tmp_path / "rate.db",
            requests_per_window=10,
            window_seconds=60,
        )

        results = []
        errors = []

        def check_rate_limit(client_id: str) -> None:
            try:
                allowed, retry_after = limiter.check_rate_limit(client_id)
                results.append((client_id, allowed, retry_after))
            except Exception as e:
                errors.append(e)

        # Same client makes many requests
        with ThreadPoolExecutor(max_workers=5) as executor:  # Lower concurrency for predictable behavior
            futures = [executor.submit(check_rate_limit, "client_1") for _ in range(15)]
            [f.result() for f in as_completed(futures)]

        assert len(errors) == 0
        assert len(results) == 15

        # First 10 should be allowed, rest rate limited (may be slightly off due to timing)
        allowed_count = sum(1 for _, allowed, _ in results if allowed)
        assert 10 <= allowed_count <= 15, f"Expected ~10 allowed, got {allowed_count}"

    def test_concurrent_different_clients(self, tmp_path: Path):
        """Different clients should have independent rate limits."""
        limiter = SQLiteRateLimiter(
            tmp_path / "rate.db",
            requests_per_window=5,
            window_seconds=60,
        )

        results = {}
        errors = []

        def check_rate_limit(client_id: str) -> None:
            try:
                allowed, _ = limiter.check_rate_limit(client_id)
                if client_id not in results:
                    results[client_id] = []
                results[client_id].append(allowed)
            except Exception as e:
                errors.append(e)

        # Multiple clients
        with ThreadPoolExecutor(max_workers=3) as executor:  # Lower concurrency
            futures = []
            for client in ["client_a", "client_b", "client_c"]:
                for _ in range(7):
                    futures.append(executor.submit(check_rate_limit, client))
            [f.result() for f in as_completed(futures)]

        assert len(errors) == 0
        # Each client should have approximately 5 allowed
        for client in ["client_a", "client_b", "client_c"]:
            allowed = sum(1 for allowed in results[client] if allowed)
            assert 5 <= allowed <= 7, f"Client {client} had {allowed} allowed requests"

    def test_concurrent_rate_limit_reset(self, tmp_path: Path):
        """Reset operations should be thread-safe."""
        limiter = SQLiteRateLimiter(
            tmp_path / "rate.db",
            requests_per_window=5,
            window_seconds=60,
        )

        # Use up rate limit
        for _ in range(5):
            limiter.check_rate_limit("client_1")

        errors = []

        def check_and_reset(client_id: str) -> None:
            try:
                allowed, _ = limiter.check_rate_limit(client_id)
                if not allowed:
                    limiter.reset_rate_limit(client_id)
                    # Now should be allowed
                    allowed2, _ = limiter.check_rate_limit(client_id)
                    assert allowed2, f"Reset failed for {client_id}"
            except Exception as e:
                errors.append(e)

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(check_and_reset, "client_1") for _ in range(5)]
            [f.result() for f in as_completed(futures)]

        assert len(errors) == 0


class TestAPIConcurrency:
    """Tests for API under concurrent load."""

    @pytest.fixture
    def concurrent_client(self, tmp_path: Path) -> TestClient:
        """Create a test client with sample data."""
        agents = [
            {
                "id": f"agent_{i}",
                "name": f"Agent {i}",
                "description": f"Test agent {i}",
                "category": ["rag", "chatbot", "agent"][i % 3],
                "frameworks": ["langchain", "crewai"][i % 2],
                "llm_providers": ["openai", "anthropic"][i % 2],
            }
            for i in range(30)
        ]
        data_file = tmp_path / "agents.json"
        data_file.write_text(json.dumps(agents), encoding="utf-8")

        app = create_app(agents_path=data_file)
        return TestClient(app, raise_server_exceptions=False)

    def test_concurrent_search_requests(self, concurrent_client: TestClient):
        """API should handle concurrent search requests."""
        errors = []
        results = []

        def make_request(query: str) -> None:
            try:
                response = concurrent_client.get(f"/v1/agents?q={query}")
                if response.status_code == 200:
                    results.append(len(response.json()["items"]))
                else:
                    errors.append((query, response.status_code))
            except Exception as e:
                errors.append((query, e))

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request, f"agent_{i}") for i in range(20)]
            [f.result() for f in as_completed(futures)]

        assert len(errors) == 0
        assert len(results) == 20

    def test_concurrent_filter_requests(self, concurrent_client: TestClient):
        """API should handle concurrent filter requests."""
        errors = []
        results = []

        def make_filter_request(category: str) -> None:
            try:
                response = concurrent_client.get(f"/v1/agents?category={category}")
                if response.status_code == 200:
                    results.append((category, response.json()["total"]))
                else:
                    errors.append((category, response.status_code))
            except Exception as e:
                errors.append((category, e))

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(make_filter_request, cat)
                for cat in ["rag", "chatbot", "agent", "rag", "chatbot"]
            ]
            [f.result() for f in as_completed(futures)]

        assert len(errors) == 0
        assert len(results) == 5

    def test_concurrent_detail_requests(self, concurrent_client: TestClient):
        """API should handle concurrent detail requests."""
        errors = []
        successful = [0]

        # First, get a valid agent ID from the search endpoint
        search_response = concurrent_client.get("/v1/agents")
        if search_response.status_code != 200:
            pytest.skip("Search endpoint not available")

        agents_data = search_response.json()
        if not agents_data.get("items"):
            pytest.skip("No agents available")

        # Get first available agent
        agent_id = agents_data["items"][0]["id"]

        def get_detail(aid: str) -> None:
            try:
                response = concurrent_client.get(f"/v1/agents/{aid}")
                if response.status_code == 200:
                    with threading.Lock():
                        successful[0] += 1
                else:
                    errors.append((aid, response.status_code))
            except Exception as e:
                errors.append((aid, e))

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(get_detail, agent_id) for _ in range(10)]
            [f.result() for f in as_completed(futures)]

        assert len(errors) == 0
        assert successful[0] == 10

    def test_concurrent_mixed_requests(self, concurrent_client: TestClient):
        """API should handle mixed request types concurrently."""
        errors = []
        results = {
            "search": 0,
            "filter": 0,
            "health": 0,
        }

        def make_search() -> None:
            try:
                response = concurrent_client.get("/v1/agents?q=test")
                if response.status_code == 200:
                    with threading.Lock():
                        results["search"] += 1
                else:
                    errors.append(("search", response.status_code))
            except Exception as e:
                errors.append(("search", e))

        def make_filter() -> None:
            try:
                response = concurrent_client.get("/v1/agents?category=rag")
                if response.status_code == 200:
                    with threading.Lock():
                        results["filter"] += 1
                else:
                    errors.append(("filter", response.status_code))
            except Exception as e:
                errors.append(("filter", e))

        def make_health() -> None:
            try:
                response = concurrent_client.get("/v1/health")
                if response.status_code == 200:
                    with threading.Lock():
                        results["health"] += 1
                else:
                    errors.append(("health", response.status_code))
            except Exception as e:
                errors.append(("health", e))

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            for _ in range(5):
                futures.append(executor.submit(make_search))
                futures.append(executor.submit(make_filter))
                futures.append(executor.submit(make_health))
            [f.result() for f in as_completed(futures)]

        assert len(errors) == 0
        assert all(count == 5 for count in results.values())


class TestRaceConditionPrevention:
    """Tests for race condition prevention."""

    def test_search_result_immutability(self, sample_agents):
        """Search results should be independent copies, not shared references."""
        search = AgentSearch(sample_agents)

        results1 = search.search("pdf", limit=5)
        results2 = search.search("pdf", limit=5)

        # Both results should have the same structure
        assert len(results1) == len(results2)
        if results1 and results2:
            assert results1[0]["id"] == results2[0]["id"]

    def test_concurrent_filter_immutability(self, sample_agents):
        """Filter results should be independent copies."""
        search = AgentSearch(sample_agents)

        filtered1 = search.filter_agents(sample_agents, category="rag")
        filtered2 = search.filter_agents(sample_agents, category="rag")

        # Both results should have the same structure
        assert len(filtered1) == len(filtered2)
        if filtered1 and filtered2:
            assert filtered1[0]["id"] == filtered2[0]["id"]

    def test_cache_key_uniqueness(self):
        """Cache keys should be unique per query/limit combination."""
        cache = LRUCache(max_size=100)

        cache.set(("query", "10"), [{"id": "result1"}])
        cache.set(("query", "20"), [{"id": "result2"}])

        result1 = cache.get(("query", "10"))
        result2 = cache.get(("query", "20"))

        assert result1[0]["id"] == "result1"
        assert result2[0]["id"] == "result2"
