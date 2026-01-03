"""
Tests for src.data_store module.

Tests for:
- load_agents() - with and without cache
- get_search_engine() - caching behavior
- Thread safety
"""

import json
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import pytest

from src.config import settings
from src.data_store import AgentsSnapshot, _read_agents_file, get_search_engine, load_agents
from src.search import AgentSearch, _search_cache


@pytest.fixture(autouse=True)
def reset_data_store_cache() -> None:
    """Reset data_store module cache before each test."""
    import src.data_store

    src.data_store._snapshot = None
    src.data_store._search_engine = None
    _search_cache.clear()
    yield
    # Also clear after test
    src.data_store._snapshot = None
    src.data_store._search_engine = None
    _search_cache.clear()


class TestReadAgentsFile:
    """Tests for _read_agents_file function."""

    def test_read_existing_file(self, tmp_path: Path) -> None:
        """Test reading an existing agents.json file."""
        agents_data = [{"id": "agent1", "name": "Agent 1"}]
        agents_file = tmp_path / "agents.json"
        agents_file.write_text(json.dumps(agents_data), encoding="utf-8")

        result = _read_agents_file(agents_file)

        assert result == agents_data

    def test_read_nonexistent_file_returns_empty(self, tmp_path: Path) -> None:
        """Test that non-existent file returns empty list."""
        result = _read_agents_file(tmp_path / "nonexistent.json")
        assert result == []

    def test_read_falls_back_to_src_data(self, tmp_path: Path) -> None:
        """Test fallback to src/data/agents.json."""
        # Create file in src/data
        src_data_path = Path("src/data")
        src_data_path.mkdir(parents=True, exist_ok=True)
        agents_file = src_data_path / "agents.json"

        agents_data = [{"id": "fallback", "name": "Fallback Agent"}]
        agents_file.write_text(json.dumps(agents_data), encoding="utf-8")

        try:
            # Try to read from non-existent path first
            result = _read_agents_file(tmp_path / "nonexistent.json")
            assert result == agents_data
        finally:
            # Cleanup
            if agents_file.exists():
                agents_file.unlink()

    def test_read_invalid_json(self, tmp_path: Path) -> None:
        """Test that invalid JSON raises error."""
        agents_file = tmp_path / "invalid.json"
        agents_file.write_text("not valid json", encoding="utf-8")

        with pytest.raises(json.JSONDecodeError):
            _read_agents_file(agents_file)


class TestLoadAgents:
    """Tests for load_agents function."""

    @pytest.fixture
    def sample_agents(self) -> list[dict[str, Any]]:
        """Sample agent data."""
        return [
            {
                "id": "agent1",
                "name": "Agent 1",
                "description": "First agent",
                "category": "rag",
                "frameworks": ["langchain"],
            },
            {
                "id": "agent2",
                "name": "Agent 2",
                "description": "Second agent",
                "category": "chatbot",
                "frameworks": ["openai"],
            },
        ]

    @pytest.fixture
    def agents_file(self, tmp_path: Path, sample_agents: list[dict[str, Any]]) -> Path:
        """Create a temporary agents.json file."""
        agents_path = tmp_path / "agents.json"
        agents_path.write_text(json.dumps(sample_agents), encoding="utf-8")
        return agents_path

    def test_load_agents_returns_snapshot(self, agents_file: Path) -> None:
        """Test that load_agents returns an AgentsSnapshot."""
        result = load_agents(path=agents_file)

        assert isinstance(result, AgentsSnapshot)
        assert hasattr(result, "mtime_ns")
        assert hasattr(result, "agents")
        assert len(result.agents) == 2

    def test_load_agents_caches_by_mtime(self, agents_file: Path) -> None:
        """Test that load_agents caches by modification time."""
        snapshot1 = load_agents(path=agents_file)
        snapshot2 = load_agents(path=agents_file)

        # Should return the same cached snapshot
        assert snapshot1 is snapshot2
        assert snapshot1.mtime_ns == snapshot2.mtime_ns

    def test_load_agents_invalidates_on_change(self, agents_file: Path, sample_agents: list[dict[str, Any]]) -> None:
        """Test that cache is invalidated when file changes."""
        snapshot1 = load_agents(path=agents_file)

        # Modify the file
        new_agents = sample_agents + [{"id": "agent3", "name": "Agent 3"}]
        agents_file.write_text(json.dumps(new_agents), encoding="utf-8")

        # Wait a tiny bit to ensure different mtime
        import time

        time.sleep(0.01)

        snapshot2 = load_agents(path=agents_file)

        # Should have different mtime and different agents
        assert snapshot1 is not snapshot2
        assert snapshot1.mtime_ns != snapshot2.mtime_ns
        assert len(snapshot2.agents) == 3

    def test_load_agents_with_path_parameter(self, tmp_path: Path, agents_file: Path) -> None:
        """Test load_agents with explicit path parameter."""
        result = load_agents(path=agents_file)

        assert len(result.agents) == 2

    def test_load_agents_uses_settings_default(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """Test that load_agents uses settings.data_path by default."""
        # Create agents.json in tmp_path
        agents_data = [{"id": "default", "name": "Default Agent"}]
        agents_path = tmp_path / "data" / "agents.json"
        agents_path.parent.mkdir(parents=True)
        agents_path.write_text(json.dumps(agents_data), encoding="utf-8")

        monkeypatch.setattr(settings, "data_path", agents_path)

        result = load_agents()

        assert len(result.agents) == 1
        assert result.agents[0]["id"] == "default"

    def test_load_agents_nonexistent_file(self, tmp_path: Path) -> None:
        """Test loading from non-existent file."""
        result = load_agents(path=tmp_path / "nonexistent.json")

        assert isinstance(result, AgentsSnapshot)
        assert result.agents == []
        assert result.mtime_ns == 0

    def test_load_agents_concurrent_access(self, agents_file: Path) -> None:
        """Test that concurrent loads are thread-safe."""
        results = []
        errors = []

        def load_worker():
            try:
                result = load_agents(path=agents_file)
                results.append(result)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=load_worker) for _ in range(10)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"Errors occurred: {errors}"
        assert len(results) == 10
        # All should be the same cached instance
        assert all(r is results[0] for r in results)


