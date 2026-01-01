"""
Agent Navigator - Hybrid Search Engine
=======================================
Combines BM25 keyword search with vector similarity for best of both worlds.

"coding bot" finds:
1. BM25: "Coding Assistant" (keyword match)
2. Vector: "Developer Agent" (semantic similarity)
3. RRF: Fused results ranked by combined relevance

Performance Features:
- Lazy embedding generation (only when needed)
- Embeddings cached in JSON (no vector DB needed for <10k items)
- Reciprocal Rank Fusion for result merging
- Cost-effective: ~$0.01 per 500 agents using text-embedding-3-small

Migration Path:
- Drop-in replacement for AgentSearch
- Works with both BM25 and SQLite FTS5 backends
- Enable with HYBRID_SEARCH=true
"""

from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)

# Lazy imports (only load if embeddings are enabled)
_numpy = None
_openai = None


def _get_numpy():
    """Lazy import numpy."""
    global _numpy
    if _numpy is None:
        try:
            import numpy as np
            _numpy = np
        except ImportError:
            raise ImportError("numpy is required for hybrid search. Install with: pip install numpy")
    return _numpy


def _get_openai():
    """Lazy import OpenAI client."""
    global _openai
    if _openai is None:
        try:
            import openai
            _openai = openai
        except ImportError:
            raise ImportError("openai is required for embeddings. Install with: pip install openai")
    return _openai


class EmbeddingCache:
    """
    Persistent cache for agent embeddings.

    Stores embeddings in JSON with content hash for invalidation.
    Cost-effective for <10k agents (no vector DB needed).
    """

    def __init__(self, cache_path: Path):
        self.cache_path = Path(cache_path)
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self.embeddings: Dict[str, Dict[str, Any]] = {}
        self._load()

    def _load(self) -> None:
        """Load embeddings from disk."""
        if self.cache_path.exists():
            try:
                self.embeddings = json.loads(self.cache_path.read_text(encoding="utf-8"))
                logger.info(f"Loaded {len(self.embeddings)} embeddings from cache")
            except Exception as e:
                logger.warning(f"Failed to load embedding cache: {e}")
                self.embeddings = {}

    def save(self) -> None:
        """Save embeddings to disk."""
        try:
            self.cache_path.write_text(json.dumps(self.embeddings, ensure_ascii=False), encoding="utf-8")
        except Exception as e:
            logger.error(f"Failed to save embedding cache: {e}")

    def get(self, agent_id: str, content_hash: str) -> Optional[List[float]]:
        """
        Get cached embedding if content hash matches.

        Args:
            agent_id: Agent identifier
            content_hash: Hash of agent content

        Returns:
            Embedding vector or None if not cached/invalid
        """
        cached = self.embeddings.get(agent_id)
        if cached and cached.get("hash") == content_hash:
            return cached.get("embedding")
        return None

    def set(self, agent_id: str, content_hash: str, embedding: List[float]) -> None:
        """
        Cache an embedding.

        Args:
            agent_id: Agent identifier
            content_hash: Hash of agent content
            embedding: Embedding vector
        """
        self.embeddings[agent_id] = {
            "hash": content_hash,
            "embedding": embedding,
        }

    def clear(self) -> None:
        """Clear all cached embeddings."""
        self.embeddings = {}
        if self.cache_path.exists():
            self.cache_path.unlink()


def compute_content_hash(agent: Dict) -> str:
    """
    Compute stable hash of agent content for cache invalidation.

    Args:
        agent: Agent dictionary

    Returns:
        MD5 hash of searchable content
    """
    # Combine all searchable fields
    content = " ".join([
        str(agent.get("name", "")),
        str(agent.get("description", "")),
        str(agent.get("tagline", "")),
        str(agent.get("category", "")),
        " ".join(agent.get("frameworks", [])),
        " ".join(agent.get("llm_providers", [])),
    ])
    return hashlib.md5(content.encode("utf-8")).hexdigest()[:12]


