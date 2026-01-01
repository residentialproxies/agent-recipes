"""
Security module for Agent Navigator.

Provides input validation, rate limiting, secrets management,
and output sanitization to prevent common vulnerabilities.
"""

from src.security.validators import (
    validate_github_url,
    sanitize_llm_output,
    ValidationError,
)
from src.security.rate_limit import (
    FileRateLimiter,
    get_rate_limiter,
)
from src.security.secrets import (
    SecretsManager,
    get_secrets_manager,
)
from src.security.sql import (
    escape_like_pattern,
    build_like_clause,
    validate_search_input,
)
from src.security.markdown import (
    sanitize_markdown,
    sanitize_html_only,
    MarkdownSanitizer,
)

__all__ = [
    "validate_github_url",
    "sanitize_llm_output",
    "ValidationError",
    "FileRateLimiter",
    "get_rate_limiter",
    "SecretsManager",
    "get_secrets_manager",
    "escape_like_pattern",
    "build_like_clause",
    "validate_search_input",
    "sanitize_markdown",
    "sanitize_html_only",
    "MarkdownSanitizer",
]
