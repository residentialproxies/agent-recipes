"""
Tests for src.indexer module.

Covers:
- LLM extraction with proper mocking
- Heuristic extraction logic
- Content hashing and caching
- Language detection
- Quick start extraction
- URL generation
- GitHub API integration (mocked)
- RepoIndexer class functionality
"""

import json
from pathlib import Path
from typing import Any, Dict
from unittest.mock import Mock, MagicMock, patch

import pytest

from src.indexer import (
    _content_hash,
    _safe_title_from_path,
    _tokenize_for_tags,
    _detect_languages,
    _extract_quick_start,
    _heuristic_extract,
    _normalize_llm_output,
    _git_last_modified_ts,
    _parse_github_owner_repo,
    _fetch_github_repo_stars,
    AgentMetadata,
    RepoIndexer,
    CATEGORIES,
    FRAMEWORKS,
    LLM_PROVIDERS,
    API_KEY_NAMES,
)


class TestContentHash:
    """Tests for content hash generation."""

    def test_content_hash_is_stable(self):
        content = "test content"
        hash1 = _content_hash(content)
        hash2 = _content_hash(content)
        assert hash1 == hash2
        assert len(hash1) == 12

    def test_content_hash_differs_for_different_content(self):
        hash1 = _content_hash("content one")
        hash2 = _content_hash("content two")
        assert hash1 != hash2

    def test_content_hash_handles_unicode(self):
        hash1 = _content_hash("Hello 世界")
        hash2 = _content_hash("Hello 世界")
        assert hash1 == hash2

    def test_content_hash_handles_errors_gracefully(self):
        # Should not crash on problematic content
        result = _content_hash("test\x00content")
        assert len(result) == 12


class TestSafeTitleFromPath:
    """Tests for title extraction from folder path."""

    @pytest.mark.parametrize(
        ("path", "expected"),
        [
            ("simple-agent", "Simple Agent"),
            ("my_agent", "My Agent"),
            ("AnotherTest", "Anothertest"),
            ("multi-word-path", "Multi Word Path"),
            ("", "Untitled"),
        ],
    )
    def test_safe_title_from_path(self, path: str, expected: str):
        assert _safe_title_from_path(path) == expected


class TestTokenizeForTags:
    """Tests for tag tokenization."""

    def test_tokenize_extracts_meaningful_tokens(self):
        text = "RAG chatbot with LangChain and OpenAI"
        tokens = _tokenize_for_tags(text)
        assert "rag" in tokens
        assert "chatbot" in tokens
        assert "langchain" in tokens
        assert "openai" in tokens

    def test_tokenize_filters_short_tokens(self):
        text = "a an the in on at ai ml"
        tokens = _tokenize_for_tags(text)
        assert "ai" in tokens
        assert "ml" in tokens
        # Short tokens should be filtered
        assert "a" not in tokens
        assert "an" not in tokens

    def test_tokenize_handles_special_chars(self):
        text = "hello-world! test@example.com"
        tokens = _tokenize_for_tags(text)
        assert "hello" in tokens or "world" in tokens
        assert "test" in tokens or "example" in tokens

    def test_tokenize_limits_length(self):
        text = "word " * 100
        tokens = _tokenize_for_tags(text)
        assert len(tokens) <= 80


class TestDetectLanguages:
    """Tests for programming language detection."""

    def test_detect_python_files(self, tmp_path: Path):
        (tmp_path / "main.py").write_text("print('hello')")
        (tmp_path / "utils.py").write_text("def foo(): pass")
        langs = _detect_languages(tmp_path)
        assert "python" in langs

    def test_detect_javascript_typescript(self, tmp_path: Path):
        (tmp_path / "app.js").write_text("console.log('test')")
        (tmp_path / "utils.ts").write_text("const x: number = 1")
        langs = _detect_languages(tmp_path)
        assert "javascript" in langs
        assert "typescript" in langs

    def test_detect_jupyter_notebooks(self, tmp_path: Path):
        (tmp_path / "notebook.ipynb").write_text('{"cells": []}')
        langs = _detect_languages(tmp_path)
        assert "python" in langs

    def test_detect_multiple_languages(self, tmp_path: Path):
        (tmp_path / "main.py").write_text("print('test')")
        (tmp_path / "app.js").write_text("console.log('test')")
        (tmp_path / "lib.go").write_text("package main")
        langs = _detect_languages(tmp_path)
        assert len(langs) >= 3
        assert "python" in langs
        assert "javascript" in langs
        assert "go" in langs

    def test_detect_returns_top_three(self, tmp_path: Path):
        for i in range(5):
            (tmp_path / f"file{i}.py").write_text("print('test')")
        for i in range(3):
            (tmp_path / f"js{i}.js").write_text("console.log('test')")
        for i in range(2):
            (tmp_path / f"go{i}.go").write_text("package main")

        langs = _detect_languages(tmp_path)
        assert len(langs) <= 3
        assert langs[0] == "python"  # Most frequent