class HybridSearch:
    """
    Hybrid search combining BM25/FTS5 with vector similarity.

    Wraps an existing search engine and adds semantic search via embeddings.
    Uses Reciprocal Rank Fusion (RRF) to merge results.

    Example:
        base_search = AgentSearch(agents)
        hybrid = HybridSearch(base_search, api_key="sk-...")
        results = hybrid.search("coding assistant", limit=10)
    """

    def __init__(
        self,
        base_search_engine: Any,
        api_key: Optional[str] = None,
        embedding_model: str = "text-embedding-3-small",
        cache_path: Optional[Path] = None,
        enable_embeddings: bool = True,
    ):
        """
        Initialize hybrid search.

        Args:
            base_search_engine: Existing search engine (AgentSearch or SQLiteAgentSearch)
            api_key: OpenAI API key (uses OPENAI_API_KEY env if None)
            embedding_model: OpenAI embedding model to use
            cache_path: Path to embedding cache file
            enable_embeddings: Enable vector search (set False to fallback to BM25 only)
        """
        self.base_search = base_search_engine
        self.embedding_model = embedding_model
        self.enable_embeddings = enable_embeddings

        # Initialize OpenAI client if embeddings enabled
        if enable_embeddings:
            openai = _get_openai()
            self.client = openai.OpenAI(api_key=api_key)
        else:
            self.client = None

        # Initialize embedding cache
        if cache_path is None:
            cache_path = Path("data/.embeddings_cache.json")
        self.embedding_cache = EmbeddingCache(cache_path)

        # Precompute embeddings for all agents if enabled
        if enable_embeddings:
            self._ensure_embeddings()

    def _ensure_embeddings(self) -> None:
        """Ensure all agents have cached embeddings."""
        agents = self.base_search.agents
        missing = []

        for agent_id, agent in agents.items():
            content_hash = compute_content_hash(agent)
            if self.embedding_cache.get(agent_id, content_hash) is None:
                missing.append((agent_id, agent, content_hash))

        if missing:
            logger.info(f"Generating embeddings for {len(missing)} agents")
            self._batch_embed(missing)
            self.embedding_cache.save()

    def _batch_embed(self, agents_to_embed: List[tuple]) -> None:
        """
        Generate embeddings for multiple agents in batch.

        Args:
            agents_to_embed: List of (agent_id, agent, content_hash) tuples
        """
        if not self.client:
            return

        # Prepare texts for embedding
        texts = []
        for _, agent, _ in agents_to_embed:
            # Combine searchable fields
            text = " ".join([
                agent.get("name", ""),
                agent.get("description", ""),
                agent.get("tagline", ""),
                agent.get("category", ""),
                " ".join(agent.get("frameworks", [])),
                " ".join(agent.get("llm_providers", [])),
            ])
            texts.append(text.strip())

        # Batch API call (OpenAI supports up to 2048 inputs per request)
        batch_size = 100
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i : i + batch_size]
            batch_agents = agents_to_embed[i : i + batch_size]

            try:
                response = self.client.embeddings.create(
                    model=self.embedding_model,
                    input=batch_texts,
                )

                # Cache embeddings
                for j, embedding_obj in enumerate(response.data):
                    agent_id, _, content_hash = batch_agents[j]
                    embedding = embedding_obj.embedding
                    self.embedding_cache.set(agent_id, content_hash, embedding)

            except Exception as e:
                logger.error(f"Failed to generate embeddings for batch {i}: {e}")

    def _get_embedding(self, text: str) -> Optional[List[float]]:
        """
        Get embedding for a query text.

        Args:
            text: Query text

        Returns:
            Embedding vector or None on error
        """
        if not self.client:
            return None

        try:
            response = self.client.embeddings.create(
                model=self.embedding_model,
                input=[text],
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Failed to generate query embedding: {e}")
            return None

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        Compute cosine similarity between two vectors.

        Args:
            vec1: First vector
            vec2: Second vector

        Returns:
            Similarity score (0-1, higher is more similar)
        """
        np = _get_numpy()
        a = np.array(vec1)
        b = np.array(vec2)
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

    def _vector_search(self, query: str, limit: int) -> List[Dict]:
        """
        Perform vector similarity search.

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            List of agents with similarity scores
        """
        query_embedding = self._get_embedding(query)
        if not query_embedding:
            return []

        # Compute similarity with all agents
        agents = self.base_search.agents
        scores = []

        for agent_id, agent in agents.items():
            content_hash = compute_content_hash(agent)
            agent_embedding = self.embedding_cache.get(agent_id, content_hash)

            if agent_embedding:
                similarity = self._cosine_similarity(query_embedding, agent_embedding)
                scores.append((agent_id, similarity))

        # Sort by similarity and return top results
        scores.sort(key=lambda x: -x[1])

        results = []
        for agent_id, score in scores[:limit]:
            agent = agents[agent_id].copy()
            agent["_vector_score"] = round(score, 3)
            results.append(agent)

        return results

    def _reciprocal_rank_fusion(
        self,
        keyword_results: List[Dict],
        vector_results: List[Dict],
        k: int = 60,
    ) -> List[Dict]:
        """
        Merge keyword and vector results using Reciprocal Rank Fusion.

        RRF formula: score = sum(1 / (k + rank))
        where k is a constant (typically 60) and rank starts at 1.

        Args:
            keyword_results: Results from BM25/FTS5 search
            vector_results: Results from vector search
            k: RRF constant (default: 60)

        Returns:
            Merged and re-ranked results
        """
        # Build rank maps
        keyword_ranks = {r["id"]: i + 1 for i, r in enumerate(keyword_results)}
        vector_ranks = {r["id"]: i + 1 for i, r in enumerate(vector_results)}

        # Combine all agent IDs
        all_ids = set(keyword_ranks.keys()) | set(vector_ranks.keys())

        # Compute RRF scores
        rrf_scores = {}
        for agent_id in all_ids:
            score = 0.0
            if agent_id in keyword_ranks:
                score += 1.0 / (k + keyword_ranks[agent_id])
            if agent_id in vector_ranks:
                score += 1.0 / (k + vector_ranks[agent_id])
            rrf_scores[agent_id] = score

        # Sort by RRF score
        ranked = sorted(rrf_scores.items(), key=lambda x: -x[1])

        # Build result list
        agents = self.base_search.agents
        results = []
        for agent_id, rrf_score in ranked:
            agent = agents[agent_id].copy()
            agent["_rrf_score"] = round(rrf_score, 3)
            # Preserve original scores if available
            if agent_id in keyword_ranks:
                keyword_agent = keyword_results[keyword_ranks[agent_id] - 1]
                agent["_keyword_score"] = keyword_agent.get("_score", 0)
            if agent_id in vector_ranks:
                vector_agent = vector_results[vector_ranks[agent_id] - 1]
                agent["_vector_score"] = vector_agent.get("_vector_score", 0)
            results.append(agent)

        return results

    def search(self, query: str, limit: int = 20, use_cache: bool = True) -> List[Dict]:
        """
        Hybrid search combining keyword and semantic search.

        Args:
            query: Search query
            limit: Maximum results to return
            use_cache: Use cached results (passed to base search)

        Returns:
            Merged and re-ranked results
        """
        if not self.enable_embeddings:
            # Fallback to keyword-only search
            return self.base_search.search(query, limit=limit, use_cache=use_cache)

        # Perform both searches in parallel (could be parallelized further)
        keyword_results = self.base_search.search(query, limit=limit * 2, use_cache=use_cache)
        vector_results = self._vector_search(query, limit=limit * 2)

        # Merge using RRF
        merged = self._reciprocal_rank_fusion(keyword_results, vector_results)

        return merged[:limit]

    # Delegate other methods to base search engine
    def filter_agents(self, *args, **kwargs):
        """Delegate filtering to base search."""
        return self.base_search.filter_agents(*args, **kwargs)

    def get_filter_options(self):
        """Delegate filter options to base search."""
        return self.base_search.get_filter_options()

    @property
    def agents(self):
        """Delegate agents property to base search."""
        return self.base_search.agents

    def clear_cache(self):
        """Clear both search and embedding caches."""
        self.base_search.clear_cache()
        self.embedding_cache.clear()

    def cache_stats(self):
        """Get cache statistics from base search."""
        return self.base_search.cache_stats()
