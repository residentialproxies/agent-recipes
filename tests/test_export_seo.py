"""
Tests for SEO module (src.export.seo).

Tests meta description generation, keyword generation, and Open Graph tags.
"""

import pytest

from src.export.seo import (
    _generate_keywords_meta_tag,
    _generate_meta_description,
    _generate_open_graph_tags,
    _generate_page_title,
)


class TestGenerateMetaDescription:
    """Tests for meta description generation."""

    @pytest.mark.parametrize(
        ("agent", "expected_length_range"),
        [
            # RAG agent with frameworks and providers
            (
                {
                    "name": "PDF Chatbot",
                    "category": "rag",
                    "frameworks": ["langchain", "llamaindex"],
                    "llm_providers": ["openai", "anthropic"],
                    "complexity": "beginner",
                },
                (120, 158),
            ),
            # Minimal agent
            (
                {
                    "name": "Simple Bot",
                    "category": "chatbot",
                    "frameworks": [],
                    "llm_providers": [],
                    "complexity": "intermediate",
                },
                (120, 158),
            ),
            # Agent with single framework/provider
            (
                {
                    "name": "AI Assistant",
                    "category": "agent",
                    "frameworks": ["raw_api"],
                    "llm_providers": ["openai"],
                    "complexity": "advanced",
                },
                (120, 158),
            ),
            # Multi-agent system
            (
                {
                    "name": "Research Team",
                    "category": "multi_agent",
                    "frameworks": ["crewai"],
                    "llm_providers": ["anthropic"],
                    "complexity": "advanced",
                },
                (120, 158),
            ),
        ],
    )
    def test_meta_description_length(self, agent, expected_length_range):
        """Meta description should be within target length (120-158 chars)."""
        min_len, max_len = expected_length_range
        result = _generate_meta_description(agent)
        assert (
            min_len <= len(result) <= max_len
        ), f"Description length {len(result)} not in range [{min_len}, {max_len}]: {result}"

    def test_meta_description_rag_category(self):
        """RAG category should get specific wording."""
        agent = {
            "name": "PDF Chat",
            "category": "rag",
            "frameworks": ["langchain"],
            "llm_providers": ["openai"],
            "complexity": "intermediate",
        }
        result = _generate_meta_description(agent)
        assert "RAG" in result or "rag" in result.lower()

    def test_meta_description_multi_agent_category(self):
        """Multi-agent category should get specific wording."""
        agent = {
            "name": "Team AI",
            "category": "multi_agent",
            "frameworks": [],
            "llm_providers": [],
            "complexity": "intermediate",
        }
        result = _generate_meta_description(agent)
        assert "Multi-agent" in result or "multi-agent" in result.lower()

    def test_meta_description_with_complexity(self):
        """Non-intermediate complexity should be mentioned."""
        agent = {
            "name": "Simple Bot",
            "category": "chatbot",
            "frameworks": [],
            "llm_providers": [],
            "complexity": "beginner",
        }
        result = _generate_meta_description(agent)
        assert "Beginner" in result

    def test_meta_description_advanced_level(self):
        """Advanced complexity should be mentioned."""
        agent = {
            "name": "Complex Agent",
            "category": "agent",
            "frameworks": ["langchain"],
            "llm_providers": ["openai"],
            "complexity": "advanced",
        }
        result = _generate_meta_description(agent)
        assert "Advanced" in result

    def test_meta_description_frameworks_included(self):
        """Frameworks should be mentioned in description."""
        agent = {
            "name": "LC Agent",
            "category": "agent",
            "frameworks": ["langchain", "crewai"],
            "llm_providers": [],
            "complexity": "intermediate",
        }
        result = _generate_meta_description(agent)
        assert "Langchain" in result

    def test_meta_description_providers_included(self):
        """LLM providers should be mentioned."""
        agent = {
            "name": "GPT Bot",
            "category": "chatbot",
            "frameworks": [],
            "llm_providers": ["openai", "anthropic"],
            "complexity": "intermediate",
        }
        result = _generate_meta_description(agent)
        assert "Openai" in result or "openai" in result.lower()

    def test_meta_description_raw_api_filtered(self):
        """raw_api framework should be filtered out."""
        agent = {
            "name": "Direct API Bot",
            "category": "chatbot",
            "frameworks": ["raw_api"],
            "llm_providers": ["openai"],
            "complexity": "intermediate",
        }
        result = _generate_meta_description(agent)
        assert "raw_api" not in result.lower()

    def test_meta_description_truncation(self):
        """Very long descriptions should be truncated."""
        agent = {
            "name": "A" * 200,
            "category": "agent",
            "frameworks": ["langchain"] * 10,
            "llm_providers": ["openai"] * 10,
            "complexity": "intermediate",
        }
        result = _generate_meta_description(agent)
        assert len(result) <= 158

    def test_meta_description_empty_agent(self):
        """Empty/minimal agent should still generate valid description."""
        agent = {
            "name": "",
            "category": "",
            "frameworks": [],
            "llm_providers": [],
            "complexity": "intermediate",
        }
        result = _generate_meta_description(agent)
        assert len(result) >= 120
        assert len(result) <= 158


