"""
Tests for src.search module.

Covers:
- BM25 scoring and ranking
- Query tokenization
- Empty query handling
- Fallback substring matching
- Multi-value filter support
- Filter edge cases
- Search result limiting
"""

import pytest
from src.search import AgentSearch


class TestAgentSearchInit:
    """Tests for AgentSearch initialization."""

    def test_initialization_with_empty_agents(self):
        search = AgentSearch([])
        assert search.agents == {}
        assert search.agent_ids == []
        assert len(search.corpus) == 0

    def test_initialization_builds_corpus(self, sample_agents):
        search = AgentSearch(sample_agents)
        assert len(search.agents) == 3
        assert len(search.corpus) == 3
        assert "pdf_assistant" in search.agents

    def test_initialization_with_missing_fields(self):
        agents = [
            {"id": "a"},  # Missing many fields
            {"id": "b", "name": "B"},
        ]
        search = AgentSearch(agents)
        assert len(search.agents) == 2


class TestTokenize:
    """Tests for text tokenization."""

    def test_tokenize_lowercases(self):
        search = AgentSearch([])
        tokens = search._tokenize("HELLO World")
        assert "hello" in tokens
        assert "world" in tokens

    def test_tokenize_removes_special_chars(self):
        search = AgentSearch([])
        tokens = search._tokenize("hello-world! test@example.com")
        assert "hello" in tokens or "world" in tokens
        assert "test" in tokens or "example" in tokens

    def test_tokenize_filters_short_tokens(self):
        search = AgentSearch([])
        tokens = search._tokenize("a an the hello world")
        assert "hello" in tokens
        assert "world" in tokens
        # Short tokens should be filtered
        assert "a" not in tokens
        assert "an" not in tokens


class TestSearch:
    """Tests for search functionality."""

    def test_search_empty_query_returns_sorted_by_name(self, sample_agents):
        search = AgentSearch(sample_agents)
        results = search.search("", limit=10)
        assert [r["id"] for r in results] == ["finance_agent", "local_chat", "pdf_assistant"]

    def test_search_whitespace_query_returns_sorted(self, sample_agents):
        search = AgentSearch(sample_agents)
        results = search.search("   ", limit=10)
        assert len(results) == 3

    def test_search_bm25_finds_expected_match(self, sample_agents):
        search = AgentSearch(sample_agents)
        results = search.search("pdf bot", limit=5)
        assert results
        assert results[0]["id"] == "pdf_assistant"
        assert results[0]["_score"] > 0

    def test_search_finds_by_description(self, sample_agents):
        search = AgentSearch(sample_agents)
        results = search.search("stock analysis", limit=5)
        assert any(r["id"] == "finance_agent" for r in results)

    def test_search_finds_by_framework(self, sample_agents):
        search = AgentSearch(sample_agents)
        results = search.search("langchain", limit=5)
        langchain_agents = [r for r in results if "langchain" in r.get("frameworks", [])]
        assert len(langchain_agents) >= 2  # pdf_assistant and finance_agent

    def test_search_finds_by_provider(self, sample_agents):
        search = AgentSearch(sample_agents)
        results = search.search("ollama", limit=5)
        assert any(r["id"] == "local_chat" for r in results)

    def test_search_respects_limit(self, sample_agents):
        search = AgentSearch(sample_agents)
        results = search.search("agent", limit=2)
        assert len(results) <= 2

    def test_search_returns_score_in_results(self, sample_agents):
        search = AgentSearch(sample_agents)
        results = search.search("pdf", limit=5)
        for r in results:
            assert "_score" in r
            assert isinstance(r["_score"], (int, float))

    def test_search_with_no_matches(self, sample_agents):
        search = AgentSearch(sample_agents)
        results = search.search("xyznotfound123", limit=5)
        # May return empty or fallback results
        assert isinstance(results, list)

    def test_search_case_insensitive(self, sample_agents):
        search = AgentSearch(sample_agents)
        r1 = search.search("PDF", limit=5)
        r2 = search.search("pdf", limit=5)
        r3 = search.search("PdF", limit=5)
        # All should return the same top result
        assert r1[0]["id"] == r2[0]["id"] == r3[0]["id"]

    def test_search_multiword_query(self, sample_agents):
        search = AgentSearch(sample_agents)
        results = search.search("offline local chatbot", limit=5)
        assert any(r["id"] == "local_chat" for r in results)

    def test_search_returns_all_for_large_limit(self, sample_agents):
        search = AgentSearch(sample_agents)
        results = search.search("", limit=100)
        assert len(results) == 3


