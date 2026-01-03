"""
Tests for src.domain module.

Covers:
- GitHub URL parsing and manipulation
- Readme URL generation
- Markdown link rewriting
- Mermaid diagram building and sanitization
- Similarity scoring and recommendations
- Agent record normalization
- Complexity ranking and time estimation
"""

import pytest

from src import domain
from src.config import CATEGORY_ICONS


class TestComplexityRank:
    """Tests for complexity ranking function."""

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("beginner", 0),
            ("intermediate", 1),
            ("advanced", 2),
            ("BEGINNER", 0),
            ("Intermediate", 1),
            ("ADVANCED", 2),
            ("unknown", 99),
            ("", 99),
            (None, 99),
        ],
    )
    def test_complexity_rank(self, value: str, expected: int):
        assert domain.complexity_rank(value) == expected


class TestEstimateSetupTime:
    """Tests for setup time estimation."""

    @pytest.mark.parametrize(
        ("complexity", "expected"),
        [
            ("beginner", "10–20 min"),
            ("intermediate", "20–45 min"),
            ("advanced", "45–90+ min"),
            ("BEGINNER", "10–20 min"),
            ("unknown", "Varies"),
            ("", "Varies"),
            (None, "Varies"),
        ],
    )
    def test_estimate_setup_time(self, complexity: str, expected: str):
        assert domain.estimate_setup_time(complexity) == expected


class TestParseGithubTreeUrl:
    """Tests for GitHub tree URL parsing."""

    @pytest.mark.parametrize(
        ("url", "expected"),
        [
            ("https://github.com/user/repo/tree/main/path", ("user", "repo", "main")),
            ("https://github.com/foo/bar/tree/develop/sub/path", ("foo", "bar", "develop")),
            ("https://notgithub.com/user/repo", None),
            ("", None),
            (None, None),
            ("https://github.com/user/repo/blob/main/file.py", None),  # blob, not tree
        ],
    )
    def test_parse_github_tree_url(self, url: str, expected: tuple[str, str, str] | None):
        result = domain.parse_github_tree_url(url)
        assert result == expected


class TestRawReadmeUrl:
    """Tests for raw README URL generation."""

    def test_raw_readme_url_from_github_url(self):
        agent = {
            "github_url": "https://github.com/foo/bar/tree/main/some/path",
            "folder_path": "some/path",
            "readme_relpath": "some/path/README.md",
        }
        url = domain.raw_readme_url(agent)
        assert url == "https://raw.githubusercontent.com/foo/bar/main/some/path/README.md"

    def test_raw_readme_url_with_custom_defaults(self):
        agent = {
            "folder_path": "custom/path",
            "readme_relpath": "custom/path/README.md",
        }
        url = domain.raw_readme_url(
            agent,
            default_owner="custom_owner",
            default_repo="custom_repo",
            default_branch="develop",
        )
        assert url == "https://raw.githubusercontent.com/custom_owner/custom_repo/develop/custom/path/README.md"

    def test_raw_readme_url_generates_from_folder_path(self):
        agent = {
            "folder_path": "my_agent",
            "readme_relpath": "",
        }
        url = domain.raw_readme_url(agent)
        assert url == "https://raw.githubusercontent.com/Shubhamsaboo/awesome-llm-apps/main/my_agent/README.md"

    def test_raw_readme_url_with_missing_paths(self):
        agent = {}
        url = domain.raw_readme_url(agent)
        assert url is None


