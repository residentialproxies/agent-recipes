"""
Tests for src.export_static module.

Covers:
- HTML generation for index and agent pages
- Asset file generation (CSS, JS)
- Sitemap and robots.txt generation
- SEO meta tags
- URL slugification
- Date formatting
- HTML escaping
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import pytest
from src.export_static import (
    _read_json,
    _write,
    _slug,
    _iso_date,
    _category_icon,
    _normalize_record,
    _layout,
    _render_index,
    _render_agent,
    _render_assets,
    _render_sitemap,
    export_site,
)


class TestReadJson:
    """Tests for JSON file reading."""

    def test_read_json_valid(self, tmp_path: Path):
        data_file = tmp_path / "data.json"
        data_file.write_text('[{"id": "test"}]', encoding="utf-8")
        result = _read_json(data_file)
        assert result == [{"id": "test"}]

    def test_read_json_empty_array(self, tmp_path: Path):
        data_file = tmp_path / "data.json"
        data_file.write_text('[]', encoding="utf-8")
        result = _read_json(data_file)
        assert result == []

    def test_read_json_invalid(self, tmp_path: Path):
        data_file = tmp_path / "data.json"
        data_file.write_text('invalid json', encoding="utf-8")
        with pytest.raises(json.JSONDecodeError):
            _read_json(data_file)


class TestWrite:
    """Tests for file writing."""

    def test_write_creates_parent_dirs(self, tmp_path: Path):
        file_path = tmp_path / "nested" / "dir" / "file.txt"
        _write(file_path, "content")
        assert file_path.exists()
        assert file_path.read_text(encoding="utf-8") == "content"

    def test_write_overwrites_existing(self, tmp_path: Path):
        file_path = tmp_path / "file.txt"
        _write(file_path, "original")
        _write(file_path, "new content")
        assert file_path.read_text(encoding="utf-8") == "new content"


class TestSlug:
    """Tests for URL slugification."""

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("Simple Agent", "simple-agent"),
            ("Agent!@#$%Name", "agent-name"),
            ("Multiple   Spaces", "multiple-spaces"),
            ("already-slug", "already-slug"),
            ("UPPER CASE", "upper-case"),
            ("123 numbers", "123-numbers"),
            ("", "agent"),
            ("a" * 100, "a" * 80),  # Length limit
        ],
    )
    def test_slug(self, value: str, expected: str):
        result = _slug(value)
        assert result == expected


class TestIsoDate:
    """Tests for ISO date formatting."""

    def test_iso_date_valid(self):
        result = _iso_date(1609459200)  # 2021-01-01 00:00:00 UTC
        assert result == "2021-01-01"

    def test_iso_date_zero(self):
        assert _iso_date(0) is None

    def test_iso_date_negative(self):
        assert _iso_date(-1) is None

    def test_iso_date_none(self):
        assert _iso_date(None) is None

    def test_iso_date_recent(self):
        ts = int(datetime(2024, 6, 15).timestamp())
        result = _iso_date(ts)
        assert result == "2024-06-15"


class TestCategoryIcon:
    """Tests for category icon lookup."""

    def test_known_category_icons(self):
        assert _category_icon("rag") == "📚"
        assert _category_icon("chatbot") == "💬"
        assert _category_icon("agent") == "🤖"
        assert _category_icon("multi_agent") == "🧩"

    def test_unknown_category_icon(self):
        assert _category_icon("unknown") == "✨"
        assert _category_icon("") == "✨"
        assert _category_icon(None) == "✨"

    def test_all_categories_have_icons(self):
        categories = ["rag", "chatbot", "agent", "multi_agent", "automation", "search", "vision", "voice", "coding", "finance", "research", "other"]
        for cat in categories:
            icon = _category_icon(cat)
            assert icon
            assert len(icon) > 0


class TestNormalizeRecord:
    """Tests for agent record normalization."""

    def test_normalize_adds_defaults(self):
        agent = {}
        normalized = _normalize_record(agent)
        assert normalized["id"]
        assert normalized["name"] == "Untitled"
        assert normalized["category"] == "other"
        assert normalized["frameworks"] == []
        assert normalized["llm_providers"] == []

    def test_normalize_preserves_fields(self):
        agent = {
            "id": "test",
            "name": "Test Agent",
            "category": "rag",
        }
        normalized = _normalize_record(agent)
        assert normalized["id"] == "test"
        assert normalized["name"] == "Test Agent"
        assert normalized["category"] == "rag"

    def test_normalize_generates_id_from_name(self):
        agent = {"name": "My Great Agent"}
        normalized = _normalize_record(agent)
        assert normalized["id"] == "my-great-agent"

    def test_normalize_handles_empty_name(self):
        agent = {"name": ""}
        normalized = _normalize_record(agent)
        assert normalized["id"] == "agent"

    def test_normalize_lists_default_to_empty(self):
        agent = {}
        normalized = _normalize_record(agent)
        assert normalized["frameworks"] == []
        assert normalized["llm_providers"] == []
        assert normalized["api_keys"] == []


class TestLayout:
    """Tests for HTML layout generation."""

    def test_layout_contains_required_elements(self):
        html = _layout(
            title="Test Title",
            description="Test Description",
            body="<p>Body</p>",
        )
        assert "<!doctype html>" in html.lower()
        assert "<html" in html.lower()
        assert "<title>Test Title</title>" in html
        assert '<meta name="description" content="Test Description"' in html
        assert "<p>Body</p>" in html

    def test_layout_html_escaping(self):
        html = _layout(
            title="<script>alert('xss')</script>",
            description="Test & Test",
            body="<p>Body</p>",
        )
        assert "<script>" not in html
        assert "&lt;script&gt;" in html
        assert "Test &amp; Test" in html

    def test_layout_with_canonical(self):
        html = _layout(
            title="Test",
            description="Test",
            body="Body",
            canonical="https://example.com/page",
        )
        assert '<link rel="canonical" href="https://example.com/page"' in html

    def test_layout_without_canonical(self):
        html = _layout(
            title="Test",
            description="Test",
            body="Body",
            canonical=None,
        )
        assert "canonical" not in html.lower()

    def test_layout_with_asset_prefix(self):
        html = _layout(
            title="Test",
            description="Test",
            body="Body",
            asset_prefix="/custom/",
        )
        assert 'href="/custom/assets/style.css"' in html

    def test_layout_default_asset_prefix(self):
        html = _layout(
            title="Test",
            description="Test",
            body="Body",
        )
        assert 'href="/assets/style.css"' in html or 'href="./assets/style.css"' in html


class TestRenderIndex:
    """Tests for index page rendering."""

    def test_render_index_basic(self):
        agents = [
            {
                "id": "test-agent",
                "name": "Test Agent",
                "description": "A test agent",
                "category": "rag",
                "frameworks": ["langchain"],
                "llm_providers": ["openai"],
                "stars": 100,
            }
        ]
        html = _render_index(agents)
        assert "Test Agent" in html
        assert "A test agent" in html
        assert "test-agent" in html
        assert "rag" in html

    def test_render_index_with_stats(self):
        agents = [
            {"id": "a", "name": "A", "description": "", "category": "rag", "frameworks": [], "llm_providers": []},
            {"id": "b", "name": "B", "description": "", "category": "chatbot", "frameworks": [], "llm_providers": []},
        ]
        html = _render_index(agents)
        assert "2 agents" in html or "2" in html
        assert "2 categories" in html or "categories" in html

    def test_render_index_escaping(self):
        agents = [
            {
                "id": "test",
                "name": "<script>Agent</script>",
                "description": "Test & Description",
                "category": "other",
                "frameworks": [],
                "llm_providers": [],
            }
        ]
        html = _render_index(agents)
        assert "<script>Agent</script>" not in html
        assert "&lt;script&gt;" in html
        assert "Test &amp; Description" in html

    def test_render_index_empty_agents(self):
        html = _render_index([])
        assert "0 agents" in html or "0" in html


class TestRenderAgent:
    """Tests for individual agent page rendering."""

    def test_render_agent_basic(self):
        agent = {
            "id": "test-agent",
            "name": "Test Agent",
            "description": "A test agent for testing",
            "category": "rag",
            "frameworks": ["langchain", "llamaindex"],
            "llm_providers": ["openai", "anthropic"],
            "complexity": "intermediate",
            "github_url": "https://github.com/user/repo",
            "codespaces_url": "https://codespaces.new/user/repo",
            "colab_url": "https://colab.research.google.com/...",
            "api_keys": ["OPENAI_API_KEY"],
            "quick_start": "pip install",
            "clone_command": "git clone repo",
            "stars": 1234,
            "updated_at": 1609459200,
        }
        html = _render_agent(agent, base_url="https://example.com")
        assert "Test Agent" in html
        assert "A test agent for testing" in html
        assert "langchain, llamaindex" in html
        assert "openai, anthropic" in html
        assert "1234" in html
        assert "2021-01-01" in html

    def test_render_agent_html_escaping(self):
        agent = {
            "id": "test",
            "name": "<Test>Agent</Test>",
            "description": "Test & 'quotes'",
            "category": "other",
            "frameworks": [],
            "llm_providers": [],
            "complexity": "intermediate",
            "github_url": "https://github.com/user/repo",
            "api_keys": [],
            "quick_start": "",
            "clone_command": "",
        }
        html = _render_agent(agent, base_url=None)
        assert "<Test>Agent</Test>" not in html
        assert "Test &amp; &#x27;quotes&#x27;" in html or "Test &amp; 'quotes'" in html

    def test_render_agent_without_optional_fields(self):
        agent = {
            "id": "test",
            "name": "Minimal Agent",
            "description": "Minimal",
            "category": "other",
            "frameworks": [],
            "llm_providers": [],
            "complexity": "beginner",
            "github_url": "",
            "api_keys": [],
            "quick_start": "",
            "clone_command": "",
            "stars": None,
            "updated_at": None,
            "codespaces_url": None,
            "colab_url": None,
        }
        html = _render_agent(agent, base_url=None)
        assert "Minimal Agent" in html
        # Should show placeholders or empty values
        assert "—" in html  # Dash for empty values

    def test_render_agent_with_base_url(self):
        agent = {
            "id": "test",
            "name": "Test",
            "description": "Test",
            "category": "other",
            "frameworks": [],
            "llm_providers": [],
            "github_url": "",
            "api_keys": [],
            "quick_start": "",
            "clone_command": "",
        }
        html = _render_agent(agent, base_url="https://example.com")
        assert "canonical" in html.lower()
        assert "https://example.com/agents/test/" in html

    def test_render_agent_without_base_url(self):
        agent = {
            "id": "test",
            "name": "Test",
            "description": "Test",
            "category": "other",
            "frameworks": [],
            "llm_providers": [],
            "github_url": "",
            "api_keys": [],
            "quick_start": "",
            "clone_command": "",
        }
        html = _render_agent(agent, base_url=None)
        assert "canonical" not in html.lower()


class TestRenderAssets:
    """Tests for asset file generation."""

    def test_render_css(self, tmp_path: Path):
        _render_assets(tmp_path)
        css_file = tmp_path / "assets" / "style.css"
        assert css_file.exists()
        css_content = css_file.read_text(encoding="utf-8")
        assert ":root" in css_content
        assert "background:" in css_content or "background:" in css_content

    def test_render_js(self, tmp_path: Path):
        _render_assets(tmp_path)
        js_file = tmp_path / "assets" / "app.js"
        assert js_file.exists()
        js_content = js_file.read_text(encoding="utf-8")
        assert "getElementById" in js_content
        assert "addEventListener" in js_content

    def test_render_creates_assets_dir(self, tmp_path: Path):
        _render_assets(tmp_path)
        assert (tmp_path / "assets").exists()
        assert (tmp_path / "assets").is_dir()


class TestRenderSitemap:
    """Tests for sitemap and robots.txt generation."""

    def test_render_sitemap(self, tmp_path: Path):
        agents = [
            {"id": "agent1", "name": "Agent 1"},
            {"id": "agent2", "name": "Agent 2"},
        ]
        _render_sitemap(tmp_path, agents, base_url="https://example.com")

        sitemap = tmp_path / "sitemap.xml"
        assert sitemap.exists()
        sitemap_content = sitemap.read_text(encoding="utf-8")
        assert "<?xml version=" in sitemap_content
        assert "https://example.com/" in sitemap_content
        assert "https://example.com/agents/agent1/" in sitemap_content
        assert "https://example.com/agents/agent2/" in sitemap_content

    def test_render_robots_txt(self, tmp_path: Path):
        agents = [{"id": "test", "name": "Test"}]
        _render_sitemap(tmp_path, agents, base_url="https://example.com")

        robots = tmp_path / "robots.txt"
        assert robots.exists()
        robots_content = robots.read_text(encoding="utf-8")
        assert "User-agent:" in robots_content
        assert "Sitemap:" in robots_content
        assert "https://example.com/sitemap.xml" in robots_content


class TestExportSite:
    """Tests for full site export."""

    def test_export_site_creates_index(self, tmp_path: Path):
        data_path = tmp_path / "agents.json"
        data_path.write_text('[{"id": "test", "name": "Test", "description": "Test", "category": "other", "frameworks": [], "llm_providers": [], "github_url": ""}]', encoding="utf-8")

        output_dir = tmp_path / "site"
        export_site(data_path, output_dir, base_url="https://example.com")

        assert (output_dir / "index.html").exists()
        assert (output_dir / "404.html").exists()
        assert (output_dir / "_headers").exists()

    def test_export_site_creates_agent_pages(self, tmp_path: Path):
        data_path = tmp_path / "agents.json"
        data_path.write_text(json.dumps([
            {"id": "agent1", "name": "Agent 1", "description": "Test", "category": "other", "frameworks": [], "llm_providers": [], "github_url": ""},
            {"id": "agent2", "name": "Agent 2", "description": "Test", "category": "other", "frameworks": [], "llm_providers": [], "github_url": ""},
        ]), encoding="utf-8")

        output_dir = tmp_path / "site"
        export_site(data_path, output_dir, base_url="https://example.com")

        assert (output_dir / "agents" / "agent1" / "index.html").exists()
        assert (output_dir / "agents" / "agent2" / "index.html").exists()

    def test_export_site_creates_assets(self, tmp_path: Path):
        data_path = tmp_path / "agents.json"
        data_path.write_text('[{"id": "test", "name": "Test", "description": "Test", "category": "other", "frameworks": [], "llm_providers": [], "github_url": ""}]', encoding="utf-8")

        output_dir = tmp_path / "site"
        export_site(data_path, output_dir, base_url="https://example.com")

        assert (output_dir / "assets" / "style.css").exists()
        assert (output_dir / "assets" / "app.js").exists()

    def test_export_site_creates_sitemap_with_base_url(self, tmp_path: Path):
        data_path = tmp_path / "agents.json"
        data_path.write_text('[{"id": "test", "name": "Test", "description": "Test", "category": "other", "frameworks": [], "llm_providers": [], "github_url": ""}]', encoding="utf-8")

        output_dir = tmp_path / "site"
        export_site(data_path, output_dir, base_url="https://example.com")

        assert (output_dir / "sitemap.xml").exists()
        assert (output_dir / "robots.txt").exists()

    def test_export_site_no_sitemap_without_base_url(self, tmp_path: Path):
        data_path = tmp_path / "agents.json"
        data_path.write_text('[{"id": "test", "name": "Test", "description": "Test", "category": "other", "frameworks": [], "llm_providers": [], "github_url": ""}]', encoding="utf-8")

        output_dir = tmp_path / "site"
        export_site(data_path, output_dir, base_url=None)

        assert not (output_dir / "sitemap.xml").exists()
        assert not (output_dir / "robots.txt").exists()
        assert (output_dir / "404.html").exists()
        assert (output_dir / "_headers").exists()

    def test_export_site_sorts_by_name(self, tmp_path: Path):
        data_path = tmp_path / "agents.json"
        data_path.write_text(json.dumps([
            {"id": "z", "name": "Z Agent", "description": "Test", "category": "other", "frameworks": [], "llm_providers": [], "github_url": ""},
            {"id": "a", "name": "A Agent", "description": "Test", "category": "other", "frameworks": [], "llm_providers": [], "github_url": ""},
            {"id": "m", "name": "M Agent", "description": "Test", "category": "other", "frameworks": [], "llm_providers": [], "github_url": ""},
        ]), encoding="utf-8")

        output_dir = tmp_path / "site"
        export_site(data_path, output_dir, base_url="https://example.com")

        index_html = (output_dir / "index.html").read_text(encoding="utf-8")
        # A should appear before Z
        a_pos = index_html.find("A Agent")
        z_pos = index_html.find("Z Agent")
        assert a_pos < z_pos

    def test_export_site_creates_additional_pseo_pages(self, tmp_path: Path):
        data_path = tmp_path / "agents.json"
        data_path.write_text(
            json.dumps(
                [
                    {
                        "id": "rag_langchain_openai",
                        "name": "RAG LangChain OpenAI",
                        "description": "RAG example using Pinecone and function calling tools.",
                        "category": "rag",
                        "frameworks": ["langchain"],
                        "llm_providers": ["openai"],
                        "design_pattern": "rag_patterns",
                        "supports_local_models": False,
                        "stars": 123,
                        "github_url": "",
                    },
                    {
                        "id": "voice_whisper_agent",
                        "name": "Voice Agent with Whisper",
                        "description": "Speech-to-text voice assistant using Whisper.",
                        "category": "voice",
                        "frameworks": ["raw_api"],
                        "llm_providers": ["openai"],
                        "design_pattern": "other",
                        "supports_local_models": False,
                        "stars": 50,
                        "github_url": "",
                    },
                    {
                        "id": "crewai_local",
                        "name": "CrewAI Local Automation",
                        "description": "Workflow automation with CrewAI and Ollama local models.",
                        "category": "automation",
                        "frameworks": ["crewai"],
                        "llm_providers": ["ollama", "local"],
                        "design_pattern": "tool_use",
                        "supports_local_models": True,
                        "stars": 77,
                        "github_url": "",
                    },
                ]
            ),
            encoding="utf-8",
        )

        output_dir = tmp_path / "site"
        export_site(data_path, output_dir, base_url="https://example.com")

        assert (output_dir / "rag-patterns" / "index.html").exists()
        assert (output_dir / "best-rag-agents-2025" / "index.html").exists()
        assert (output_dir / "customer-support-agents" / "index.html").exists()
        assert (output_dir / "langchain-with-openai" / "index.html").exists()
        assert (output_dir / "voice-agents-with-whisper" / "index.html").exists()

        sitemap = (output_dir / "sitemap.xml").read_text(encoding="utf-8")
        assert "https://example.com/rag-patterns/" in sitemap
        assert "https://example.com/best-rag-agents-2025/" in sitemap
        assert "https://example.com/langchain-with-openai/" in sitemap
        assert "https://example.com/voice-agents-with-whisper/" in sitemap


class TestEdgeCases:
    """Edge case tests."""

    def test_unicode_in_agent_data(self, tmp_path: Path):
        data_path = tmp_path / "agents.json"
        data_path.write_text(json.dumps([{
            "id": "test",
            "name": "Test Agent 世界",
            "description": "Test with emoji 🚀",
            "category": "other",
            "frameworks": [],
            "llm_providers": [],
            "github_url": "",
        }]), encoding="utf-8")

        output_dir = tmp_path / "site"
        export_site(data_path, output_dir, base_url="https://example.com")

        index_html = (output_dir / "index.html").read_text(encoding="utf-8")
        assert "世界" in index_html
        assert "🚀" in index_html

    def test_very_long_description(self, tmp_path: Path):
        data_path = tmp_path / "agents.json"
        data_path.write_text(json.dumps([{
            "id": "test",
            "name": "Test",
            "description": "x" * 500,
            "category": "other",
            "frameworks": [],
            "llm_providers": [],
            "github_url": "",
        }]), encoding="utf-8")

        output_dir = tmp_path / "site"
        export_site(data_path, output_dir, base_url="https://example.com")

        index_html = (output_dir / "index.html").read_text(encoding="utf-8")
        assert "xxx" in index_html  # Description present

    def test_empty_agents_list(self, tmp_path: Path):
        data_path = tmp_path / "agents.json"
        data_path.write_text("[]", encoding="utf-8")

        output_dir = tmp_path / "site"
        export_site(data_path, output_dir, base_url="https://example.com")

        assert (output_dir / "index.html").exists()
        assert not (output_dir / "agents").exists()  # No agents, no agent dir

    def test_special_chars_in_id(self, tmp_path: Path):
        data_path = tmp_path / "agents.json"
        data_path.write_text('[{"id": "test with spaces!", "name": "Test", "description": "Test", "category": "other", "frameworks": [], "llm_providers": [], "github_url": ""}]', encoding="utf-8")

        output_dir = tmp_path / "site"
        export_site(data_path, output_dir, base_url="https://example.com")

        # Slug should sanitize ID
        agent_dir = output_dir / "agents" / "test-with-spaces"
        assert agent_dir.exists()

    def test_xss_injection_attempt(self, tmp_path: Path):
        data_path = tmp_path / "agents.json"
        data_path.write_text(json.dumps([{
            "id": "test",
            "name": "<script>alert('xss')</script>",
            "description": "<img src=x onerror=alert('xss')>",
            "category": "other",
            "frameworks": [],
            "llm_providers": [],
            "github_url": "",
        }]), encoding="utf-8")

        output_dir = tmp_path / "site"
        export_site(data_path, output_dir, base_url="https://example.com")

        index_html = (output_dir / "index.html").read_text(encoding="utf-8")
        # Should be escaped - script tags should be escaped
        assert "<script>alert" not in index_html
        # The onerror should appear within escaped content (harmless)
        assert "&lt;script&gt;" in index_html
        # Check that the description is properly escaped (html.escape uses &#x27; for single quotes)
        assert "&lt;img src=x onerror=alert(&#x27;xss&#x27;)&gt;" in index_html

    def test_duplicate_ids(self, tmp_path: Path):
        data_path = tmp_path / "agents.json"
        data_path.write_text(json.dumps([
            {"id": "duplicate", "name": "First", "description": "Test", "category": "other", "frameworks": [], "llm_providers": [], "github_url": ""},
            {"id": "duplicate", "name": "Second", "description": "Test", "category": "other", "frameworks": [], "llm_providers": [], "github_url": ""},
        ]), encoding="utf-8")

        output_dir = tmp_path / "site"
        export_site(data_path, output_dir, base_url="https://example.com")

        # Both should be written (last one wins or both coexist)
        assert (output_dir / "agents" / "duplicate" / "index.html").exists()
