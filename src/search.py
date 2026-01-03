"""
Agent Navigator - BM25 Search Engine (Performance Optimized)
============================================================
Smarter than keyword matching, cheaper than embeddings.

"PDF bot" can find "Document Assistant"

Performance Features:
- Search result caching with LRU eviction
- Optimized tokenization
- Efficient BM25 implementation
- Structured logging for observability
"""

import hashlib
import logging
import re
import threading
import time
from collections import OrderedDict
from typing import Any

from src.exceptions import AgentNotFoundError, InvalidQueryError

try:
    from rank_bm25 import BM25Okapi

    HAS_BM25 = True
except ImportError:
    HAS_BM25 = False
    # Fallback implementation if rank_bm25 is not available

logger = logging.getLogger(__name__)


# Common English stopwords to filter out
_STOPWORDS = {
    "a",
    "an",
    "the",
    "and",
    "or",
    "but",
    "in",
    "on",
    "at",
    "to",
    "for",
    "of",
    "with",
    "by",
    "from",
    "as",
    "is",
    "was",
    "are",
    "were",
    "be",
    "been",
    "being",
    "have",
    "has",
    "had",
    "do",
    "does",
    "did",
    "will",
    "would",
    "could",
    "should",
    "may",
    "might",
    "can",
    "this",
    "that",
}


# =============================================================================
# Search Result Cache
# =============================================================================


class LRUCache:
    """Thread-safe LRU cache for search results."""

    def __init__(self, max_size: int = 1000) -> None:
        self.max_size = max_size
        self._cache: OrderedDict = OrderedDict()
        self._hits = 0
        self._misses = 0
        self._lock = threading.Lock()

    def get(self, key: tuple) -> list[dict] | None:
        """Get cached search results."""
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
                self._hits += 1
                return self._cache[key]
            self._misses += 1
            return None

    def set(self, key: tuple, value: list[dict]) -> None:
        """Cache search results."""
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
            self._cache[key] = value
            if len(self._cache) > self.max_size:
                self._cache.popitem(last=False)

    def clear(self) -> None:
        """Clear the cache."""
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0

    def stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total = self._hits + self._misses
            hit_rate = self._hits / total if total > 0 else 0
            return {
                "size": len(self._cache),
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": hit_rate,
            }

    def __len__(self) -> int:
        with self._lock:
            return len(self._cache)


# Global search cache
_search_cache = LRUCache(max_size=500)