class TestRewriteRelativeLinks:
    """Tests for markdown link rewriting."""

    def test_rewrite_image_links(self):
        agent = {
            "github_url": "https://github.com/foo/bar/tree/main/some/path",
            "folder_path": "some/path",
        }
        md = "See ![image](./image.png) here."
        result = domain.rewrite_relative_links(md, agent)
        assert "raw.githubusercontent.com/foo/bar/main/some/path/image.png" in result

    def test_rewrite_markdown_links(self):
        agent = {
            "github_url": "https://github.com/foo/bar/tree/main/some/path",
            "folder_path": "some/path",
        }
        md = "See [doc](README.md) for info."
        result = domain.rewrite_relative_links(md, agent)
        assert "raw.githubusercontent.com/foo/bar/main/some/path/README.md" in result

    def test_rewrite_preserves_absolute_links(self):
        agent = {
            "github_url": "https://github.com/foo/bar/tree/main/path",
            "folder_path": "path",
        }
        md = "Visit [https://example.com](https://example.com)"
        result = domain.rewrite_relative_links(md, agent)
        assert "https://example.com" in result

    def test_rewrite_preserves_anchor_links(self):
        agent = {
            "github_url": "https://github.com/foo/bar/tree/main/path",
            "folder_path": "path",
        }
        md = "[Section](#section)"
        result = domain.rewrite_relative_links(md, agent)
        assert "(#section)" in result

    def test_rewrite_handles_parent_directory_links(self):
        agent = {
            "github_url": "https://github.com/foo/bar/tree/main/nested/path",
            "folder_path": "nested/path",
        }
        md = "[Parent](../parent.md)"
        result = domain.rewrite_relative_links(md, agent)
        assert "raw.githubusercontent.com" in result
        assert "parent.md" in result

    def test_rewrite_with_custom_branch(self):
        agent = {
            "github_url": "https://github.com/foo/bar/tree/main/path",
            "folder_path": "path",
        }
        md = "[Doc](./doc.md)"
        result = domain.rewrite_relative_links(md, agent, default_branch="develop")
        assert "/develop/" in result

    def test_rewrite_handles_root_relative_links(self):
        agent = {
            "github_url": "https://github.com/foo/bar/tree/main/nested/path",
            "folder_path": "nested/path",
        }
        md = "[Root](/README.md)"
        result = domain.rewrite_relative_links(md, agent)
        assert "raw.githubusercontent.com/foo/bar/main/README.md" in result


class TestSafeMermaidLabel:
    """Tests for Mermaid label sanitization."""

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("Simple Label", "Simple Label"),
            ("Label<script>", "Label"),
            ("Label</div>Test", "LabelTest"),
            ("Label with - and _", "Label with - and _"),
            ("Label!@#$%^&*()", "Label"),
            ("", "Other"),
            (None, "Other"),
        ],
    )
    def test_safe_mermaid_label(self, value: str | None, expected: str):
        result = domain.safe_mermaid_label(value)
        assert result == expected

    def test_safe_mermaid_label_length_limit(self):
        long_label = "a" * 100
        result = domain.safe_mermaid_label(long_label)
        assert len(result) <= 40


class TestBuildAgentDiagram:
    """Tests for agent diagram generation."""

    def test_diagram_structure(self):
        agent = {
            "frameworks": ["langchain"],
            "llm_providers": ["openai"],
            "design_pattern": "rag",
        }
        diagram = domain.build_agent_diagram(agent)
        assert "graph LR" in diagram
        assert "User" in diagram
        assert "Streamlit" in diagram
        assert "Rag" in diagram
        assert "Langchain" in diagram
        assert "OPENAI" in diagram

    def test_diagram_sanitizes_inputs(self):
        agent = {
            "frameworks": ["langchain<script>"],
            "llm_providers": ["openai</div>"],
            "design_pattern": "rag</script>",
        }
        diagram = domain.build_agent_diagram(agent)
        assert "<script>" not in diagram
        assert "</div>" not in diagram
        assert "Langchain" in diagram

    def test_diagram_handles_empty_frameworks(self):
        agent = {
            "frameworks": [],
            "llm_providers": [],
            "design_pattern": "other",
        }
        diagram = domain.build_agent_diagram(agent)
        assert "App" in diagram
        assert "LLM" in diagram

    def test_diagram_title_cases_framework(self):
        agent = {
            "frameworks": ["langchain"],
            "llm_providers": ["openai"],
            "design_pattern": "rag",
        }
        diagram = domain.build_agent_diagram(agent)
        assert "Langchain" in diagram

    def test_diagram_uppercases_provider(self):
        agent = {
            "frameworks": ["langchain"],
            "llm_providers": ["openai"],
            "design_pattern": "rag",
        }
        diagram = domain.build_agent_diagram(agent)
        assert "OPENAI" in diagram

    def test_diagram_formats_design_pattern(self):
        agent = {
            "frameworks": ["langchain"],
            "llm_providers": ["openai"],
            "design_pattern": "plan_and_execute",
        }
        diagram = domain.build_agent_diagram(agent)
        assert "Plan And Execute" in diagram