class TestGenerateKeywordsMetaTag:
    """Tests for keywords meta tag generation."""

    def test_keywords_meta_tag_basic(self):
        """Should generate proper HTML meta tag."""
        agent = {
            "category": "rag",
            "frameworks": ["langchain"],
            "llm_providers": ["openai"],
            "complexity": "beginner",
            "languages": ["python"],
            "tags": ["pdf", "document"],
        }
        result = _generate_keywords_meta_tag(agent)
        assert result.startswith('<meta name="keywords" content="')
        assert result.endswith('" />')
        assert "rag" in result.lower()
        assert "langchain" in result.lower()

    def test_keywords_meta_tag_empty(self):
        """Should return empty string for agent with no keywords."""
        agent = {
            "category": "",
            "frameworks": [],
            "llm_providers": [],
            "complexity": "intermediate",
            "languages": [],
            "tags": [],
        }
        result = _generate_keywords_meta_tag(agent)
        assert result == ""

    def test_keywords_meta_tag_includes_category(self):
        """Category should be in keywords."""
        agent = {
            "category": "chatbot",
            "frameworks": [],
            "llm_providers": [],
            "complexity": "intermediate",
        }
        result = _generate_keywords_meta_tag(agent)
        assert "chatbot" in result.lower()

    def test_keywords_meta_tag_framework_variations(self):
        """Framework keywords should include variations."""
        agent = {
            "category": "agent",
            "frameworks": ["langchain"],
            "llm_providers": [],
            "complexity": "intermediate",
        }
        result = _generate_keywords_meta_tag(agent)
        assert "langchain" in result.lower()

    def test_keywords_meta_tag_openai_expands_to_gpt(self):
        """OpenAI provider should expand to GPT keyword."""
        agent = {
            "category": "agent",
            "frameworks": [],
            "llm_providers": ["openai"],
            "complexity": "intermediate",
        }
        result = _generate_keywords_meta_tag(agent)
        assert "gpt" in result.lower()

    def test_keywords_meta_tag_anthropic_expands_to_claude(self):
        """Anthropic provider should expand to Claude keyword."""
        agent = {
            "category": "agent",
            "frameworks": [],
            "llm_providers": ["anthropic"],
            "complexity": "intermediate",
        }
        result = _generate_keywords_meta_tag(agent)
        assert "claude" in result.lower()

    def test_keywords_meta_tag_includes_languages(self):
        """Programming languages should be in keywords."""
        agent = {
            "category": "agent",
            "frameworks": [],
            "llm_providers": [],
            "complexity": "intermediate",
            "languages": ["python", "typescript"],
        }
        result = _generate_keywords_meta_tag(agent)
        assert "python" in result.lower()
        assert "typescript" in result.lower()

    def test_keywords_meta_tag_includes_tags(self):
        """Tags should be included as keywords."""
        agent = {
            "category": "agent",
            "frameworks": [],
            "llm_providers": [],
            "complexity": "intermediate",
            "tags": ["rag", "vector", "embedding"],
        }
        result = _generate_keywords_meta_tag(agent)
        assert "rag" in result.lower()
        assert "vector" in result.lower()

    def test_keywords_limit_to_15(self):
        """Should limit keywords to prevent bloat."""
        agent = {
            "category": "rag",
            "frameworks": ["langchain", "llamaindex", "crewai", "autogen", "phidata", "dspy"],
            "llm_providers": ["openai", "anthropic", "google", "cohere", "huggingface"],
            "complexity": "beginner",
            "languages": ["python", "javascript", "typescript", "go", "rust"],
            "tags": [f"tag{i}" for i in range(20)],
        }
        result = _generate_keywords_meta_tag(agent)
        # Count keywords by splitting on comma
        keyword_count = len(result.split('content="')[1].split('" />')[0].split(", "))
        assert keyword_count <= 15