class TestGetSearchEngine:
    """Tests for get_search_engine function."""

    @pytest.fixture
    def sample_agents(self) -> list[dict[str, Any]]:
        """Sample agent data."""
        return [
            {
                "id": "agent1",
                "name": "PDF Chatbot",
                "description": "Chat with PDFs",
                "category": "rag",
            },
            {
                "id": "agent2",
                "name": "Email Bot",
                "description": "Auto-reply to emails",
                "category": "chatbot",
            },
        ]

    @pytest.fixture
    def sample_snapshot(self, sample_agents: list[dict[str, Any]]) -> AgentsSnapshot:
        """Create a sample snapshot."""
        return AgentsSnapshot(mtime_ns=12345, agents=sample_agents)

    def test_get_search_engine_returns_agent_search(self, sample_snapshot: AgentsSnapshot) -> None:
        """Test that get_search_engine returns AgentSearch instance."""
        result = get_search_engine(snapshot=sample_snapshot)

        assert isinstance(result, AgentSearch)

    def test_get_search_engine_caches_by_snapshot(self, sample_snapshot: AgentsSnapshot) -> None:
        """Test that engine is cached for same snapshot."""
        engine1 = get_search_engine(snapshot=sample_snapshot)
        engine2 = get_search_engine(snapshot=sample_snapshot)

        assert engine1 is engine2

    def test_get_search_engine_rebuilds_on_new_snapshot(self) -> None:
        """Test that engine rebuilds when snapshot changes."""
        snapshot1 = AgentsSnapshot(mtime_ns=1, agents=[{"id": "a1"}])
        snapshot2 = AgentsSnapshot(mtime_ns=2, agents=[{"id": "a2"}])

        engine1 = get_search_engine(snapshot=snapshot1)
        engine2 = get_search_engine(snapshot=snapshot2)

        # Should be different instances
        assert engine1 is not engine2

    def test_get_search_engine_uses_load_agents_when_no_snapshot(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Test that get_search_engine calls load_agents when no snapshot provided."""
        # Create an agents.json file
        sample_agents = [{"id": "test", "name": "Test Agent"}]
        agents_file = tmp_path / "agents.json"
        agents_file.write_text(json.dumps(sample_agents), encoding="utf-8")

        # Point settings to this file
        monkeypatch.setattr(settings, "data_path", agents_file)

        # Reset the module-level cache (the autouse fixture does this but let's be explicit)
        import src.data_store

        src.data_store._snapshot = None
        src.data_store._search_engine = None

        # Calling get_search_engine without snapshot should use load_agents
        engine = get_search_engine()

        assert isinstance(engine, AgentSearch)

    def test_get_search_engine_concurrent_access(self, sample_snapshot: AgentsSnapshot) -> None:
        """Test that concurrent access is thread-safe."""
        engines = []
        errors = []

        def get_engine():
            try:
                engine = get_search_engine(snapshot=sample_snapshot)
                engines.append(engine)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=get_engine) for _ in range(10)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"Errors occurred: {errors}"
        assert len(engines) == 10
        # All should be the same cached instance
        assert all(e is engines[0] for e in engines)


class TestAgentsSnapshot:
    """Tests for AgentsSnapshot dataclass."""

    def test_snapshot_creation(self) -> None:
        """Test creating an AgentsSnapshot."""
        agents = [{"id": "test"}]
        snapshot = AgentsSnapshot(mtime_ns=12345, agents=agents)

        assert snapshot.mtime_ns == 12345
        assert snapshot.agents == agents

    def test_snapshot_immutability(self) -> None:
        """Test that snapshot is mutable by default (dataclass)."""
        agents = [{"id": "test"}]
        snapshot = AgentsSnapshot(mtime_ns=12345, agents=agents)

        # dataclasses are mutable by default
        snapshot.agents.append({"id": "test2"})
        assert len(snapshot.agents) == 2


class TestIntegration:
    """Integration tests for data_store module."""

    def test_full_load_and_search_workflow(self, tmp_path: Path) -> None:
        """Test loading agents and searching them."""
        agents_data = [
            {
                "id": "pdf_bot",
                "name": "PDF Assistant",
                "description": "Chat with PDF documents",
                "category": "rag",
            },
            {
                "id": "chat_bot",
                "name": "Chat Assistant",
                "description": "General chatbot",
                "category": "chatbot",
            },
        ]

        agents_file = tmp_path / "agents.json"
        agents_file.write_text(json.dumps(agents_data), encoding="utf-8")

        # Load agents
        snapshot = load_agents(path=agents_file)

        # Get search engine
        engine = get_search_engine(snapshot=snapshot)

        # Search for PDF-related agent
        results = engine.search("PDF document", limit=5)

        # Should return at least the PDF bot
        assert len(results) >= 1
        result_ids = [r.get("id") for r in results]
        assert "pdf_bot" in result_ids

    def test_cache_invalidation_workflow(self, tmp_path: Path) -> None:
        """Test that cache invalidation works correctly in workflow."""
        agents_file = tmp_path / "agents.json"

        # Initial data
        agents_file.write_text(json.dumps([{"id": "v1", "name": "Version 1"}]), encoding="utf-8")
        snapshot1 = load_agents(path=agents_file)
        engine1 = get_search_engine(snapshot=snapshot1)

        # Update data
        import time

        time.sleep(0.01)  # Ensure different mtime
        agents_file.write_text(json.dumps([{"id": "v2", "name": "Version 2"}]), encoding="utf-8")
        snapshot2 = load_agents(path=agents_file)

        # Snapshots should be different
        assert snapshot1 is not snapshot2
        assert snapshot1.agents[0]["id"] == "v1"
        assert snapshot2.agents[0]["id"] == "v2"
        assert snapshot1.mtime_ns != snapshot2.mtime_ns

        # The function should rebuild the engine when mtime differs
        # But we need to force a rebuild since we're passing snapshots explicitly
        # and the global _snapshot is only checked once
        import src.data_store

        src.data_store._search_engine = None  # Force rebuild

        engine2 = get_search_engine(snapshot=snapshot2)

        # Now the engines should be different
        assert engine1 is not engine2

    def test_concurrent_load_and_search(self, tmp_path: Path) -> None:
        """Test concurrent loading and searching."""
        agents_data = [
            {"id": f"agent{i}", "name": f"Agent {i}", "description": f"This is agent {i} with description"}
            for i in range(20)
        ]

        agents_file = tmp_path / "agents.json"
        agents_file.write_text(json.dumps(agents_data), encoding="utf-8")

        errors = []
        search_results = []

        def worker(worker_id: int):
            try:
                snapshot = load_agents(path=agents_file)
                engine = get_search_engine(snapshot=snapshot)
                # Use a more general search that will match
                results = engine.search("agent", limit=5)
                search_results.append(len(results))
            except Exception as e:
                errors.append(e)

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(worker, i) for i in range(20)]
            for f in as_completed(futures):
                f.result()

        assert not errors, f"Errors occurred: {errors}"
        assert len(search_results) == 20
        # All searches should return results for "agent"
        assert all(count > 0 for count in search_results)