class TestRecommendSimilar:
    """Tests for similarity-based agent recommendations."""

    def test_recommends_similar_agents(self):
        base = {
            "id": "a",
            "category": "rag",
            "frameworks": ["langchain"],
            "llm_providers": ["openai"],
            "design_pattern": "rag",
        }
        b = {
            "id": "b",
            "category": "rag",
            "frameworks": ["langchain"],
            "llm_providers": ["openai"],
            "design_pattern": "rag",
        }
        c = {
            "id": "c",
            "category": "finance",
            "frameworks": ["crewai"],
            "llm_providers": ["anthropic"],
            "design_pattern": "tool_use",
        }
        out = domain.recommend_similar(base, [base, c, b], limit=2)
        assert len(out) <= 2
        assert out[0]["id"] == "b"  # Most similar

    def test_recommends_with_partial_overlap(self):
        base = {
            "id": "base",
            "category": "rag",
            "frameworks": ["langchain", "llamaindex"],
            "llm_providers": ["openai"],
            "design_pattern": "rag",
        }
        similar1 = {
            "id": "sim1",
            "category": "chatbot",
            "frameworks": ["langchain"],
            "llm_providers": ["openai"],
            "design_pattern": "simple_chat",
        }
        similar2 = {
            "id": "sim2",
            "category": "vision",
            "frameworks": ["crewai"],
            "llm_providers": ["anthropic"],
            "design_pattern": "tool_use",
        }
        out = domain.recommend_similar(base, [similar1, similar2], limit=5)
        # similar1 should rank higher due to langchain + openai overlap
        assert out[0]["id"] == "sim1"

    def test_recommends_excludes_base_agent(self):
        base = {
            "id": "a",
            "category": "rag",
            "frameworks": ["langchain"],
            "llm_providers": ["openai"],
            "design_pattern": "rag",
        }
        out = domain.recommend_similar(base, [base], limit=5)
        assert len(out) == 0  # Base agent excluded

    def test_recommends_respects_limit(self):
        base = {
            "id": "a",
            "category": "rag",
            "frameworks": ["langchain"],
            "llm_providers": ["openai"],
            "design_pattern": "rag",
        }
        others = [
            {
                "id": f"agent{i}",
                "category": "rag",
                "frameworks": ["langchain"],
                "llm_providers": ["openai"],
                "design_pattern": "rag",
            }
            for i in range(10)
        ]
        out = domain.recommend_similar(base, others, limit=3)
        assert len(out) <= 3

    def test_recommends_handles_missing_fields(self):
        base = {"id": "a", "category": "rag"}
        other = {"id": "b", "category": "rag"}
        out = domain.recommend_similar(base, [other], limit=5)
        # Should not crash
        assert isinstance(out, list)

    def test_recommands_with_zero_overlap(self):
        base = {
            "id": "a",
            "category": "rag",
            "frameworks": ["langchain"],
            "llm_providers": ["openai"],
            "design_pattern": "rag",
        }
        different = {
            "id": "b",
            "category": "chatbot",
            "frameworks": ["crewai"],
            "llm_providers": ["anthropic"],
            "design_pattern": "simple_chat",
        }
        out = domain.recommend_similar(base, [different], limit=5)
        # May or may not return results depending on threshold
        assert isinstance(out, list)

    def test_recommends_sorts_by_name_for_ties(self):
        base = {
            "id": "base",
            "category": "rag",
            "frameworks": ["langchain"],
            "llm_providers": ["openai"],
            "design_pattern": "rag",
        }
        z_agent = {
            "id": "z",
            "name": "Z Agent",
            "category": "rag",
            "frameworks": ["langchain"],
            "llm_providers": ["openai"],
            "design_pattern": "rag",
        }
        a_agent = {
            "id": "a",
            "name": "A Agent",
            "category": "rag",
            "frameworks": ["langchain"],
            "llm_providers": ["openai"],
            "design_pattern": "rag",
        }
        out = domain.recommend_similar(base, [z_agent, a_agent], limit=5)
        # Both have same overlap, should sort by name
        assert out[0]["id"] == "a"


