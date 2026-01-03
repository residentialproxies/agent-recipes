"""
Tests for src.config module.

Covers:
- Settings initialization
- Environment variable overrides
- Default values
- Constants
"""

import os
from pathlib import Path
from unittest import mock


class TestSettings:
    """Tests for Settings class."""

    def test_default_values(self):
        """Test that default values are set correctly."""
        from src.config import Settings

        with mock.patch.dict(os.environ, {}, clear=True):
            settings = Settings()

        assert settings.data_path == Path("data/agents.json")
        assert settings.source_repo_url == "https://github.com/Shubhamsaboo/awesome-llm-apps"
        assert settings.source_branch == "main"
        assert settings.anthropic_model == "claude-3-5-haiku-20241022"
        assert settings.max_llm_tokens == 600
        assert settings.default_page_size == 20
        assert settings.rate_limit_requests == 10
        assert settings.rate_limit_window_seconds == 60
        assert settings.enable_ai_selector is True
        assert settings.debug_mode is False

    def test_env_override_paths(self):
        """Test environment variable overrides for paths."""
        from src.config import Settings

        env = {
            "AGENT_NAV_DATA_PATH": "/custom/data.json",
            "AGENT_NAV_CACHE_PATH": "/custom/cache.json",
            "AGENT_NAV_OUTPUT_PATH": "/custom/output",
        }
        with mock.patch.dict(os.environ, env, clear=True):
            settings = Settings()

        assert settings.data_path == Path("/custom/data.json")
        assert settings.cache_path == Path("/custom/cache.json")
        assert settings.static_output_path == Path("/custom/output")

    def test_env_override_source_repo(self):
        """Test environment variable overrides for source repo."""
        from src.config import Settings

        env = {
            "SOURCE_REPO_URL": "https://github.com/other/repo",
            "SOURCE_BRANCH": "develop",
        }
        with mock.patch.dict(os.environ, env, clear=True):
            settings = Settings()

        assert settings.source_repo_url == "https://github.com/other/repo"
        assert settings.source_branch == "develop"

    def test_env_override_api_settings(self):
        """Test environment variable overrides for API settings."""
        from src.config import Settings

        env = {
            "ANTHROPIC_MODEL": "claude-3-opus",
            "MAX_LLM_TOKENS": "1000",
        }
        with mock.patch.dict(os.environ, env, clear=True):
            settings = Settings()

        assert settings.anthropic_model == "claude-3-opus"
        assert settings.max_llm_tokens == 1000

    def test_env_override_rate_limiting(self):
        """Test environment variable overrides for rate limiting."""
        from src.config import Settings

        env = {
            "RATE_LIMIT_REQUESTS": "20",
            "RATE_LIMIT_WINDOW": "120",
        }
        with mock.patch.dict(os.environ, env, clear=True):
            settings = Settings()

        assert settings.rate_limit_requests == 20
        assert settings.rate_limit_window_seconds == 120

    def test_env_override_indexer(self):
        """Test environment variable overrides for indexer."""
        from src.config import Settings

        env = {
            "INDEXER_WORKERS": "10",
            "INDEXER_RATE_LIMIT": "5.5",
        }
        with mock.patch.dict(os.environ, env, clear=True):
            settings = Settings()

        assert settings.indexer_workers == 10
        assert settings.indexer_rate_limit == 5.5

    def test_env_override_feature_flags(self):
        """Test environment variable overrides for feature flags."""
        from src.config import Settings

        env = {
            "DISABLE_AI_SELECTOR": "true",
            "ENABLE_ANALYTICS": "1",
            "DEBUG": "TRUE",
        }
        with mock.patch.dict(os.environ, env, clear=True):
            settings = Settings()

        assert settings.enable_ai_selector is False
        assert settings.enable_analytics is True
        assert settings.debug_mode is True

    def test_api_key_property(self):
        """Test that API key is retrieved from environment."""
        from src.config import Settings

        with mock.patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-test-key"}):
            settings = Settings()
            # Access the property while the mock is still active
            assert settings.anthropic_api_key == "sk-test-key"

    def test_api_key_not_stored(self):
        """Test that API key is not stored in settings object."""
        from src.config import Settings

        env = {"ANTHROPIC_API_KEY": "sk-test-key"}
        with mock.patch.dict(os.environ, env, clear=True):
            settings = Settings()

        # API key should not be in __dict__
        assert "anthropic_api_key" not in settings.__dict__
        assert "sk-test-key" not in str(settings.__dict__)

    def test_github_token_property(self):
        """Test that GitHub token is retrieved from environment."""
        from src.config import Settings

        with mock.patch.dict(os.environ, {"GITHUB_TOKEN": "ghp_test"}):
            settings = Settings()
            # Access the property while the mock is still active
            assert settings.github_token == "ghp_test"  # noqa: S105

    def test_missing_api_key(self):
        """Test that missing API key returns None."""
        from src.config import Settings

        with mock.patch.dict(os.environ, {}, clear=True):
            settings = Settings()

        assert settings.anthropic_api_key is None