class TestExtractQuickStart:
    """Tests for quick start command extraction."""

    def test_extract_finds_code_blocks(self):
        readme = """
# Title

Some description.

```bash
pip install -r requirements.txt
streamlit run app.py
```

More content.
"""
        result = _extract_quick_start(readme, "my_agent")
        assert "pip install" in result
        assert "streamlit run" in result

    def test_extract_prefers_explicit_commands(self):
        readme = """
```bash
npm install
npm start
```

```text
some other text
```
"""
        result = _extract_quick_start(readme, "agent")
        assert "npm install" in result

    def test_extract_fallback_to_clone_hint(self):
        readme = "No code blocks here."
        result = _extract_quick_start(readme, "path/to/agent")
        assert "cd path/to/agent" in result or "cd path" in result

    def test_extract_limits_length(self):
        readme = "\n".join([f"line {i}" for i in range(1000)])
        result = _extract_quick_start(readme, "agent")
        assert len(result) <= 800


class TestHeuristicExtract:
    """Tests for heuristic metadata extraction."""

    def test_detects_rag_category(self, tmp_path: Path):
        readme = "This is a RAG system with vector embeddings."
        (tmp_path / "main.py").write_text("print('test')")
        result = _heuristic_extract(readme, "rag_agent", tmp_path)
        assert result["category"] == "rag"
        assert result["design_pattern"] == "rag"

    def test_detects_chatbot_category(self, tmp_path: Path):
        readme = "A chatbot for customer support."
        (tmp_path / "app.py").write_text("print('test')")
        result = _heuristic_extract(readme, "chatbot", tmp_path)
        assert result["category"] == "chatbot"

    def test_detects_multi_agent_category(self, tmp_path: Path):
        readme = "Multi-agent system with autonomous agents."
        (tmp_path / "main.py").write_text("print('test')")
        result = _heuristic_extract(readme, "multi_agent", tmp_path)
        assert result["category"] == "multi_agent"

    def test_detects_frameworks(self, tmp_path: Path):
        readme = "Built with LangChain and LlamaIndex."
        (tmp_path / "app.py").write_text("print('test')")
        result = _heuristic_extract(readme, "agent", tmp_path)
        assert "langchain" in result["frameworks"]
        assert "llamaindex" in result["frameworks"]

    def test_detects_llm_providers(self, tmp_path: Path):
        readme = "Uses OpenAI GPT-4 and Anthropic Claude."
        (tmp_path / "app.py").write_text("print('test')")
        result = _heuristic_extract(readme, "agent", tmp_path)
        assert "openai" in result["llm_providers"]
        assert "anthropic" in result["llm_providers"]

    def test_detects_local_models(self, tmp_path: Path):
        readme = "Run locally with Ollama and GGUF models."
        (tmp_path / "app.py").write_text("print('test')")
        result = _heuristic_extract(readme, "agent", tmp_path)
        assert result["supports_local_models"] is True

    def test_detects_gpu_requirement(self, tmp_path: Path):
        readme = "Requires NVIDIA GPU with CUDA support."
        (tmp_path / "app.py").write_text("print('test')")
        result = _heuristic_extract(readme, "agent", tmp_path)
        assert result["requires_gpu"] is True

    def test_detects_api_keys(self, tmp_path: Path):
        readme = "Set OPENAI_API_KEY and ANTHROPIC_API_KEY environment variables."
        (tmp_path / "app.py").write_text("print('test')")
        result = _heuristic_extract(readme, "agent", tmp_path)
        assert "OPENAI_API_KEY" in result["api_keys"]
        assert "ANTHROPIC_API_KEY" in result["api_keys"]

    def test_complexity_based_on_file_count(self, tmp_path: Path):
        readme = "A simple agent."
        # Create many files to trigger advanced complexity
        for i in range(100):
            (tmp_path / f"file{i}.py").write_text("print('test')")
        result = _heuristic_extract(readme, "agent", tmp_path)
        assert result["complexity"] == "advanced"

    def test_extracts_name_from_heading(self, tmp_path: Path):
        readme = "# My Awesome Agent\n\nDescription here."
        (tmp_path / "app.py").write_text("print('test')")
        result = _heuristic_extract(readme, "fallback_name", tmp_path)
        assert result["name"] == "My Awesome Agent"

    def test_extracts_description(self, tmp_path: Path):
        readme = "# Agent\n\nThis is a detailed description of the agent.\n\nMore content."
        (tmp_path / "app.py").write_text("print('test')")
        result = _heuristic_extract(readme, "agent", tmp_path)
        assert "detailed description" in result["description"]

    def test_frameworks_fallback_to_raw_api(self, tmp_path: Path):
        readme = "A simple agent without framework mentions."
        (tmp_path / "app.py").write_text("print('test')")
        result = _heuristic_extract(readme, "agent", tmp_path)
        assert result["frameworks"] == ["raw_api"]