class TestNormalizeAgentRecord:
    """Tests for agent record normalization."""

    def test_normalize_adds_defaults(self):
        agent = {"id": "test"}
        normalized = domain.normalize_agent_record(agent, source_repo_url="https://github.com/user/repo")
        assert normalized["frameworks"] == []
        assert normalized["llm_providers"] == []
        assert normalized["category"] == "other"
        assert normalized["complexity"] == "intermediate"

    def test_normalize_preserves_existing_fields(self):
        agent = {
            "id": "test",
            "name": "Test Agent",
            "category": "rag",
            "frameworks": ["langchain"],
        }
        normalized = domain.normalize_agent_record(agent, source_repo_url="https://github.com/user/repo")
        assert normalized["name"] == "Test Agent"
        assert normalized["category"] == "rag"
        assert normalized["frameworks"] == ["langchain"]

    def test_normalize_generates_clone_command(self):
        agent = {
            "id": "test",
            "folder_path": "path/to/agent",
        }
        normalized = domain.normalize_agent_record(agent, source_repo_url="https://github.com/user/repo.git")
        assert "git clone" in normalized["clone_command"]
        assert "path/to/agent" in normalized["clone_command"]

    def test_normalize_generates_readme_relpath(self):
        agent = {
            "id": "test",
            "folder_path": "my_agent",
        }
        normalized = domain.normalize_agent_record(agent, source_repo_url="https://github.com/user/repo")
        assert normalized["readme_relpath"] == "my_agent/README.md"

    def test_normalize_uses_readme_path(self):
        agent = {
            "id": "test",
            "readme_path": "custom/path.md",
        }
        normalized = domain.normalize_agent_record(agent, source_repo_url="https://github.com/user/repo")
        assert normalized["folder_path"] == "custom/path.md"

    def test_normalize_preserves_clone_command(self):
        agent = {
            "id": "test",
            "clone_command": "custom clone command",
        }
        normalized = domain.normalize_agent_record(agent, source_repo_url="https://github.com/user/repo")
        assert normalized["clone_command"] == "custom clone command"

    def test_normalize_does_not_modify_original(self):
        agent = {"id": "test"}
        original_id = id(agent)
        normalized = domain.normalize_agent_record(agent, source_repo_url="https://github.com/user/repo")
        assert id(normalized) != original_id
        assert "frameworks" not in agent  # Original unchanged

    def test_normalize_with_none_values(self):
        agent = {
            "id": "test",
            "name": None,
            "category": None,
        }
        normalized = domain.normalize_agent_record(agent, source_repo_url="https://github.com/user/repo")
        assert normalized["name"] is None
        assert normalized["category"] == "other"  # Default applied


class TestCategoryIcons:
    """Tests for category icon mapping."""

    def test_all_categories_have_icons(self):
        for _category, icon in CATEGORY_ICONS.items():
            assert isinstance(icon, str)
            assert len(icon) > 0

    def test_expected_categories_present(self):
        expected = [
            "rag",
            "chatbot",
            "agent",
            "multi_agent",
            "automation",
            "search",
            "vision",
            "voice",
            "coding",
            "finance",
            "research",
            "other",
        ]
        for cat in expected:
            assert cat in CATEGORY_ICONS


class TestEdgeCases:
    """Edge case tests."""

    def test_rewrite_empty_markdown(self):
        agent = {"github_url": "https://github.com/user/repo", "folder_path": "path"}
        result = domain.rewrite_relative_links("", agent)
        assert result == ""

    def test_rewrite_markdown_with_no_links(self):
        agent = {"github_url": "https://github.com/user/repo", "folder_path": "path"}
        md = "Just some text with no links"
        result = domain.rewrite_relative_links(md, agent)
        assert result == md

    def test_diagram_with_unicode_pattern(self):
        agent = {
            "frameworks": ["langchain"],
            "llm_providers": ["openai"],
            "design_pattern": "rag_世界",
        }
        diagram = domain.build_agent_diagram(agent)
        # Should handle unicode gracefully
        assert isinstance(diagram, str)

    def test_recommend_with_empty_agents_list(self):
        base = {"id": "a", "category": "rag"}
        out = domain.recommend_similar(base, [], limit=5)
        assert out == []

    def test_normalize_with_empty_strings(self):
        agent = {"id": "", "name": "", "category": ""}
        normalized = domain.normalize_agent_record(agent, source_repo_url="https://github.com/user/repo")
        assert normalized["id"] == ""  # Preserved
        assert normalized["category"] == "other"  # Default for empty category

    def test_parse_malformed_github_urls(self):
        urls = [
            "github.com/user/repo",
            "https://github.com/user",
            "https://github.com/user/repo/tree/",
            "ftp://github.com/user/repo",
        ]
        for url in urls:
            result = domain.parse_github_tree_url(url)
            assert result is None