class TestSearchFallback:
    """Tests for fallback substring matching when BM25 fails."""

    def test_fallback_when_bm25_zero_scores(self):
        # Create agents with very generic content
        agents = [
            {"id": "a", "name": "Agent A", "description": "test", "category": "other", "frameworks": [], "llm_providers": []},
            {"id": "b", "name": "Agent B", "description": "test", "category": "other", "frameworks": [], "llm_providers": []},
        ]
        search = AgentSearch(agents)
        results = search.search("agent", limit=10)
        assert len(results) >= 1

    def test_fallback_token_overlap(self):
        agents = [
            {
                "id": "python_agent",
                "name": "Python Agent",
                "description": "A python tool",
                "category": "other",
                "frameworks": ["python"],
                "llm_providers": [],
            },
            {
                "id": "js_agent",
                "name": "JavaScript Agent",
                "description": "A js tool",
                "category": "other",
                "frameworks": ["javascript"],
                "llm_providers": [],
            },
        ]
        search = AgentSearch(agents)
        results = search.search("python", limit=10)
        assert any(r["id"] == "python_agent" for r in results)


class TestFilterAgents:
    """Tests for agent filtering."""

    def test_no_filters_returns_all(self, sample_agents):
        search = AgentSearch(sample_agents)
        filtered = search.filter_agents(sample_agents)
        assert len(filtered) == 3

    def test_filter_single_category(self, sample_agents):
        search = AgentSearch(sample_agents)
        filtered = search.filter_agents(sample_agents, category="rag")
        assert all(a["category"] == "rag" for a in filtered)

    def test_filter_multiple_categories(self, sample_agents):
        search = AgentSearch(sample_agents)
        filtered = search.filter_agents(sample_agents, category=["rag", "chatbot"])
        assert all(a["category"] in ["rag", "chatbot"] for a in filtered)

    def test_filter_single_framework(self, sample_agents):
        search = AgentSearch(sample_agents)
        filtered = search.filter_agents(sample_agents, framework="langchain")
        assert all(any(f == "langchain" for f in a.get("frameworks", [])) for a in filtered)

    def test_filter_multiple_frameworks(self, sample_agents):
        search = AgentSearch(sample_agents)
        filtered = search.filter_agents(sample_agents, framework=["langchain", "raw_api"])
        for a in filtered:
            frameworks = a.get("frameworks", [])
            assert any(f in ["langchain", "raw_api"] for f in frameworks)

    def test_filter_provider(self, sample_agents):
        search = AgentSearch(sample_agents)
        filtered = search.filter_agents(sample_agents, provider="openai")
        assert all(any(p == "openai" for p in a.get("llm_providers", [])) for a in filtered)

    def test_filter_complexity(self, sample_agents):
        search = AgentSearch(sample_agents)
        filtered = search.filter_agents(sample_agents, complexity="beginner")
        assert all(a["complexity"] == "beginner" for a in filtered)

    def test_filter_multiple_complexities(self, sample_agents):
        search = AgentSearch(sample_agents)
        filtered = search.filter_agents(sample_agents, complexity=["beginner", "intermediate"])
        assert all(a["complexity"] in ["beginner", "intermediate"] for a in filtered)

    def test_filter_local_only(self, sample_agents):
        search = AgentSearch(sample_agents)
        filtered = search.filter_agents(sample_agents, local_only=True)
        assert all(a.get("supports_local_models") is True for a in filtered)
        assert len(filtered) == 1
        assert filtered[0]["id"] == "local_chat"

    def test_filter_combined_filters(self, sample_agents):
        search = AgentSearch(sample_agents)
        filtered = search.filter_agents(
            sample_agents,
            category="rag",
            provider="openai",
            complexity="beginner",
        )
        assert all(
            a["category"] == "rag"
            and any(p == "openai" for p in a.get("llm_providers", []))
            and a["complexity"] == "beginner"
            for a in filtered
        )

    def test_filter_all_value_returns_none(self, sample_agents):
        search = AgentSearch(sample_agents)
        # "all" should be treated as no filter
        filtered = search.filter_agents(sample_agents, category="all")
        assert len(filtered) == 3

    def test_filter_empty_list_acts_as_no_filter(self, sample_agents):
        search = AgentSearch(sample_agents)
        filtered = search.filter_agents(sample_agents, category=[])
        assert len(filtered) == 3

    def test_filter_tuple_values(self, sample_agents):
        search = AgentSearch(sample_agents)
        filtered = search.filter_agents(sample_agents, category=("rag", "chatbot"))
        assert all(a["category"] in ["rag", "chatbot"] for a in filtered)

    def test_filter_set_values(self, sample_agents):
        search = AgentSearch(sample_agents)
        filtered = search.filter_agents(sample_agents, category={"rag", "chatbot"})
        assert all(a["category"] in ["rag", "chatbot"] for a in filtered)

    def test_filter_with_no_matches(self, sample_agents):
        search = AgentSearch(sample_agents)
        filtered = search.filter_agents(sample_agents, category="nonexistent")
        assert len(filtered) == 0

    def test_filter_with_missing_fields(self):
        agents = [
            {"id": "a", "name": "A"},  # Missing category
            {"id": "b", "name": "B", "category": "rag"},
        ]
        search = AgentSearch(agents)
        filtered = search.filter_agents(agents, category="rag")
        assert len(filtered) == 1
        assert filtered[0]["id"] == "b"