class AgentSearch:
    """BM25-based search for agent discovery with result caching."""

    def __init__(self, agents: list[dict], enable_cache: bool = True) -> None:
        """
        Args:
            agents: List of agent dictionaries
            enable_cache: Enable search result caching (default: True)
        """
        self.agents = {}
        for a in agents or []:
            key = (a.get("id") or a.get("slug") or "").strip()
            if not key:
                continue
            self.agents[key] = a
        self.agent_ids = list(self.agents.keys())
        self.enable_cache = enable_cache

        # Create a short, stable cache salt (avoid huge keys with thousands of IDs).
        salt_source = "\0".join(sorted(self.agent_ids)).encode("utf-8")
        self._cache_key_salt = hashlib.sha256(salt_source).hexdigest()[:16]

        # Precompile regex for better performance
        self._tokenize_pattern = re.compile(r"[^\w\s]")

        # Build searchable corpus
        self.corpus = []
        for agent in self.agents.values():
            # Combine all searchable fields
            name = agent.get("name", "") or ""
            description = agent.get("description", "") or ""
            tagline = agent.get("tagline", "") or ""
            capabilities = agent.get("capabilities") or []
            frameworks = agent.get("frameworks") or []
            providers = agent.get("llm_providers") or []
            pricing = agent.get("pricing", "") or ""
            text = " ".join(
                [
                    " ".join([name] * 3),  # Boost name without token merging
                    " ".join([description] * 2),  # Boost description without token merging
                    " ".join([tagline] * 2),  # Boost tagline (WebManus)
                    agent.get("category", "") or "",
                    " ".join([str(c) for c in capabilities]) if capabilities else "",
                    " ".join(frameworks) if frameworks else "",
                    " ".join(providers) if providers else "",
                    agent.get("design_pattern", "") or "",
                    agent.get("complexity", "") or "",
                    pricing,
                ]
            )
            tokens = self._tokenize(text)
            # Ensure we have at least one token per document (use id as fallback)
            if not tokens:
                tokens = [(agent.get("id") or agent.get("slug") or "unknown")]
            self.corpus.append(tokens)

        # Initialize BM25 (only if we have agents and the library is available)
        if HAS_BM25 and self.corpus and all(self.corpus):
            self.bm25 = BM25Okapi(self.corpus)
        else:
            self.bm25 = None

    def _tokenize(self, text: str) -> list[str]:
        """
        Simple tokenization with lowercasing (optimized).

        Args:
            text: Text to tokenize.

        Returns:
            List of tokens with stopwords removed.
        """
        # Remove special characters, lowercase, split
        text = self._tokenize_pattern.sub(" ", text.lower())
        tokens = text.split()
        # Remove very short tokens and stopwords
        return [t for t in tokens if len(t) > 1 and t not in _STOPWORDS]

    def search(self, query: str, limit: int = 20, use_cache: bool = True) -> list[dict]:
        """
        Search agents using BM25.

        Args:
            query: Search query string
            limit: Maximum results to return
            use_cache: Use cached results if available (default: True)

        Returns:
            List of agent dicts with scores, sorted by relevance.
        """
        start_time = time.perf_counter()

        # Check cache first
        cache_key = None
        if self.enable_cache and use_cache:
            cache_key = (self._cache_key_salt, query.strip().lower(), limit)
            cached = _search_cache.get(cache_key)
            if cached is not None:
                # Return a deep copy to prevent cache mutation
                duration_ms = (time.perf_counter() - start_time) * 1000
                logger.debug(
                    "search_cache_hit",
                    extra={
                        "query": query[:100],
                        "result_count": len(cached),
                        "duration_ms": round(duration_ms, 2),
                    },
                )
                return [a.copy() for a in cached[:limit]]

        if not query.strip():
            # Return all agents sorted by name (using a copy to prevent cache mutation)
            results = [a.copy() for a in sorted(self.agents.values(), key=lambda a: (a.get("name", "") or "").lower())][
                :limit
            ]
            if self.enable_cache and cache_key:
                _search_cache.set(cache_key, [a.copy() for a in results])
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.debug(
                "search_empty_query",
                extra={
                    "result_count": len(results),
                    "duration_ms": round(duration_ms, 2),
                },
            )
            return results

        # Tokenize query
        query_tokens = self._tokenize(query)
        if not query_tokens:
            results = [a.copy() for a in list(self.agents.values())[:limit]]
            if self.enable_cache and cache_key:
                _search_cache.set(cache_key, [a.copy() for a in results])
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.debug(
                "search_no_tokens",
                extra={
                    "query": query[:100],
                    "result_count": len(results),
                    "duration_ms": round(duration_ms, 2),
                },
            )
            return results

        # Get BM25 scores
        if self.bm25 is not None:
            scores = list(self.bm25.get_scores(query_tokens))
        else:
            # Fallback: simple overlap scoring
            scores = []
            for tokens in self.corpus:
                overlap = len(set(tokens).intersection(query_tokens))
                scores.append(overlap)

        if not scores:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.warning(
                "search_no_scores",
                extra={
                    "query": query[:100],
                    "duration_ms": round(duration_ms, 2),
                },
            )
            return []

        # If BM25 cannot discriminate (common in tiny corpora), fall back to substring match.
        if max(scores) <= 0:
            ranked = []
            for agent_id in self.agent_ids:
                agent = self.agents[agent_id]
                hay_text = " ".join(
                    [
                        str(agent.get("name", "")),
                        str(agent.get("description", "")),
                        str(agent.get("tagline", "")),
                        str(agent.get("category", "")),
                        " ".join([str(c) for c in (agent.get("capabilities") or [])]),
                        str(agent.get("pricing", "")),
                        " ".join(agent.get("frameworks", []) or []),
                        " ".join(agent.get("llm_providers", []) or []),
                    ]
                )
                hay_tokens = set(self._tokenize(hay_text))
                overlap = len(hay_tokens.intersection(query_tokens))
                if overlap > 0:
                    ranked.append((overlap, agent_id))

            ranked.sort(key=lambda x: -x[0])
            output = []
            for overlap, agent_id in ranked[:limit]:
                agent = self.agents[agent_id].copy()
                agent["_score"] = overlap
                output.append(agent)

            if self.enable_cache and cache_key:
                _search_cache.set(cache_key, output)

            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.debug(
                "search_fallback_overlap",
                extra={
                    "query": query[:100],
                    "result_count": len(output),
                    "duration_ms": round(duration_ms, 2),
                },
            )
            return output

        # Combine with agent IDs and sort (keep all scores; BM25 may be <=0 for common terms)
        results = [(self.agent_ids[i], float(scores[i])) for i in range(len(scores))]
        results.sort(key=lambda x: -x[1])

        # Return top results with scores
        output = []
        for agent_id, score in results[:limit]:
            agent = self.agents[agent_id].copy()
            agent["_score"] = round(score, 2)
            output.append(agent)

        if self.enable_cache and cache_key:
            _search_cache.set(cache_key, output)

        duration_ms = (time.perf_counter() - start_time) * 1000
        logger.debug(
            "search_completed",
            extra={
                "query": query[:100],
                "result_count": len(output),
                "duration_ms": round(duration_ms, 2),
                "cached": False,
            },
        )

        return output

    def clear_cache(self) -> None:
        """Clear the search result cache."""
        _search_cache.clear()

    def cache_stats(self) -> dict:
        """Get cache statistics.

        Returns:
            dict: Cache statistics including size, hits, misses, and hit_rate.
        """
        return _search_cache.stats()

    def filter_agents(
        self,
        agents: list[dict],
        category: str | None = None,
        capability: str | None = None,
        framework: str | None = None,
        provider: str | None = None,
        complexity: str | None = None,
        local_only: bool = False,
        pricing: str | None = None,
        min_score: float = 0.0,
    ) -> list[dict]:
        """
        Apply filters to an agent list.

        Backwards compatible with the original single-select API while also
        supporting multi-select values (lists/tuples/sets).

        Args:
            agents: List of agent dictionaries.
            category: Category filter(s).
            capability: Capability filter(s).
            framework: Framework filter(s).
            provider: LLM provider filter(s).
            complexity: Complexity level filter(s).
            local_only: Filter for local model support only.
            pricing: Pricing tier filter(s).
            min_score: Minimum labor score.

        Returns:
            Filtered list of agents.
        """

        def normalize(values):
            """Normalize filter values to list or None."""
            if values is None:
                return None
            if values == "all":
                return None
            if isinstance(values, list | tuple | set):
                cleaned = [v for v in values if v and v != "all"]
                return cleaned or None
            return [values]

        categories = normalize(category)
        capabilities = normalize(capability)
        frameworks = normalize(framework)
        providers = normalize(provider)
        complexities = normalize(complexity)
        pricings = normalize(pricing)

        filtered = agents

        if min_score and float(min_score) > 0:
            filtered = [a for a in filtered if float(a.get("labor_score") or 0) >= float(min_score)]

        if categories:
            filtered = [a for a in filtered if a.get("category") in categories]

        if capabilities:
            filtered = [a for a in filtered if any(c in (a.get("capabilities") or []) for c in capabilities)]

        if frameworks:
            filtered = [a for a in filtered if any(f in a.get("frameworks", []) for f in frameworks)]

        if providers:
            filtered = [a for a in filtered if any(p in a.get("llm_providers", []) for p in providers)]

        if complexities:
            filtered = [a for a in filtered if a.get("complexity") in complexities]

        if local_only:
            filtered = [a for a in filtered if a.get("supports_local_models", False)]

        if pricings:
            filtered = [a for a in filtered if a.get("pricing") in pricings]

        return filtered

    def get_filter_options(self) -> dict:
        """Extract all unique filter values from agents."""
        categories = set()
        frameworks = set()
        providers = set()
        complexities = set()
        capabilities = set()
        pricings = set()

        for agent in self.agents.values():
            if agent.get("category") is not None:
                categories.add(agent.get("category", "other"))
            frameworks.update(agent.get("frameworks", []))
            providers.update(agent.get("llm_providers", []))
            complexities.add(agent.get("complexity", "intermediate"))
            capabilities.update(agent.get("capabilities") or [])
            if agent.get("pricing"):
                pricings.add(agent.get("pricing"))

        return {
            "categories": sorted(categories),
            "capabilities": sorted({str(c).lower() for c in capabilities if c}),
            "frameworks": sorted(frameworks),
            "providers": sorted(providers),
            "pricings": sorted(pricings),
            "complexities": ["beginner", "intermediate", "advanced"],
        }


# Quick test
if __name__ == "__main__":
    # Sample data for testing
    sample_agents = [
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
        },
    ]

    search = AgentSearch(sample_agents)

    # Test search
    print("Search: 'PDF bot'")
    results = search.search("PDF bot")
    for r in results:
        print(f"  {r['name']}: {r.get('_score', 0)}")

    print("\nSearch: 'document'")
    results = search.search("document")
    for r in results:
        print(f"  {r['name']}: {r.get('_score', 0)}")

    print("\nSearch: 'offline local'")
    results = search.search("offline local")
    for r in results:
        print(f"  {r['name']}: {r.get('_score', 0)}")

    print("\nFilter options:")
    print(search.get_filter_options())