class TestNormalizeLlmOutput:
    """Tests for LLM output normalization."""

    def test_normalizes_category_to_known_enum(self):
        result = _normalize_llm_output({"category": "unknown_category"})
        assert result["category"] == "other"

    def test_normalizes_frameworks(self):
        result = _normalize_llm_output({
            "frameworks": ["langchain", "unknown_framework", "crewai"]
        })
        assert "langchain" in result["frameworks"]
        assert "crewai" in result["frameworks"]
        assert "unknown_framework" not in result["frameworks"]

    def test_normalizes_llm_providers(self):
        result = _normalize_llm_output({
            "llm_providers": ["openai", "unknown_provider"]
        })
        assert "openai" in result["llm_providers"]
        assert "unknown_provider" not in result["llm_providers"]

    def test_normalizes_complexity(self):
        result = _normalize_llm_output({"complexity": "unknown"})
        assert result["complexity"] == "intermediate"

    def test_normalizes_api_keys(self):
        result = _normalize_llm_output({
            "api_keys": ["OPENAI_API_KEY", "UNKNOWN_KEY"]
        })
        assert "OPENAI_API_KEY" in result["api_keys"]
        assert "UNKNOWN_KEY" not in result["api_keys"]

    def test_handles_list_values(self):
        result = _normalize_llm_output({"frameworks": "langchain"})
        assert result["frameworks"] == ["langchain"]

    def test_handles_none_values(self):
        result = _normalize_llm_output({
            "frameworks": None,
            "llm_providers": None,
        })
        assert result["frameworks"] == ["other"]
        assert result["llm_providers"] == ["other"]

    def test_trims_description_length(self):
        long_desc = "x" * 200
        result = _normalize_llm_output({"description": long_desc})
        assert len(result["description"]) <= 160

    def test_trims_quick_start_length(self):
        long_qs = "command\n" * 500
        result = _normalize_llm_output({"quick_start": long_qs})
        assert len(result["quick_start"]) <= 1200


class TestGitLastModified:
    """Tests for git timestamp extraction."""

    @patch("subprocess.run")
    def test_git_last_modified_success(self, mock_run: Mock):
        mock_run.return_value.stdout = "1609459200"
        result = _git_last_modified_ts(Path("/fake/repo"), "some/path")
        assert result == 1609459200

    @patch("subprocess.run")
    def test_git_last_modified_failure(self, mock_run: Mock):
        mock_run.side_effect = Exception("git not found")
        result = _git_last_modified_ts(Path("/fake/repo"), "some/path")
        assert result is None

    @patch("subprocess.run")
    def test_git_last_modified_invalid_output(self, mock_run: Mock):
        mock_run.return_value.stdout = "not_a_number"
        result = _git_last_modified_ts(Path("/fake/repo"), "some/path")
        assert result is None


