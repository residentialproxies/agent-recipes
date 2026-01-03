"""
Agent Navigator - Configuration Management
==========================================
Centralized configuration with environment variable support and validation.

Usage:
    from src.config import settings

    api_key = settings.anthropic_api_key
    max_agents = settings.max_agents_per_page
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class Settings:
    """Application settings with environment variable overrides."""

    # Paths
    data_path: Path = field(default_factory=lambda: Path("data/agents.json"))
    cache_path: Path = field(default_factory=lambda: Path("data/.indexer_cache.json"))
    static_output_path: Path = field(default_factory=lambda: Path("site"))
    webmanus_db_path: Path = field(default_factory=lambda: Path("data/webmanus.db"))

    # Source repository
    source_repo_url: str = "https://github.com/Shubhamsaboo/awesome-llm-apps"
    source_branch: str = "main"

    # API Configuration
    anthropic_model: str = "claude-3-5-haiku-20241022"
    max_llm_tokens: int = 600
    llm_timeout_seconds: int = 30

    # Search settings
    max_search_results: int = 500
    search_cache_size: int = 500

    # UI settings
    default_page_size: int = 20
    max_agents_per_page: int = 40
    recently_viewed_limit: int = 10

    # Rate limiting
    rate_limit_requests: int = 10
    rate_limit_window_seconds: int = 60

    # Reverse proxy / client IP extraction
    # When running behind a reverse proxy, set TRUST_PROXY_HEADERS=true and TRUSTED_PROXY_IPS
    # to correctly derive client IPs from X-Forwarded-For.
    trust_proxy_headers: bool = False
    trusted_proxy_ips: set[str] = field(default_factory=set)

    # AI selector (API)
    ai_cache_path: Path = field(default_factory=lambda: Path("data/.ai_selector_cache.json"))
    ai_budget_path: Path = field(default_factory=lambda: Path("data/.ai_selector_budget.json"))
    ai_cache_ttl_seconds: int = 60 * 60 * 6  # 6 hours
    ai_daily_budget_usd: float = 5.0

    # Indexer settings
    max_readme_chars: int = 8000
    indexer_workers: int = 20
    indexer_rate_limit: float = 10.0  # requests per second

    # Security
    allowed_readme_hosts: set[str] = field(
        default_factory=lambda: {
            "raw.githubusercontent.com",
            "github.com",
        }
    )

    # CORS configuration
    # Set CORS_ALLOW_ORIGINS environment variable to comma-separated list of allowed origins
    # Use "*" for development only (allows all origins)
    # Example: CORS_ALLOW_ORIGINS="https://example.com,https://app.example.com"
    cors_allow_origins: set[str] = field(
        default_factory=lambda: {
            "http://localhost",
            "http://localhost:8501",  # Streamlit default
            "http://127.0.0.1",
            "http://127.0.0.1:8501",
        }
    )
    cors_allow_credentials: bool = False
    cors_max_age: int = 600  # 10 minutes

    # CSP nonce generation (for inline scripts)
    # When enabled, generates nonces for inline script CSP
    csp_use_nonce: bool = True

    # SEO
    site_base_url: str = "https://agent-navigator.com"
    site_name: str = "Agent Navigator"

    # Feature flags
    enable_ai_selector: bool = True
    enable_analytics: bool = False
    debug_mode: bool = False

    def __post_init__(self):
        """Load overrides from environment variables."""
        self._load_env_overrides()

    def _load_env_overrides(self):
        """Load configuration from environment variables."""
        # Paths
        if data_path := os.environ.get("AGENT_NAV_DATA_PATH"):
            self.data_path = Path(data_path)
        if cache_path := os.environ.get("AGENT_NAV_CACHE_PATH"):
            self.cache_path = Path(cache_path)
        if output_path := os.environ.get("AGENT_NAV_OUTPUT_PATH"):
            self.static_output_path = Path(output_path)
        if webmanus_db_path := os.environ.get("WEBMANUS_DB_PATH"):
            self.webmanus_db_path = Path(webmanus_db_path)

        # Source repo
        if repo_url := os.environ.get("SOURCE_REPO_URL"):
            self.source_repo_url = repo_url
        if branch := os.environ.get("SOURCE_BRANCH"):
            self.source_branch = branch

        # API settings
        if model := os.environ.get("ANTHROPIC_MODEL"):
            self.anthropic_model = model
        if max_tokens := os.environ.get("MAX_LLM_TOKENS"):
            self.max_llm_tokens = int(max_tokens)

        # Rate limiting
        if rate_limit := os.environ.get("RATE_LIMIT_REQUESTS"):
            self.rate_limit_requests = int(rate_limit)
        if window := os.environ.get("RATE_LIMIT_WINDOW"):
            self.rate_limit_window_seconds = int(window)

        # Reverse proxy / headers
        if os.environ.get("TRUST_PROXY_HEADERS", "").lower() in ("1", "true", "yes"):
            self.trust_proxy_headers = True
        if trusted := os.environ.get("TRUSTED_PROXY_IPS", "").strip():
            self.trusted_proxy_ips = {ip.strip() for ip in trusted.split(",") if ip.strip()}

        # AI selector
        if ai_cache_path := os.environ.get("AI_CACHE_PATH"):
            self.ai_cache_path = Path(ai_cache_path)
        if ai_budget_path := os.environ.get("AI_BUDGET_PATH"):
            self.ai_budget_path = Path(ai_budget_path)
        if ai_cache_ttl := os.environ.get("AI_CACHE_TTL_SECONDS"):
            self.ai_cache_ttl_seconds = int(ai_cache_ttl)
        if ai_budget := os.environ.get("AI_DAILY_BUDGET_USD"):
            self.ai_daily_budget_usd = float(ai_budget)

        # Indexer
        if workers := os.environ.get("INDEXER_WORKERS"):
            self.indexer_workers = int(workers)
        if rate := os.environ.get("INDEXER_RATE_LIMIT"):
            self.indexer_rate_limit = float(rate)

        # CORS configuration - security: requires explicit configuration
        if cors_origins := os.environ.get("CORS_ALLOW_ORIGINS", "").strip():
            if cors_origins == "*":
                # Allow all origins - development only
                # In production, explicitly list allowed origins
                logger.warning(
                    "CORS_ALLOW_ORIGINS set to '*' - allowing all origins. " "This should only be used in development."
                )
                self.cors_allow_origins = {"*"}
            else:
                # Parse comma-separated list of origins
                self.cors_allow_origins = {origin.strip() for origin in cors_origins.split(",") if origin.strip()}
        if cors_max_age := os.environ.get("CORS_MAX_AGE"):
            self.cors_max_age = int(cors_max_age)

        # CSP configuration
        if os.environ.get("CSP_USE_NONCE", "").lower() in ("0", "false", "no"):
            self.csp_use_nonce = False

        # SEO
        if base_url := os.environ.get("SITE_BASE_URL"):
            self.site_base_url = base_url

        # Feature flags
        if os.environ.get("DISABLE_AI_SELECTOR", "").lower() in ("1", "true"):
            self.enable_ai_selector = False
        if os.environ.get("ENABLE_ANALYTICS", "").lower() in ("1", "true"):
            self.enable_analytics = True
        if os.environ.get("DEBUG", "").lower() in ("1", "true"):
            self.debug_mode = True

    @property
    def anthropic_api_key(self) -> str | None:
        """Get Anthropic API key from environment (never stored in config)."""
        return os.environ.get("ANTHROPIC_API_KEY")

    @property
    def github_token(self) -> str | None:
        """Get GitHub token from environment (never stored in config)."""
        return os.environ.get("GITHUB_TOKEN")


# Singleton instance
_settings: Settings | None = None


def get_settings() -> Settings:
    """Get the global settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
        if _settings.debug_mode:
            logger.info("Settings loaded with debug mode enabled")
    return _settings


def reload_settings() -> Settings:
    """Force reload settings from environment."""
    global _settings
    _settings = Settings()
    return _settings


# Convenience alias
settings = get_settings()


# Category and framework constants
CATEGORIES = frozenset(
    {
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
    }
)

FRAMEWORKS = frozenset(
    {
        "langchain",
        "llamaindex",
        "crewai",
        "autogen",
        "phidata",
        "dspy",
        "haystack",
        "semantic_kernel",
        "raw_api",
        "other",
    }
)

LLM_PROVIDERS = frozenset(
    {
        "openai",
        "anthropic",
        "google",
        "cohere",
        "mistral",
        "ollama",
        "huggingface",
        "local",
        "other",
    }
)

COMPLEXITY_LEVELS = frozenset(
    {
        "beginner",
        "intermediate",
        "advanced",
    }
)

CATEGORY_ICONS = {
    "rag": "📚",
    "chatbot": "💬",
    "agent": "🤖",
    "multi_agent": "🧩",
    "automation": "⚙️",
    "search": "🔎",
    "vision": "🖼️",
    "voice": "🎙️",
    "coding": "🧑‍💻",
    "finance": "💹",
    "research": "🧪",
    "other": "✨",
}