class TestGetSettings:
    """Tests for get_settings singleton function."""

    def test_get_settings_returns_settings(self):
        """Test that get_settings returns a Settings instance."""
        from src.config import Settings, get_settings

        settings = get_settings()
        assert isinstance(settings, Settings)

    def test_get_settings_singleton(self):
        """Test that get_settings returns the same instance."""
        from src.config import get_settings

        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2

    def test_reload_settings(self):
        """Test that reload_settings creates a new instance."""
        from src.config import get_settings, reload_settings

        settings1 = get_settings()
        settings2 = reload_settings()
        # After reload, should be different instance
        assert settings1 is not settings2


class TestConstants:
    """Tests for configuration constants."""

    def test_categories_frozenset(self):
        """Test that CATEGORIES is a frozenset with expected values."""
        from src.config import CATEGORIES

        assert isinstance(CATEGORIES, frozenset)
        assert "rag" in CATEGORIES
        assert "chatbot" in CATEGORIES
        assert "agent" in CATEGORIES
        assert "multi_agent" in CATEGORIES
        assert "other" in CATEGORIES

    def test_frameworks_frozenset(self):
        """Test that FRAMEWORKS is a frozenset with expected values."""
        from src.config import FRAMEWORKS

        assert isinstance(FRAMEWORKS, frozenset)
        assert "langchain" in FRAMEWORKS
        assert "llamaindex" in FRAMEWORKS
        assert "crewai" in FRAMEWORKS
        assert "raw_api" in FRAMEWORKS

    def test_llm_providers_frozenset(self):
        """Test that LLM_PROVIDERS is a frozenset with expected values."""
        from src.config import LLM_PROVIDERS

        assert isinstance(LLM_PROVIDERS, frozenset)
        assert "openai" in LLM_PROVIDERS
        assert "anthropic" in LLM_PROVIDERS
        assert "ollama" in LLM_PROVIDERS
        assert "local" in LLM_PROVIDERS

    def test_complexity_levels_frozenset(self):
        """Test that COMPLEXITY_LEVELS is a frozenset with expected values."""
        from src.config import COMPLEXITY_LEVELS

        assert isinstance(COMPLEXITY_LEVELS, frozenset)
        assert "beginner" in COMPLEXITY_LEVELS
        assert "intermediate" in COMPLEXITY_LEVELS
        assert "advanced" in COMPLEXITY_LEVELS

    def test_category_icons_mapping(self):
        """Test that CATEGORY_ICONS contains expected mappings."""
        from src.config import CATEGORIES, CATEGORY_ICONS

        assert isinstance(CATEGORY_ICONS, dict)
        # All categories should have icons
        for cat in CATEGORIES:
            assert cat in CATEGORY_ICONS
            assert len(CATEGORY_ICONS[cat]) > 0

    def test_category_icons_are_emoji(self):
        """Test that category icons are emoji characters."""
        from src.config import CATEGORY_ICONS

        for _cat, icon in CATEGORY_ICONS.items():
            # Emoji should be non-ASCII
            assert not icon.isascii() or icon == "✨"


class TestAllowedHosts:
    """Tests for allowed hosts configuration."""

    def test_allowed_readme_hosts(self):
        """Test that allowed hosts are configured correctly."""
        from src.config import Settings

        settings = Settings()
        assert "raw.githubusercontent.com" in settings.allowed_readme_hosts
        assert "github.com" in settings.allowed_readme_hosts

    def test_allowed_hosts_is_set(self):
        """Test that allowed_readme_hosts is a set for O(1) lookup."""
        from src.config import Settings

        settings = Settings()
        assert isinstance(settings.allowed_readme_hosts, set)