class TestParseGithubUrl:
    """Tests for GitHub URL parsing."""

    @pytest.mark.parametrize(
        ("url", "expected"),
        [
            ("https://github.com/user/repo", ("user", "repo")),
            ("https://github.com/user/repo.git", ("user", "repo")),
            ("https://github.com/user/repo/", ("user", "repo")),
            ("https://notgithub.com/user/repo", None),
            ("invalid_url", None),
        ],
    )
    def test_parse_github_owner_repo(self, url: str, expected: Any):
        result = _parse_github_owner_repo(url)
        assert result == expected


class TestFetchGithubStars:
    """Tests for GitHub stars fetching."""

    @patch("urllib.request.urlopen")
    def test_fetch_stars_success(self, mock_urlopen: Mock):
        mock_response = Mock()
        mock_response.headers.get_content_charset.return_value = "utf-8"
        mock_response.read.return_value = b'{"stargazers_count": 1234}'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = _fetch_github_repo_stars("user", "repo", token=None, use_cache=False)
        assert result == 1234

    @patch("urllib.request.urlopen")
    def test_fetch_stars_with_token(self, mock_urlopen: Mock):
        mock_response = Mock()
        mock_response.headers.get_content_charset.return_value = "utf-8"
        mock_response.read.return_value = b'{"stargazers_count": 5678}'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = _fetch_github_repo_stars("user", "repo", token="test_token", use_cache=False)
        assert result == 5678

    @patch("urllib.request.urlopen")
    def test_fetch_stars_failure(self, mock_urlopen: Mock):
        mock_urlopen.side_effect = Exception("Network error")
        result = _fetch_github_repo_stars("user", "repo", token=None, use_cache=False)
        assert result is None

    @patch("urllib.request.urlopen")
    def test_fetch_stars_invalid_json(self, mock_urlopen: Mock):
        mock_response = Mock()
        mock_response.read.return_value = b'{"invalid": json'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = _fetch_github_repo_stars("user", "repo", token=None, use_cache=False)
        assert result is None