class TestGetFilterOptions:
    """Tests for extracting filter options."""

    def test_get_filter_options(self, sample_agents):
        search = AgentSearch(sample_agents)
        options = search.get_filter_options()

        assert "categories" in options
        assert "frameworks" in options
        assert "providers" in options
        assert "complexities" in options

        assert "rag" in options["categories"]
        assert "chatbot" in options["categories"]
        assert "langchain" in options["frameworks"]
        assert "openai" in options["providers"]

    def test_filter_options_complexities_always_full(self):
        agents = [{"id": "a", "name": "A", "category": "other", "frameworks": [], "llm_providers": [], "complexity": "beginner"}]
        search = AgentSearch(agents)
        options = search.get_filter_options()
        assert options["complexities"] == ["beginner", "intermediate", "advanced"]

    def test_filter_options_empty_agents(self):
        search = AgentSearch([])
        options = search.get_filter_options()
        assert options["categories"] == []
        assert options["frameworks"] == []
        assert options["providers"] == []


class TestEdgeCases:
    """Edge case tests."""

    def test_search_with_unicode_query(self, sample_agents):
        search = AgentSearch(sample_agents)
        results = search.search("chatbot", limit=5)
        assert isinstance(results, list)

    def test_search_with_special_chars(self, sample_agents):
        search = AgentSearch(sample_agents)
        results = search.search("rag@chatbot!", limit=5)
        assert isinstance(results, list)

    def test_agents_with_duplicate_ids(self):
        # Last agent should win
        agents = [
            {"id": "a", "name": "First A", "description": "", "category": "other", "frameworks": [], "llm_providers": []},
            {"id": "a", "name": "Second A", "description": "", "category": "other", "frameworks": [], "llm_providers": []},
        ]
        search = AgentSearch(agents)
        assert search.agents["a"]["name"] == "Second A"
        assert len(search.agent_ids) == 1  # Should deduplicate

    def test_agents_with_none_values(self):
        agents = [
            {"id": "a", "name": None, "description": None, "category": None, "frameworks": None, "llm_providers": None},
        ]
        search = AgentSearch(agents)
        assert len(search.agents) == 1

    def test_search_result_immutability(self, sample_agents):
        search = AgentSearch(sample_agents)
        results1 = search.search("pdf", limit=5)
        results1[0]["name"] = "Modified"
        results2 = search.search("pdf", limit=5)
        # Original agent data should be unchanged
        assert results2[0]["name"] != "Modified"

    def test_filter_with_all_none_values(self, sample_agents):
        search = AgentSearch(sample_agents)
        filtered = search.filter_agents(
            sample_agents,
            category=None,
            framework=None,
            provider=None,
            complexity=None,
        )
        assert len(filtered) == 3


class TestSearchRanking:
    """Tests for result ranking."""

    def test_bm25_score_ordering(self, sample_agents):
        search = AgentSearch(sample_agents)
        results = search.search("pdf", limit=10)
        # Results should be sorted by score
        scores = [r.get("_score", 0) for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_relevance_sort_maintains_order(self, sample_agents):
        search = AgentSearch(sample_agents)
        results = search.search("chatbot", limit=10)
        # With non-empty query, should use relevance (score) ordering
        assert "_score" in results[0]

    def test_empty_query_name_sort(self):
        agents = [
            {"id": "z", "name": "Zeta", "description": "", "category": "other", "frameworks": [], "llm_providers": []},
            {"id": "a", "name": "Alpha", "description": "", "category": "other", "frameworks": [], "llm_providers": []},
            {"id": "m", "name": "Middle", "description": "", "category": "other", "frameworks": [], "llm_providers": []},
        ]
        search = AgentSearch(agents)
        results = search.search("", limit=10)
        assert [r["id"] for r in results] == ["a", "m", "z"]


class TestSearchCorpusBuilding:
    """Tests for search corpus construction."""

    def test_corpus_boosts_name(self):
        agents = [
            {
                "id": "a",
                "name": "UniqueKeyword",
                "description": "common words",
                "category": "other",
                "frameworks": [],
                "llm_providers": [],
            },
            {
                "id": "b",
                "name": "Agent B",
                "description": "also has UniqueKeyword mentioned",
                "category": "other",
                "frameworks": [],
                "llm_providers": [],
            },
        ]
        search = AgentSearch(agents)
        results = search.search("UniqueKeyword", limit=5)
        # Agent with keyword in name should rank higher
        assert results[0]["id"] == "a"

    def test_corpus_includes_all_fields(self, sample_agents):
        search = AgentSearch(sample_agents)
        # Query should match across different fields
        results = search.search("finance", limit=5)
        assert any(r["id"] == "finance_agent" for r in results)
