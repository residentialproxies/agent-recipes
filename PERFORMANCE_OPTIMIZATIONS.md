# Agent Navigator Performance Optimizations

## Overview

This document describes the performance optimizations applied to the Agent Navigator indexer and search components.

## Performance Improvements

### Before Optimization

- Sequential LLM processing: ~5 minutes for 120 agents
- Scalability ceiling at ~500 agents
- Single-threaded LLM calls
- No HTTP caching
- No search result caching

### After Optimization (Target)

- Parallel LLM processing: <45 seconds for 120 agents (10-15x speedup)
- Scalability up to 2000+ agents
- Multi-threaded LLM calls with rate limiting
- HTTP caching with TTL
- Search result LRU caching

---

## 1. Parallel LLM Processing (`src/indexer.py`)

### Key Changes

#### ThreadPoolExecutor for Parallel Processing

- `max_workers` parameter (default: 20)
- Batch processing (100 agents per batch)
- Thread-safe cache access with locks

```python
with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
    futures = {
        executor.submit(self.extract_agent, readme, repo_root): (readme, repo_root)
        for readme, repo_root in uncached_iter
    }
```

#### Rate Limiting

- Token bucket algorithm (10 req/s for Haiku)
- Configurable rate and burst capacity
- Thread-safe implementation

```python
class RateLimiter:
    def __init__(self, rate: float = 10.0, burst: int = 20):
        # Token bucket rate limiter
```

### Usage

```bash
# Default: 20 workers, 10 req/s
python3 src/indexer.py --repo /path/to/repo

# Custom workers and rate limit
python3 src/indexer.py --repo /path/to/repo --workers 30 --rate-limit 15
```

---

## 2. Enhanced Caching

### HTTP Cache (`src/indexer.py`)

Features:

- File-based persistent cache
- TTL support (default: 1 hour)
- Automatic expiration
- Thread-safe operations

```python
class HTTPCache:
    def __init__(self, cache_path: Path, ttl_seconds: int = 3600):
        # Cache with automatic expiration
```

Cache files:

- `data/.http_cache.json` - HTTP responses (GitHub API, etc.)
- `data/.indexer_cache.json` - Agent content hash cache (existing)

### Search Result Cache (`src/search.py`)

Features:

- LRU (Least Recently Used) eviction
- Thread-safe operations
- Configurable max size (default: 500 entries)
- Hit/miss tracking

```python
class LRUCache:
    def __init__(self, max_size: int = 1000):
        # LRU cache implementation
```

Usage:

```python
search = AgentSearch(agents, enable_cache=True)
results = search.search("query", use_cache=True)
stats = search.cache_stats()
```

---

## 3. Performance Monitoring

### PerformanceMetrics Class

Tracks:

- Operation timings (avg, total, call count)
- Counters (agents extracted, cache hits, etc.)
- Slow operation detection (>1s average)

```python
class PerformanceMetrics:
    def record_timing(self, operation: str, duration: float) -> None:
        # Track operation timing

    def increment(self, counter: str, value: int = 1) -> None:
        # Track counters
```

### Decorator for Timing

```python
@timed("llm_extraction")
def _extract_with_llm(self, readme_content: str, folder_path: str) -> dict:
    # Automatically timed operation
```

### Performance Report

After indexing, a detailed report is printed:

```
============================================================
PERFORMANCE REPORT
============================================================
Total time: 42.35s

Counters:
  agents_extracted: 120
  cache_hits_agent: 85
  llm_success: 35
  llm_failures: 0

Timings:
  llm_extraction:
    calls: 35, avg: 0.845s, total: 29.58s
  github_api_stars:
    calls: 1, avg: 0.234s, total: 0.23s
============================================================
```

---

## 4. Data Structure Optimizations

### Precompiled Regex

Search tokenization uses precompiled regex for better performance:

```python
self._tokenize_pattern = re.compile(r"[^\w\s]")
```

### Tokenization Fallback

Empty documents are handled gracefully:

```python
if not tokens:
    tokens = [agent.get("id", "unknown")]
```

---

## 5. CLI Enhancements

### New Options

```bash
--workers N          # Max parallel workers (default: 20)
--rate-limit N       # LLM API rate limit in req/s (default: 10)
--no-progress        # Disable progress bars
```

### Examples

```bash
# Fast indexing with LLM enrichment
ANTHROPIC_API_KEY=xxx python3 src/indexer.py \
  --repo /path/to/awesome-llm-apps \
  --workers 30 \
  --rate-limit 15

# Heuristic-only mode (no API key needed)
python3 src/indexer.py \
  --repo /path/to/awesome-llm-apps \
  --workers 10 \
  --no-llm

# Test run with limit
python3 src/indexer.py \
  --repo /path/to/awesome-llm-apps \
  --limit 50 \
  --dry-run
```

---

## 6. Testing

### Performance Test Suite

Run the performance tests:

```bash
python3 test_performance.py
```

Tests cover:

- Rate limiter functionality
- Search cache hit/miss
- Parallel processing
- Performance metrics tracking
- HTTP cache operations

---

## 7. Dependencies

Added to `requirements.txt`:

```
tqdm>=4.65.0  # Progress bars
```

---

## 8. Configuration Tuning

### Worker Count

- **Low memory/CPU**: 5-10 workers
- **Standard**: 20 workers (default)
- **High performance**: 30-50 workers

### Rate Limiting

- **Claude Haiku**: 10 req/s (default)
- **Claude Sonnet**: 5 req/s
- **Claude Opus**: 2 req/s

### Batch Size

Hardcoded to 100 agents per batch for memory efficiency.

---

## 9. Monitoring and Debugging

### Enable Progress Bars

Progress bars are automatically enabled when `tqdm` is installed and output is a TTY.

```bash
# Install tqdm
pip install tqdm

# Run with progress bars
python3 src/indexer.py --repo /path/to/repo
```

### Performance Report

Always printed at the end of indexing:

- Total time
- Operation counts
- Timing breakdown
- Slow operations (>1s avg)

---

## 10. Troubleshooting

### Slow Indexing

1. Check worker count: Increase `--workers`
2. Check rate limit: Adjust `--rate-limit`
3. Check cache hits: High cache hits = good
4. Check for network issues

### Memory Issues

Reduce `--workers` or batch size (modify `batch_size` in code).

### Rate Limiting Errors

Reduce `--rate-limit` to match API quotas.

---

## Summary

| Feature      | Before      | After                 |
| ------------ | ----------- | --------------------- |
| 120 agents   | ~5 min      | <45 sec (10-15x)      |
| Scalability  | ~500 agents | 2000+ agents          |
| LLM calls    | Sequential  | Parallel (20 workers) |
| HTTP cache   | None        | TTL-based             |
| Search cache | None        | LRU (500 entries)     |
| Monitoring   | Basic       | Detailed report       |