class TestRepoIndexer:
    """Tests for RepoIndexer class."""

    def test_initialization(self, tmp_path: Path):
        cache_path = tmp_path / "cache.json"
        indexer = RepoIndexer(
            cache_path=cache_path,
            anthropic_api_key=None,
            enable_llm=False,
        )
        assert indexer.cache_path == cache_path
        assert indexer.enable_llm is False
        assert indexer.client is None

    def test_cache_loading(self, tmp_path: Path):
        cache_path = tmp_path / "cache.json"
        cache_data = {
            "agent_one": {
                "id": "agent_one",
                "name": "Agent One",
                "description": "Test",
                "category": "other",
                "frameworks": ["other"],
                "llm_providers": ["other"],
                "requires_gpu": False,
                "supports_local_models": False,
                "design_pattern": "other",
                "complexity": "intermediate",
                "quick_start": "",
                "clone_command": "",
                "github_url": "",
                "codespaces_url": None,
                "colab_url": None,
                "stars": None,
                "folder_path": "",
                "readme_relpath": "",
                "updated_at": None,
                "api_keys": [],
                "languages": [],
                "tags": [],
                "content_hash": "abc123",
            }
        }
        cache_path.write_text(json.dumps(cache_data))

        indexer = RepoIndexer(cache_path=cache_path, enable_llm=False)
        assert len(indexer.cache) == 1
        assert "agent_one" in indexer.cache

    def test_cache_loading_invalid(self, tmp_path: Path):
        cache_path = tmp_path / "cache.json"
        cache_path.write_text("invalid json")

        indexer = RepoIndexer(cache_path=cache_path, enable_llm=False)
        assert len(indexer.cache) == 0

    def test_cache_saving(self, tmp_path: Path):
        cache_path = tmp_path / "cache.json"
        indexer = RepoIndexer(cache_path=cache_path, enable_llm=False)
        indexer.cache["test_agent"] = AgentMetadata(
            id="test_agent",
            name="Test",
            description="Test agent",
            category="other",
            frameworks=["other"],
            llm_providers=["other"],
            requires_gpu=False,
            supports_local_models=False,
            design_pattern="other",
            complexity="intermediate",
            quick_start="",
            clone_command="",
            github_url="",
            codespaces_url=None,
            colab_url=None,
            stars=None,
            folder_path="",
            readme_relpath="",
            updated_at=None,
            api_keys=[],
            languages=[],
            tags=[],
            content_hash="abc",
        )
        indexer._save_cache()

        assert cache_path.exists()
        loaded = json.loads(cache_path.read_text())
        assert "test_agent" in loaded

    @patch("src.indexer.RepoIndexer._extract_with_llm")
    def test_extract_agent_with_llm(self, mock_llm: Mock, tmp_path: Path):
        mock_llm.return_value = {
            "name": "LLM Agent",
            "description": "Extracted by LLM",
            "category": "rag",
            "frameworks": ["langchain"],
            "llm_providers": ["openai"],
            "requires_gpu": False,
            "supports_local_models": False,
            "design_pattern": "rag",
            "complexity": "intermediate",
            "quick_start": "pip install",
            "api_keys": [],
        }

        repo = tmp_path / "repo"
        repo.mkdir()
        agent_dir = repo / "test_agent"
        agent_dir.mkdir()
        readme = agent_dir / "README.md"
        readme.write_text("# Test Agent\n\nTest content", encoding="utf-8")

        indexer = RepoIndexer(
            cache_path=tmp_path / "cache.json",
            anthropic_api_key="fake_key",
            enable_llm=True,
        )
        # Mock the client
        indexer.client = Mock()

        result = indexer.extract_agent(readme, repo)
        assert result is not None
        assert result.name == "LLM Agent"

    def test_extract_agent_cache_hit(self, tmp_path: Path):
        repo = tmp_path / "repo"
        repo.mkdir()
        agent_dir = repo / "test_agent"
        agent_dir.mkdir()
        readme = agent_dir / "README.md"
        content = "# Test Agent\n\nTest content"
        readme.write_text(content, encoding="utf-8")

        cache_path = tmp_path / "cache.json"
        content_hash = _content_hash(content)

        # Pre-populate cache
        cached_agent = AgentMetadata(
            id="test_agent",
            name="Cached Agent",
            description="Cached",
            category="other",
            frameworks=["other"],
            llm_providers=["other"],
            requires_gpu=False,
            supports_local_models=False,
            design_pattern="other",
            complexity="intermediate",
            quick_start="",
            clone_command="",
            github_url="",
            codespaces_url=None,
            colab_url=None,
            stars=None,
            folder_path="test_agent",
            readme_relpath="test_agent/README.md",
            updated_at=None,
            api_keys=[],
            languages=[],
            tags=[],
            content_hash=content_hash,
        )

        indexer = RepoIndexer(cache_path=cache_path, enable_llm=False)
        indexer.cache["test_agent"] = cached_agent

        result = indexer.extract_agent(readme, repo)
        assert result is not None
        assert result.name == "Cached Agent"  # Should return cached version

    def test_generate_urls(self):
        indexer = RepoIndexer(enable_llm=False)
        github_url, codespaces_url = indexer._generate_urls("path/to/agent")
        assert "path/to/agent" in github_url
        assert "codespaces.new" in codespaces_url

    def test_extract_agent_creates_colab_url(self, tmp_path: Path):
        repo = tmp_path / "repo"
        repo.mkdir()
        agent_dir = repo / "notebook_agent"
        agent_dir.mkdir()
        (agent_dir / "README.md").write_text("# Test\n\nContent", encoding="utf-8")
        (agent_dir / "demo.ipynb").write_text("{}", encoding="utf-8")

        indexer = RepoIndexer(enable_llm=False)
        result = indexer.extract_agent(agent_dir / "README.md", repo)
        assert result is not None
        assert result.colab_url is not None
        assert "colab.research.google.com" in result.colab_url

    def test_index_repository(self, tmp_repo_dir: Path):
        indexer = RepoIndexer(enable_llm=False)
        agents = indexer.index_repository(tmp_repo_dir)

        # Should find agents but not excluded ones
        agent_ids = [a.id for a in agents]
        assert "agent_one" in agent_ids
        assert "agent_two" in agent_ids
        assert "nested_deep_agent" in agent_ids
        assert "package" not in agent_ids  # Excluded

    def test_index_repository_with_limit(self, tmp_repo_dir: Path):
        indexer = RepoIndexer(enable_llm=False)
        agents = indexer.index_repository(tmp_repo_dir, limit=2)
        assert len(agents) <= 2

    def test_index_repository_with_exclude_dirs(self, tmp_path: Path):
        repo = tmp_path / "repo"
        repo.mkdir()

        # Create directories
        for name in ["agent1", "agent2", "custom_dir"]:
            agent_dir = repo / name
            agent_dir.mkdir()
            (agent_dir / "README.md").write_text(f"# {name}", encoding="utf-8")

        indexer = RepoIndexer(enable_llm=False)
        agents = indexer.index_repository(
            repo,
            exclude_dirs={".git", "custom_dir"}
        )

        agent_ids = [a.id for a in agents]
        assert "agent1" in agent_ids
        assert "agent2" in agent_ids
        assert "custom_dir" not in agent_ids