class TestGenerateOpenGraphTags:
    """Tests for Open Graph tag generation."""

    def test_og_basic_tags(self):
        """Basic OG tags should be present."""
        result = _generate_open_graph_tags(
            title="Test Agent",
            description="A test agent for testing",
            url="https://example.com/agent",
        )
        assert 'property="og:type" content="website"' in result
        assert 'property="og:title" content="Test Agent"' in result
        assert 'property="og:description" content="A test agent for testing"' in result
        assert 'property="og:url" content="https://example.com/agent"' in result

    def test_og_with_image(self):
        """OG tags should include image when provided."""
        result = _generate_open_graph_tags(
            title="Test",
            description="Test desc",
            url="https://example.com",
            image="https://example.com/og.png",
        )
        assert 'property="og:image" content="https://example.com/og.png"' in result
        assert 'property="og:image:alt" content="Test"' in result
        assert 'property="og:image:width" content="1200"' in result
        assert 'property="og:image:height" content="630"' in result

    def test_og_article_type(self):
        """Article type should include article-specific tags."""
        result = _generate_open_graph_tags(
            title="Article",
            description="Desc",
            url="https://example.com/article",
            og_type="article",
            published_time="2024-01-01T00:00:00Z",
            author="Test Author",
        )
        assert 'property="og:type" content="article"' in result
        assert 'property="article:published_time" content="2024-01-01T00:00:00Z"' in result
        assert 'property="article:author" content="Test Author"' in result

    def test_og_twitter_card_tags(self):
        """Twitter Card tags should be present."""
        result = _generate_open_graph_tags(
            title="Test",
            description="Test description",
            url="https://example.com",
        )
        assert 'name="twitter:card" content="summary_large_image"' in result
        assert 'name="twitter:title" content="Test"' in result
        assert 'name="twitter:description" content="Test description"' in result

    def test_og_twitter_with_image(self):
        """Twitter tags should include image when provided."""
        result = _generate_open_graph_tags(
            title="Test",
            description="Desc",
            url="https://example.com",
            image="https://example.com/og.png",
        )
        assert 'name="twitter:image" content="https://example.com/og.png"' in result

    def test_og_html_escaping(self):
        """Special characters should be HTML-escaped."""
        result = _generate_open_graph_tags(
            title='Test <script>alert("xss")</script>',
            description='Test & Test "quoted"',
            url="https://example.com",
        )
        assert "<script>" not in result
        assert "&lt;script&gt;" in result
        assert "Test &amp; Test" in result or "Test &amp; Test" in result

    def test_og_twitter_site_handles(self):
        """Twitter site and creator handles should be present."""
        result = _generate_open_graph_tags(
            title="Test",
            description="Desc",
            url="https://example.com",
        )
        assert 'name="twitter:site" content="@agent_navigator"' in result
        assert 'name="twitter:creator" content="@agent_navigator"' in result

    def test_og_no_image(self):
        """When no image provided, image tags should be absent."""
        result = _generate_open_graph_tags(
            title="Test",
            description="Desc",
            url="https://example.com",
        )
        assert 'property="og:image"' not in result
        assert 'name="twitter:image"' not in result


class TestGeneratePageTitle:
    """Tests for page title generation."""

    def test_title_basic(self):
        """Basic title should include agent name and site name."""
        result = _generate_page_title(
            {"name": "Test Agent", "category": "rag", "frameworks": []},
            base_name="Agent Navigator",
        )
        assert "Test Agent" in result
        assert "Agent Navigator" in result

    def test_title_with_framework(self):
        """Title should include framework when available."""
        result = _generate_page_title(
            {"name": "PDF Chat", "category": "rag", "frameworks": ["langchain"]},
            base_name="Agent Navigator",
        )
        assert "PDF Chat" in result
        assert "Langchain" in result or "langchain" in result.lower()
        assert "Agent Navigator" in result

    def test_title_truncation(self):
        """Long titles should be truncated to ~65 chars."""
        long_name = "A" * 100
        result = _generate_page_title(
            {"name": long_name, "category": "agent", "frameworks": ["langchain"]},
            base_name="Agent Navigator",
        )
        assert len(result) <= 65
        assert result.endswith("...")

    def test_title_raw_api_filtered(self):
        """raw_api framework should not appear in title."""
        result = _generate_page_title(
            {"name": "Direct Bot", "category": "chatbot", "frameworks": ["raw_api"]},
            base_name="Agent Navigator",
        )
        assert "raw_api" not in result.lower()

    def test_title_multiple_frameworks_uses_first(self):
        """With multiple frameworks, only first should be used."""
        result = _generate_page_title(
            {"name": "Agent", "category": "rag", "frameworks": ["langchain", "llamaindex", "crewai"]},
            base_name="Agent Navigator",
        )
        assert "Langchain" in result or "langchain" in result.lower()
        # Should not include all frameworks
        assert result.count("|") == 2  # name | framework | site

    def test_title_no_framework(self):
        """Title without framework should omit framework section."""
        result = _generate_page_title(
            {"name": "Simple Bot", "category": "chatbot", "frameworks": []},
            base_name="Agent Navigator",
        )
        assert "Simple Bot" in result
        assert "Agent Navigator" in result
        assert result.count("|") == 1  # Only name | site

    def test_title_custom_base_name(self):
        """Custom base name should be used."""
        result = _generate_page_title(
            {"name": "Agent", "category": "rag", "frameworks": []},
            base_name="My Site",
        )
        assert "My Site" in result
        assert "Agent Navigator" not in result
