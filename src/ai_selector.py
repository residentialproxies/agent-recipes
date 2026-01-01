"""
Agent Navigator - AI Selector (API-friendly)
==========================================
Provides:
- Prompt building from candidate agents
- File-based caching (TTL)
- Daily budget enforcement (USD)
- Optional streaming via Anthropic Messages API
- Centralized Anthropic client management

Note: Streaming yields raw text deltas. The caller should render as text
(never as HTML) to avoid XSS. The final full text is sanitized server-side.
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Iterable, Optional

from src.cache import CacheEntry, SQLiteCache, SQLiteBudget
from src.config import settings
from src.security.validators import ValidationError, sanitize_llm_output


class AISelectorError(RuntimeError):
    """Exception raised for AI selector errors."""
    pass


def _sha256(text: str) -> str:
    """Compute SHA256 hash of text."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _now_s() -> float:
    """Get current time in seconds."""
    return time.time()


# =============================================================================
# Centralized Anthropic Service
# =============================================================================

class AnthropicService:
    """
    Centralized wrapper for Anthropic API client.

    Eliminates code duplication between api.py and ai_selector.py
    by providing a single source of truth for:
    - Client creation and configuration
    - Error handling and translation
    - Response extraction

    Usage:
        service = AnthropicService(api_key="sk-...")
        try:
            response = service.create_non_streaming(
                model="claude-3-5-haiku-20241022",
                max_tokens=600,
                messages=[{"role": "user", "content": "Hello"}]
            )
            text = service.extract_text(response)
        except HTTPException as e:
            # Handle API errors
            pass
    """

    # Class-level error messages for HTTP status codes
    ERROR_MESSAGES = {
        "auth": "Invalid API key",
        "rate_limit": "Upstream rate limited",
        "timeout": "Upstream timeout",
        "connection": "Upstream connection error",
    }

    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-5-haiku-20241022"):
        """
        Initialize the Anthropic service.

        Args:
            api_key: Anthropic API key. If None, uses from settings.
            model: Default model to use for requests.
        """
        self._api_key = api_key or settings.anthropic_api_key
        self._model = model
        self._client: Optional[Any] = None

    @property
    def client(self) -> Any:
        """Lazy-load the Anthropic client."""
        if self._client is None:
            try:
                import anthropic  # type: ignore
            except ImportError:
                # Offline/test fallback: allow the API layer to monkeypatch
                # `src.api.anthropic.Anthropic` even when the dependency isn't installed.
                try:
                    import src.api as api_mod  # type: ignore
                except Exception as exc:  # pragma: no cover
                    raise RuntimeError("anthropic package is required") from exc
                anthropic = api_mod.anthropic  # type: ignore
                if not getattr(anthropic, "Anthropic", None):
                    raise RuntimeError("anthropic package is required")
            if not self._api_key:
                raise RuntimeError("ANTHROPIC_API_KEY is required")
            self._client = anthropic.Anthropic(api_key=self._api_key)
        return self._client

    def create_non_streaming(
        self,
        messages: list[dict[str, str]],
        max_tokens: int,
        model: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> Any:
        """
        Create a non-streaming message request.

        Args:
            messages: List of message dicts with 'role' and 'content'.
            max_tokens: Maximum tokens in response.
            model: Model override. Uses default if None.
            timeout: Request timeout in seconds.

        Returns:
            Anthropic response object.

        Raises:
            HTTPException: For API errors with appropriate status codes.
        """
        from fastapi import HTTPException

        model = model or self._model
        timeout = timeout or settings.llm_timeout_seconds

        try:
            return self.client.messages.create(
                model=model,
                max_tokens=max_tokens,
                messages=messages,
                timeout=timeout,
            )
        except self._get_auth_error() as e:
            raise HTTPException(status_code=503, detail=self.ERROR_MESSAGES["auth"]) from e
        except self._get_rate_limit_error() as e:
            raise HTTPException(status_code=503, detail=self.ERROR_MESSAGES["rate_limit"]) from e
        except self._get_timeout_error() as e:
            raise HTTPException(status_code=504, detail=self.ERROR_MESSAGES["timeout"]) from e
        except self._get_connection_error() as e:
            raise HTTPException(status_code=503, detail=self.ERROR_MESSAGES["connection"]) from e
        except self._get_status_error() as e:
            raise HTTPException(status_code=503, detail=f"Upstream error {e.status_code}") from e

    def create_streaming(
        self,
        messages: list[dict[str, str]],
        max_tokens: int,
        model: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> Any:
        """
        Create a streaming message request.

        Args:
            messages: List of message dicts with 'role' and 'content'.
            max_tokens: Maximum tokens in response.
            model: Model override. Uses default if None.
            timeout: Request timeout in seconds.

        Returns:
            Anthropic stream context manager.

        Raises:
            HTTPException: For API errors with appropriate status codes.
        """
        from fastapi import HTTPException

        model = model or self._model
        timeout = timeout or settings.llm_timeout_seconds

        return self.client.messages.stream(
            model=model,
            max_tokens=max_tokens,
            messages=messages,
            timeout=timeout,
        )

    def extract_text(self, response: Any) -> str:
        """
        Extract text content from a non-streaming response.

        Args:
            response: Anthropic response object.

        Returns:
            Extracted text content.
        """
        if response and response.content:
            return response.content[0].text
        return ""

    def extract_usage(self, response: Any) -> dict:
        """
        Extract usage information from a response.

        Args:
            response: Anthropic response object (can be from stream.get_final_message()).

        Returns:
            Dict with input_tokens and output_tokens if available.
        """
        usage = getattr(response, "usage", None)
        if usage is None:
            return {}
        input_tokens = getattr(usage, "input_tokens", None)
        output_tokens = getattr(usage, "output_tokens", None)
        out = {}
        if isinstance(input_tokens, int):
            out["input_tokens"] = input_tokens
        if isinstance(output_tokens, int):
            out["output_tokens"] = output_tokens
        return out

    @staticmethod
    def _get_auth_error() -> type:
        """Get the AuthenticationError class (lazy import)."""
        try:
            import anthropic
        except ImportError:  # pragma: no cover
            return Exception
        return anthropic.AuthenticationError  # type: ignore[attr-defined]

    @staticmethod
    def _get_rate_limit_error() -> type:
        """Get the RateLimitError class (lazy import)."""
        try:
            import anthropic
        except ImportError:  # pragma: no cover
            return Exception
        return anthropic.RateLimitError  # type: ignore[attr-defined]

    @staticmethod
    def _get_timeout_error() -> type:
        """Get the APITimeoutError class (lazy import)."""
        try:
            import anthropic
        except ImportError:  # pragma: no cover
            return Exception
        return anthropic.APITimeoutError  # type: ignore[attr-defined]

    @staticmethod
    def _get_connection_error() -> type:
        """Get the APIConnectionError class (lazy import)."""
        try:
            import anthropic
        except ImportError:  # pragma: no cover
            return Exception
        return anthropic.APIConnectionError  # type: ignore[attr-defined]

    @staticmethod
    def _get_status_error() -> type:
        """Get the APIStatusError class (lazy import)."""
        try:
            import anthropic
        except ImportError:  # pragma: no cover
            return Exception
        return anthropic.APIStatusError  # type: ignore[attr-defined]


def handle_anthropic_error(exc: Exception, detail_prefix: str = "API error") -> str:
    """
    Convert Anthropic exceptions to user-friendly error messages.

    Consolidated error handler for use across api.py and app.py.

    Args:
        exc: The caught exception.
        detail_prefix: Prefix for the error message.

    Returns:
        User-friendly error message string.
    """
    try:
        import anthropic  # type: ignore
    except ImportError:
        return f"{detail_prefix}: Unknown error"

    if isinstance(exc, anthropic.AuthenticationError):  # type: ignore[attr-defined]
        return f"{detail_prefix}: Invalid API key. Please check your ANTHROPIC_API_KEY configuration."
    if isinstance(exc, anthropic.RateLimitError):  # type: ignore[attr-defined]
        return f"{detail_prefix}: API rate limit exceeded. Please try again in a minute."
    if isinstance(exc, anthropic.APITimeoutError):  # type: ignore[attr-defined]
        return f"{detail_prefix}: Request timed out. Please try again."
    if isinstance(exc, anthropic.APIConnectionError):  # type: ignore[attr-defined]
        return f"{detail_prefix}: Could not connect to API. Please check your connection."
    if isinstance(exc, anthropic.APIStatusError):  # type: ignore[attr-defined]
        return f"{detail_prefix}: API returned status {getattr(exc, 'status_code', 'unknown')}"

    return f"{detail_prefix}: An unexpected error occurred. Please try again."


def build_ai_selector_prompt(query: str, agents: list[dict], *, max_agents: int = 80) -> str:
    """Build prompt for AI agent selection from user query."""
    candidates = []
    for a in (agents or [])[:max_agents]:
        agent_id = (a.get("id") or "").strip()
        if not agent_id:
            continue

        name = (a.get("name") or "").strip()
        description = (a.get("description") or "").strip()
        description = (description[:220] + "…") if len(description) > 220 else description
        category = (a.get("category") or "other").strip()
        frameworks = a.get("frameworks") or []
        frameworks = [str(f).strip() for f in frameworks if f][:3]

        candidates.append(
            f"- {agent_id}: {name} — {description} [{category}; {', '.join(frameworks)}]"
        )

    agent_list = "\n".join(candidates)
    return f"""You recommend the best matching agent examples.

Available Agents:
{agent_list}

User Request: "{query}"

Return the top 5 agent IDs with 1-2 sentences each:
1. **agent_id**: reason
...
If nothing fits, say what tags/frameworks the user should search for.
"""


def build_webmanus_prompt(user_problem: str, agents: list[dict], *, max_agents: int = 30) -> str:
    """
    Consumer-focused prompt for WebManus.com.

    The model should return JSON only (no markdown, no prose around it).

    Args:
        user_problem: User's described problem.
        agents: List of available agents.
        max_agents: Maximum number of agents to include in prompt.

    Returns:
        Prompt string for LLM.
    """
    """
    Consumer-focused prompt for WebManus.com.

    The model should return JSON only (no markdown, no prose around it).
    """
    user_problem = (user_problem or "").strip()

    lines = []
    for a in (agents or [])[:max_agents]:
        slug = (a.get("slug") or "").strip()
        name = (a.get("name") or "").strip()
        tagline = (a.get("tagline") or "").strip()
        tagline = (tagline[:80] + "…") if len(tagline) > 80 else tagline
        pricing = (a.get("pricing") or "freemium").strip()
        score = a.get("labor_score", 5.0)
        caps = a.get("capabilities") or []
        caps_text = ", ".join([str(c) for c in caps[:3] if c])
        if slug and name:
            lines.append(f"- {slug}: {name} ({pricing}, score:{score}) - {tagline} [{caps_text}]")

    agents_text = "\n".join(lines)

    return f"""You are the Digital HR Manager at WebManus (an AI staffing agency).

A user is describing a boring, repetitive task they want automated.
Your job is to recommend 1-3 AI "workers" that can handle this task.

Available AI Workers:
{agents_text}

User's Problem:
"{user_problem}"

Return JSON only with this schema:
{{
  "recommendations": [
    {{
      "slug": "worker-slug",
      "match_score": 0.95,
      "reason": "2 sentences explaining workflow benefits in consumer-friendly language."
    }}
  ],
  "no_match_suggestion": "If no good match, suggest what kind of AI tool they should look for."
}}

Rules:
1) Maximum 3 recommendations
2) Only recommend if match_score > 0.7
3) No jargon like "RAG" or "LangChain"
4) Focus on outcomes ("what it does for you"), not implementation
"""


def extract_json_object(text: str) -> dict:
    """
    Extract and parse the first JSON object from a model response.

    Supports:
    - fenced ```json blocks
    - raw JSON objects embedded in text

    Args:
        text: Model response text.

    Returns:
        Parsed JSON object as dict.

    Raises:
        AISelectorError: If no valid JSON found.
    """
    """
    Extract and parse the first JSON object from a model response.

    Supports:
    - fenced ```json blocks
    - raw JSON objects embedded in text
    """
    import json
    import re

    raw = (text or "").strip()
    if not raw:
        raise AISelectorError("Empty model response")

    # Prefer ```json fenced blocks
    m = re.search(r"```json\\s*(\\{.*?\\})\\s*```", raw, flags=re.DOTALL | re.IGNORECASE)
    if m:
        return json.loads(m.group(1))

    # Fallback: scan for a JSON object by matching braces.
    start = raw.find("{")
    if start < 0:
        raise AISelectorError("No JSON object found in response")

    depth = 0
    in_str = False
    escape = False
    for i in range(start, len(raw)):
        ch = raw[i]
        if in_str:
            if escape:
                escape = False
            elif ch == "\\\\":
                escape = True
            elif ch == '"':
                in_str = False
            continue

        if ch == '"':
            in_str = True
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                candidate = raw[start : i + 1]
                return json.loads(candidate)

    raise AISelectorError("Unterminated JSON object in response")

def normalize_query_for_cache(query: str) -> str:
    """
    Normalize query text for semantic caching.

    This allows similar queries to share cache entries:
    - "best coding agent" -> "coding agent"
    - "top coding assistant" -> "coding assistant"
    - "show me rag examples" -> "rag example"

    Args:
        query: User query text

    Returns:
        Normalized query string
    """
    import re

    # Convert to lowercase
    normalized = query.lower().strip()

    # Remove common query modifiers that don't change intent
    modifiers = [
        r'\b(best|top|good|great|excellent|recommended)\b',
        r'\b(show me|find|get|give me|i need|i want)\b',
        r'\b(please|thanks|thank you)\b',
        r'\b(a|an|the)\b',
    ]
    for pattern in modifiers:
        normalized = re.sub(pattern, ' ', normalized)

    # Normalize whitespace
    normalized = re.sub(r'\s+', ' ', normalized).strip()

    # Pluralization normalization (simple heuristic)
    normalized = re.sub(r'\b(\w+)s\b', r'\1', normalized)

    return normalized


def make_cache_key(*, model: str, query: str, candidate_ids: Iterable[str]) -> str:
    """
    Generate cache key for AI selector requests.

    Uses semantic normalization to allow similar queries to share cache:
    - "best coding agent" and "top coding assistant" may share cache
    - Query normalization removes filler words and modifiers
    - Candidate IDs are included to ensure different search results get different cache

    Args:
        model: LLM model identifier
        query: User query text
        candidate_ids: List of agent IDs being considered

    Returns:
        SHA256 hash as cache key
    """
    normalized_query = normalize_query_for_cache(query)
    joined = ",".join([c for c in candidate_ids if c])
    return _sha256(f"{model}\n{normalized_query}\n{joined}")


# CacheEntry is re-exported from src.cache for backward compatibility
# The actual class is defined in src/cache.CacheEntry
# We keep this definition here for type hints and documentation
@dataclass
class CacheEntry:
    created_at: float
    model: str
    text: str
    usage: dict
    cost_usd: float


# FileTTLCache is now an alias to SQLiteCache for backward compatibility
# The SQLite implementation provides O(log n) lookups instead of O(n)
FileTTLCache = SQLiteCache

# DailyBudget is now an alias to SQLiteBudget for backward compatibility
# The SQLite implementation provides atomic operations and thread safety
DailyBudget = SQLiteBudget


def estimate_tokens_for_text(text: str) -> int:
    """
    Estimate token count for text (heuristic).

    Uses ~4 chars/token for English text.
    Only used for conservative pre-checks.
    """
    # Heuristic (no tokenizer dependency): ~4 chars/token for English-ish text.
    # This is only used for conservative pre-checks.
    return max(1, int(len(text) / 4))


def default_model_pricing_usd_per_million_tokens(model: str) -> tuple[float, float]:
    """
    Returns (input_usd_per_million, output_usd_per_million).

    Defaults are intentionally minimal and can be overridden by env vars:
    - ANTHROPIC_INPUT_USD_PER_MILLION
    - ANTHROPIC_OUTPUT_USD_PER_MILLION

    Raises:
        AISelectorError: If model pricing unknown and not configured.
    """
    """
    Returns (input_usd_per_million, output_usd_per_million).

    Defaults are intentionally minimal and can be overridden by env vars:
    - ANTHROPIC_INPUT_USD_PER_MILLION
    - ANTHROPIC_OUTPUT_USD_PER_MILLION
    """
    import os

    in_override = os.environ.get("ANTHROPIC_INPUT_USD_PER_MILLION")
    out_override = os.environ.get("ANTHROPIC_OUTPUT_USD_PER_MILLION")
    if in_override and out_override:
        return float(in_override), float(out_override)

    # Reasonable default for Claude 3.5 Haiku (override if you change models).
    if "haiku" in (model or "").lower():
        return 0.80, 4.00

    # Unknown model: force explicit configuration to avoid lying about dollars.
    raise AISelectorError(
        "Unknown model pricing. Set ANTHROPIC_INPUT_USD_PER_MILLION and ANTHROPIC_OUTPUT_USD_PER_MILLION."
    )


def estimate_cost_usd(*, model: str, input_tokens: int, output_tokens: int) -> float:
    """Estimate USD cost for a model request."""
    in_usd_m, out_usd_m = default_model_pricing_usd_per_million_tokens(model)
    return (input_tokens / 1_000_000) * in_usd_m + (output_tokens / 1_000_000) * out_usd_m


def require_budget(
    *,
    budget: DailyBudget,
    model: str,
    prompt: str,
    max_output_tokens: int
) -> None:
    """
    Check if estimated cost is within daily budget.

    Raises:
        AISelectorError: If budget would be exceeded.
    """
    # Conservative pre-check using heuristic token counts.
    estimated_input = estimate_tokens_for_text(prompt)
    estimated_cost = estimate_cost_usd(model=model, input_tokens=estimated_input, output_tokens=max_output_tokens)
    if budget.would_exceed(estimated_cost):
        raise AISelectorError("Daily AI budget exceeded. Please try again tomorrow.")


def extract_usage(response: Any) -> dict:
    """Extract token usage from Anthropic response."""
    usage = getattr(response, "usage", None)
    if usage is None:
        return {}
    input_tokens = getattr(usage, "input_tokens", None)
    output_tokens = getattr(usage, "output_tokens", None)
    out = {}
    if isinstance(input_tokens, int):
        out["input_tokens"] = input_tokens
    if isinstance(output_tokens, int):
        out["output_tokens"] = output_tokens
    return out


def sanitize_final_text(raw_text: str) -> str:
    """
    Sanitize LLM output text for display.

    Args:
        raw_text: Raw LLM response text.

    Returns:
        Sanitized text safe for display.
    """
    try:
        return sanitize_llm_output(raw_text, allow_markdown=True)
    except ValidationError:
        return "AI response could not be safely displayed."