class TestAgentMetadata:
    """Tests for AgentMetadata dataclass."""

    def test_agent_metadata_creation(self):
        metadata = AgentMetadata(
            id="test",
            name="Test Agent",
            description="A test",
            category="rag",
            frameworks=["langchain"],
            llm_providers=["openai"],
            requires_gpu=True,
            supports_local_models=False,
            design_pattern="rag",
            complexity="beginner",
            quick_start="pip install",
            clone_command="git clone ...",
            github_url="https://github.com/user/repo",
            codespaces_url="https://codespaces.new/user/repo",
            colab_url=None,
            stars=100,
            folder_path="test",
            readme_relpath="test/README.md",
            updated_at=1609459200,
            api_keys=["OPENAI_API_KEY"],
            languages=["python"],
            tags=["rag", "test"],
            content_hash="abc123",
        )
        assert metadata.id == "test"
        assert metadata.category == "rag"
        assert metadata.stars == 100

    def test_agent_metadata_is_frozen(self):
        metadata = AgentMetadata(
            id="test",
            name="Test",
            description="Test",
            category="other",
            frameworks=[],
            llm_providers=[],
            requires_gpu=False,
            supports_local_models=False,
            design_pattern="other",
            complexity="intermediate",
            quick_start="",
            clone_command="",
            github_url="",
            codespaces_url=None,
            colab_url=None,
            stars=None,
            folder_path="",
            readme_relpath="",
            updated_at=None,
            api_keys=[],
            languages=[],
            tags=[],
            content_hash="",
        )
        with pytest.raises(Exception):  # FrozenInstanceError
            metadata.name = "New Name"


class TestEdgeCases:
    """Edge case tests."""

    def test_empty_readme(self, tmp_path: Path):
        readme = ""
        result = _heuristic_extract(readme, "agent", tmp_path)
        assert result["name"] == "Agent"
        assert result["category"] in CATEGORIES

    def test_readme_with_only_special_chars(self, tmp_path: Path):
        readme = "!@#$%^&*()"
        result = _heuristic_extract(readme, "agent", tmp_path)
        # Should not crash
        assert result is not None

    def test_very_long_folder_path(self):
        path = "very" * 50 + "_agent"
        result = _safe_title_from_path(path)
        assert len(result) > 0

    def test_unicode_in_readme(self, tmp_path: Path):
        readme = "# Agent 世界\n\nDescription with emoji: 🚀"
        (tmp_path / "test.py").write_text("print('test')")
        result = _heuristic_extract(readme, "agent", tmp_path)
        assert result is not None

    def test_mixed_case_keywords(self, tmp_path: Path):
        readme = "Uses LANGCHAIN and OpenAI"
        (tmp_path / "test.py").write_text("print('test')")
        result = _heuristic_extract(readme, "agent", tmp_path)
        assert "langchain" in result["frameworks"]
        assert "openai" in result["llm_providers"]

    def test_nested_code_blocks(self, tmp_path: Path):
        readme = """
```
bash
pip install
```

More text

```bash
npm install
```
"""
        (tmp_path / "test.py").write_text("print('test')")
        result = _heuristic_extract(readme, "agent", tmp_path)
        assert "pip install" in result["quick_start"]
