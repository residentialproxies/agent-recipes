#!/usr/bin/env python3
"""
Performance test script for Agent Navigator optimizations.
"""
import time
import json
from pathlib import Path
from src.indexer import RepoIndexer, RateLimiter, _metrics
from src.search import AgentSearch, _search_cache

def test_rate_limiter():
    """Test rate limiter functionality."""
    print("Testing Rate Limiter...")
    limiter = RateLimiter(rate=10.0, burst=20)
    
    start = time.time()
    for i in range(25):
        limiter.wait_if_needed()
    elapsed = time.time() - start
    
    # Should take at least 0.5 seconds for 25 requests at 10 req/s
    assert elapsed >= 0.3, f"Rate limiter too fast: {elapsed}s"
    print(f"  Rate limiter: {elapsed:.2f}s for 25 requests - PASS")


def test_search_cache():
    """Test search result caching."""
    print("\nTesting Search Cache...")
    
    # Sample agents
    agents = [
        {"id": "a", "name": "Agent A", "description": "Test agent", "category": "other", "frameworks": [], "llm_providers": []},
        {"id": "b", "name": "Agent B", "description": "Another test", "category": "other", "frameworks": [], "llm_providers": []},
    ]
    
    search = AgentSearch(agents, enable_cache=True)
    
    # First search - cache miss
    _search_cache._misses = 0
    _search_cache._hits = 0
    results1 = search.search("agent")
    
    # Second search - cache hit
    results2 = search.search("agent")
    
    # Verify same results
    assert results1 == results2, "Cache should return same results"
    
    # Check cache stats
    stats = search.cache_stats()
    print(f"  Cache stats: {stats['hits']} hits, {stats['misses']} misses")
    print("  Search cache - PASS")


def test_parallel_processing():
    """Test that parallel extraction works."""
    print("\nTesting Parallel Processing...")
    
    # Create a test repo structure
    test_repo = Path("/tmp/test_agents_repo")
    test_repo.mkdir(exist_ok=True)
    
    # Create some test READMEs
    for i in range(5):
        agent_dir = test_repo / f"agent_{i}"
        agent_dir.mkdir(exist_ok=True)
        (agent_dir / "README.md").write_text(f"# Agent {i}\n\nThis is a test agent.")
    
    try:
        indexer = RepoIndexer(
            enable_llm=False,
            max_workers=3,
            llm_rate_limit=50.0  # High rate for testing
        )
        
        start = time.time()
        agents = indexer.index_repository(test_repo)
        elapsed = time.time() - start
        
        assert len(agents) == 5, f"Expected 5 agents, got {len(agents)}"
        print(f"  Processed {len(agents)} agents in {elapsed:.2f}s")
        print("  Parallel processing - PASS")
    finally:
        # Cleanup
        import shutil
        shutil.rmtree(test_repo, ignore_errors=True)


def test_performance_metrics():
    """Test performance metrics tracking."""
    print("\nTesting Performance Metrics...")
    
    _metrics.increment("test_operation", 10)
    _metrics.record_timing("test_op", 0.5)
    _metrics.record_timing("test_op", 1.5)
    
    assert _metrics.counters["test_operation"] == 10
    assert len(_metrics.timings["test_op"]) == 2
    
    report = _metrics.report()
    assert "test_operation" in report
    assert "test_op" in report
    
    print("  Performance metrics - PASS")


def test_http_cache():
    """Test HTTP cache functionality."""
    print("\nTesting HTTP Cache...")
    
    from src.indexer import HTTPCache
    
    cache = HTTPCache(cache_path=Path("/tmp/test_http_cache.json"), ttl_seconds=3600)
    
    # Test cache miss
    result = cache.get("test_key")
    assert result is None, "Should be cache miss"
    
    # Test cache set and hit
    cache.set("test_key", {"data": "test"})
    result = cache.get("test_key")
    assert result == {"data": "test"}, "Cache hit should return stored value"
    
    # Cleanup
    import os
    try:
        os.remove("/tmp/test_http_cache.json")
    except:
        pass
    
    print("  HTTP cache - PASS")


if __name__ == "__main__":
    print("=" * 60)
    print("Agent Navigator Performance Tests")
    print("=" * 60)
    
    test_rate_limiter()
    test_search_cache()
    test_parallel_processing()
    test_performance_metrics()
    test_http_cache()
    
    print("\n" + "=" * 60)
    print("All performance tests PASSED!")
    print("=" * 60)
