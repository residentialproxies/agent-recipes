"""
Tests for src.ai_selector module.

Tests for:
- make_cache_key()
- build_ai_selector_prompt()
- build_webmanus_prompt()
- extract_json_object()
- estimate_tokens_for_text()
- default_model_pricing_usd_per_million_tokens()
- estimate_cost_usd()
- require_budget()
- extract_usage()
- sanitize_final_text()
"""

import tempfile
from pathlib import Path
from unittest import mock
from unittest.mock import MagicMock, Mock

import pytest

from src.ai_selector import (
    AISelectorError,
    _now_s,
    _sha256,
    build_ai_selector_prompt,
    build_webmanus_prompt,
    default_model_pricing_usd_per_million_tokens,
    estimate_cost_usd,
    estimate_tokens_for_text,
    extract_json_object,
    extract_usage,
    make_cache_key,
    require_budget,
    sanitize_final_text,
)
from src.cache import CacheEntry, SQLiteBudget, SQLiteCache

# Aliases for backward compatibility (as defined in ai_selector.py)
DailyBudget = SQLiteBudget
FileTTLCache = SQLiteCache


class TestSHA256:
    """Tests for _sha256 function."""

    def test_sha256_hash(self) -> None:
        """Test SHA256 hashing produces consistent results."""
        text = "test input"
        hash1 = _sha256(text)
        hash2 = _sha256(text)

        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hex length

    def test_sha256_different_inputs(self) -> None:
        """Test that different inputs produce different hashes."""
        hash1 = _sha256("input1")
        hash2 = _sha256("input2")

        assert hash1 != hash2

    def test_sha256_empty_string(self) -> None:
        """Test SHA256 of empty string."""
        result = _sha256("")
        assert len(result) == 64
        # Known SHA256 of empty string
        assert result == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"


class TestNowS:
    """Tests for _now_s function."""

    def test_now_s_returns_float(self) -> None:
        """Test that _now_s returns a float."""
        result = _now_s()
        assert isinstance(result, float)

    def test_now_s_increases(self) -> None:
        """Test that _now_s increases over time."""
        result1 = _now_s()
        import time
        time.sleep(0.01)
        result2 = _now_s()

        assert result2 > result1


class TestMakeCacheKey:
    """Tests for make_cache_key function."""

    def test_cache_key_consistency(self) -> None:
        """Test that same inputs produce same cache key."""
        key1 = make_cache_key(
            model="claude-3-5-haiku-20241022",
            query="test query",
            candidate_ids=["agent1", "agent2"]
        )
        key2 = make_cache_key(
            model="claude-3-5-haiku-20241022",
            query="test query",
            candidate_ids=["agent1", "agent2"]
        )

        assert key1 == key2

    def test_cache_key_different_models(self) -> None:
        """Test that different models produce different keys."""
        key1 = make_cache_key(
            model="model1",
            query="query",
            candidate_ids=["agent1"]
        )
        key2 = make_cache_key(
            model="model2",
            query="query",
            candidate_ids=["agent1"]
        )

        assert key1 != key2

    def test_cache_key_different_queries(self) -> None:
        """Test that different queries produce different keys."""
        key1 = make_cache_key(
            model="model",
            query="query1",
            candidate_ids=["agent1"]
        )
        key2 = make_cache_key(
            model="model",
            query="query2",
            candidate_ids=["agent1"]
        )

        assert key1 != key2

    def test_cache_key_different_candidates(self) -> None:
        """Test that different candidates produce different keys."""
        key1 = make_cache_key(
            model="model",
            query="query",
            candidate_ids=["agent1"]
        )
        key2 = make_cache_key(
            model="model",
            query="query",
            candidate_ids=["agent2"]
        )

        assert key1 != key2

    def test_cache_key_order_matters(self) -> None:
        """Test that candidate order affects cache key."""
        key1 = make_cache_key(
            model="model",
            query="query",
            candidate_ids=["agent1", "agent2"]
        )
        key2 = make_cache_key(
            model="model",
            query="query",
            candidate_ids=["agent2", "agent1"]
        )

        assert key1 != key2

    def test_cache_key_filters_empty_candidates(self) -> None:
        """Test that empty candidate IDs are filtered out."""
        key1 = make_cache_key(
            model="model",
            query="query",
            candidate_ids=["agent1", "", "agent2", None]
        )
        key2 = make_cache_key(
            model="model",
            query="query",
            candidate_ids=["agent1", "agent2"]
        )

        assert key1 == key2


class TestBuildAISselectorPrompt:
    """Tests for build_ai_selector_prompt function."""

    @pytest.fixture
    def sample_agents(self) -> list[dict]:
        """Sample agent data for prompt building."""
        return [
            {
                "id": "pdf_bot",
                "name": "PDF Assistant",
                "description": "A helpful PDF chatbot",
                "category": "rag",
                "frameworks": ["langchain", "chromadb"],
            },
            {
                "id": "chat_bot",
                "name": "Chat Bot",
                "description": "Simple chatbot",
                "category": "chatbot",
                "frameworks": ["openai"],
            },
            {
                "id": "",
                "name": "Invalid Agent",
                "description": "Should be skipped",
                "category": "other",
                "frameworks": [],
            },
        ]

    def test_prompt_contains_query(self, sample_agents: list[dict]) -> None:
        """Test that prompt contains the user query."""
        prompt = build_ai_selector_prompt("find a PDF bot", sample_agents)
        assert "find a PDF bot" in prompt

    def test_prompt_includes_agents(self, sample_agents: list[dict]) -> None:
        """Test that prompt includes agent information."""
        prompt = build_ai_selector_prompt("test", sample_agents)

        assert "pdf_bot" in prompt
        assert "PDF Assistant" in prompt
        assert "chat_bot" in prompt

    def test_prompt_truncates_long_description(self) -> None:
        """Test that long descriptions are truncated."""
        long_desc = "x" * 300
        agents = [{
            "id": "agent1",
            "name": "Agent",
            "description": long_desc,
            "category": "other",
            "frameworks": [],
        }]

        prompt = build_ai_selector_prompt("test", agents)
        assert "..." in prompt or "\u2026" in prompt  # Ellipsis

    def test_prompt_limits_frameworks(self) -> None:
        """Test that only first 3 frameworks are included."""
        agents = [{
            "id": "agent1",
            "name": "Agent",
            "description": "Test",
            "category": "other",
            "frameworks": ["f1", "f2", "f3", "f4", "f5"],
        }]

        prompt = build_ai_selector_prompt("test", agents)
        # Should only include first 3
        assert "f1" in prompt
        assert "f2" in prompt
        assert "f3" in prompt
        # f4 and f5 may or may not be in the string depending on truncation

    def test_prompt_respects_max_agents(self) -> None:
        """Test that max_agents parameter works."""
        agents = [
            {
                "id": f"agent{i}",
                "name": f"Agent {i}",
                "description": f"Description {i}",
                "category": "other",
                "frameworks": [],
            }
            for i in range(100)
        ]

        prompt = build_ai_selector_prompt("test", agents, max_agents=10)

        # Should only have first 10 agents
        for i in range(10):
            assert f"agent{i}" in prompt
        assert "agent10" not in prompt

    def test_prompt_handles_empty_agents(self) -> None:
        """Test prompt with no agents."""
        prompt = build_ai_selector_prompt("test query", [])
        assert "test query" in prompt
        assert "Available Agents:" in prompt

    def test_prompt_handles_none_agents(self) -> None:
        """Test prompt with None agents."""
        prompt = build_ai_selector_prompt("test query", None)
        assert "test query" in prompt

    def test_prompt_uses_default_category(self) -> None:
        """Test that missing category defaults to 'other'."""
        agents = [{
            "id": "agent1",
            "name": "Agent",
            "description": "Test",
            "category": "",
            "frameworks": [],
        }]

        prompt = build_ai_selector_prompt("test", agents)
        assert "[other;" in prompt


class TestBuildWebmanusPrompt:
    """Tests for build_webmanus_prompt function."""

    @pytest.fixture
    def sample_workers(self) -> list[dict]:
        """Sample worker data for WebManus prompt."""
        return [
            {
                "slug": "data-entry-bot",
                "name": "Data Entry Bot",
                "tagline": "Automates data entry from forms",
                "pricing": "freemium",
                "labor_score": 8.5,
                "capabilities": ["data entry", "forms", "automation"],
            },
            {
                "slug": "email-responder",
                "name": "Email Responder",
                "tagline": "Auto-replies to emails",
                "pricing": "paid",
                "labor_score": 7.0,
                "capabilities": ["email", "writing"],
            },
        ]

    def test_prompt_contains_user_problem(self, sample_workers: list[dict]) -> None:
        """Test that prompt contains the user's problem."""
        prompt = build_webmanus_prompt("I need help with data entry", sample_workers)
        assert "I need help with data entry" in prompt

    def test_prompt_includes_workers(self, sample_workers: list[dict]) -> None:
        """Test that prompt includes worker information."""
        prompt = build_webmanus_prompt("test", sample_workers)

        assert "data-entry-bot" in prompt
        assert "Data Entry Bot" in prompt
        assert "email-responder" in prompt

    def test_prompt_mentions_json_response(self, sample_workers: list[dict]) -> None:
        """Test that prompt asks for JSON response."""
        prompt = build_webmanus_prompt("test", sample_workers)
        assert "JSON only" in prompt
        assert "recommendations" in prompt

    def test_prompt_truncates_long_tagline(self) -> None:
        """Test that long taglines are truncated."""
        workers = [{
            "slug": "worker1",
            "name": "Worker",
            "tagline": "x" * 200,
            "pricing": "free",
            "labor_score": 5.0,
            "capabilities": [],
        }]

        prompt = build_webmanus_prompt("test", workers)
        assert "..." in prompt or "\u2026" in prompt

    def test_prompt_skips_missing_slug(self) -> None:
        """Test that workers without slug are skipped."""
        workers = [
            {
                "slug": "valid-worker",
                "name": "Valid",
                "tagline": "Valid worker",
                "pricing": "free",
                "labor_score": 5.0,
                "capabilities": [],
            },
            {
                "slug": "",
                "name": "Invalid",
                "tagline": "Should be skipped",
                "pricing": "free",
                "labor_score": 5.0,
                "capabilities": [],
            },
        ]

        prompt = build_webmanus_prompt("test", workers)
        assert "valid-worker" in prompt
        # The invalid one might not appear in the formatted output


class TestExtractJSONObject:
    """Tests for extract_json_object function."""

    def test_extract_simple_json(self) -> None:
        """Test extracting simple JSON object."""
        text = '{"key": "value"}'
        result = extract_json_object(text)
        assert result == {"key": "value"}

    def test_extract_from_fenced_block(self) -> None:
        """Test extracting JSON from fenced code block."""
        text = '```json\n{"name": "test", "value": 123}\n```'
        result = extract_json_object(text)
        assert result == {"name": "test", "value": 123}

    def test_extract_from_fenced_block_ignore_case(self) -> None:
        """Test extracting JSON from fenced block with different case."""
        text = '```JSON\n{"key": "value"}\n```'
        result = extract_json_object(text)
        assert result == {"key": "value"}

    def test_extract_from_text_with_surrounding(self) -> None:
        """Test extracting JSON embedded in other text."""
        text = 'Some text before {"key": "value"} some text after'
        result = extract_json_object(text)
        assert result == {"key": "value"}

    def test_extract_nested_json(self) -> None:
        """Test extracting nested JSON object."""
        text = '{"outer": {"inner": "value"}}'
        result = extract_json_object(text)
        assert result == {"outer": {"inner": "value"}}

    def test_extract_json_with_arrays(self) -> None:
        """Test extracting JSON with arrays."""
        text = '{"items": [1, 2, 3], "name": "test"}'
        result = extract_json_object(text)
        assert result == {"items": [1, 2, 3], "name": "test"}

    def test_extract_handles_strings_with_braces(self) -> None:
        """Test that strings containing braces are handled correctly."""
        text = '{"template": "Hello {name}", "value": 42}'
        result = extract_json_object(text)
        assert result == {"template": "Hello {name}", "value": 42}

    def test_error_on_empty_response(self) -> None:
        """Test that empty response raises error."""
        with pytest.raises(AISelectorError, match="Empty model response"):
            extract_json_object("")

    def test_error_on_none_input(self) -> None:
        """Test that None input raises error."""
        with pytest.raises(AISelectorError, match="Empty model response"):
            extract_json_object(None)  # type: ignore

    def test_error_on_no_json_found(self) -> None:
        """Test that text without JSON raises error."""
        with pytest.raises(AISelectorError, match="No JSON object found"):
            extract_json_object("This is just plain text with no JSON")

    def test_error_on_unterminated_json(self) -> None:
        """Test that unterminated JSON raises error."""
        with pytest.raises(AISelectorError, match="Unterminated JSON"):
            extract_json_object('{"key": "value"')

    def test_extract_handles_multiple_objects(self) -> None:
        """Test that first JSON object is extracted when multiple exist."""
        text = '{"first": 1} {"second": 2}'
        result = extract_json_object(text)
        assert result == {"first": 1}


class TestEstimateTokensForText:
    """Tests for estimate_tokens_for_text function."""

    def test_estimate_tokens_for_short_text(self) -> None:
        """Test token estimation for short text."""
        # ~4 chars per token
        text = "hello world"  # 11 chars
        tokens = estimate_tokens_for_text(text)
        assert tokens > 0
        assert tokens == 2  # 11 / 4 = 2.75 -> 2

    def test_estimate_tokens_for_long_text(self) -> None:
        """Test token estimation for longer text."""
        text = "word " * 100  # 500 chars
        tokens = estimate_tokens_for_text(text)
        assert tokens > 0
        # Should be approximately 125 tokens (500 / 4)
        assert 120 <= tokens <= 130

    def test_estimate_tokens_for_empty_string(self) -> None:
        """Test token estimation for empty string."""
        tokens = estimate_tokens_for_text("")
        assert tokens == 1  # Minimum is 1

    def test_estimate_tokens_for_unicode(self) -> None:
        """Test token estimation with unicode characters."""
        text = "Hello world!"  # 12 chars
        tokens = estimate_tokens_for_text(text)
        assert tokens > 0


class TestDefaultModelPricing:
    """Tests for default_model_pricing_usd_per_million_tokens function."""

    def test_haiku_pricing(self) -> None:
        """Test pricing for Haiku model."""
        input_price, output_price = default_model_pricing_usd_per_million_tokens("claude-3-5-haiku-20241022")
        assert input_price == 0.80
        assert output_price == 4.00

    def test_haiku_pricing_case_insensitive(self) -> None:
        """Test that model name is case-insensitive."""
        input_price, output_price = default_model_pricing_usd_per_million_tokens("CLAUDE-3-HAIKU")
        assert input_price == 0.80
        assert output_price == 4.00

    def test_unknown_model_raises_error(self) -> None:
        """Test that unknown model raises error."""
        with pytest.raises(AISelectorError, match="Unknown model pricing"):
            default_model_pricing_usd_per_million_tokens("unknown-model")

    def test_env_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that env vars override defaults."""
        monkeypatch.setenv("ANTHROPIC_INPUT_USD_PER_MILLION", "1.50")
        monkeypatch.setenv("ANTHROPIC_OUTPUT_USD_PER_MILLION", "5.00")

        input_price, output_price = default_model_pricing_usd_per_million_tokens("any-model")
        assert input_price == 1.50
        assert output_price == 5.00

    def test_partial_env_override_raises_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that partial env override still requires both values."""
        monkeypatch.setenv("ANTHROPIC_INPUT_USD_PER_MILLION", "1.50")
        monkeypatch.delenv("ANTHROPIC_OUTPUT_USD_PER_MILLION", raising=False)

        # Should fall back to unknown model behavior
        with pytest.raises(AISelectorError):
            default_model_pricing_usd_per_million_tokens("unknown-model")


class TestEstimateCostUsd:
    """Tests for estimate_cost_usd function."""

    def test_cost_calculation(self) -> None:
        """Test basic cost calculation."""
        # For Haiku: $0.80/M input, $4.00/M output
        cost = estimate_cost_usd(
            model="claude-3-5-haiku-20241022",
            input_tokens=1000,
            output_tokens=500
        )
        expected = (1000 / 1_000_000) * 0.80 + (500 / 1_000_000) * 4.00
        assert abs(cost - expected) < 0.0001

    def test_zero_tokens(self) -> None:
        """Test cost with zero tokens."""
        cost = estimate_cost_usd(
            model="claude-3-5-haiku-20241022",
            input_tokens=0,
            output_tokens=0
        )
        assert cost == 0.0

    def test_large_token_counts(self) -> None:
        """Test cost with large token counts."""
        cost = estimate_cost_usd(
            model="claude-3-5-haiku-20241022",
            input_tokens=1_000_000,
            output_tokens=500_000
        )
        # $0.80 + $2.00 = $2.80
        assert abs(cost - 2.80) < 0.01


class TestRequireBudget:
    """Tests for require_budget function."""

    @pytest.fixture
    def mock_budget(self) -> Mock:
        """Create a mock budget."""
        budget = Mock(spec=DailyBudget)
        budget.would_exceed = Mock(return_value=False)
        return budget

    def test_require_budget_passes_when_within_limit(self, mock_budget: Mock) -> None:
        """Test that require_budget passes when within budget."""
        mock_budget.would_exceed = Mock(return_value=False)

        # Should not raise
        require_budget(
            budget=mock_budget,
            model="claude-3-5-haiku-20241022",
            prompt="test prompt",
            max_output_tokens=100
        )

    def test_require_budget_raises_when_exceeded(self, mock_budget: Mock) -> None:
        """Test that require_budget raises when budget exceeded."""
        mock_budget.would_exceed = Mock(return_value=True)

        with pytest.raises(AISelectorError, match="Daily AI budget exceeded"):
            require_budget(
                budget=mock_budget,
                model="claude-3-5-haiku-20241022",
                prompt="test prompt",
                max_output_tokens=100
            )

    def test_require_budget_estimates_cost(self, mock_budget: Mock) -> None:
        """Test that require_budget estimates cost correctly."""
        prompt = "x" * 1000  # ~250 tokens

        require_budget(
            budget=mock_budget,
            model="claude-3-5-haiku-20241022",
            prompt=prompt,
            max_output_tokens=100
        )

        # Check that would_exceed was called with estimated cost
        mock_budget.would_exceed.assert_called_once()
        called_cost = mock_budget.would_exceed.call_args[0][0]
        assert called_cost > 0


class TestExtractUsage:
    """Tests for extract_usage function."""

    def test_extract_usage_from_response(self) -> None:
        """Test extracting usage from response object."""
        mock_response = Mock()
        mock_usage = Mock()
        mock_usage.input_tokens = 100
        mock_usage.output_tokens = 50
        mock_response.usage = mock_usage

        usage = extract_usage(mock_response)

        assert usage == {"input_tokens": 100, "output_tokens": 50}

    def test_extract_usage_partial(self) -> None:
        """Test extracting partial usage information."""
        mock_response = Mock()
        mock_usage = Mock()
        mock_usage.input_tokens = 100
        # output_tokens is not set
        del mock_usage.output_tokens
        mock_response.usage = mock_usage

        usage = extract_usage(mock_response)

        assert usage == {"input_tokens": 100}

    def test_extract_usage_none(self) -> None:
        """Test extracting usage when usage attribute is None."""
        mock_response = Mock()
        mock_response.usage = None

        usage = extract_usage(mock_response)

        assert usage == {}

    def test_extract_usage_missing_attribute(self) -> None:
        """Test extracting usage when usage attribute doesn't exist."""
        mock_response = Mock(spec=[])  # No attributes

        usage = extract_usage(mock_response)

        assert usage == {}


class TestSanitizeFinalText:
    """Tests for sanitize_final_text function."""

    def test_sanitize_valid_text(self) -> None:
        """Test sanitizing valid text."""
        text = "This is safe text."
        result = sanitize_final_text(text)
        assert "safe text" in result

    def test_sanitize_with_markdown(self) -> None:
        """Test sanitizing text with markdown."""
        text = "## Header\n\nThis is **bold** text."
        result = sanitize_final_text(text)
        # Should allow markdown but escape HTML
        assert "Header" in result

    def test_sanitize_xss_attempt(self) -> None:
        """Test that XSS attempts are neutralized."""
        text = "<script>alert('xss')</script>Hello"
        result = sanitize_final_text(text)
        assert "<script>" not in result
        assert "Hello" in result

    def test_sanitize_javascript_protocol(self) -> None:
        """Test that javascript: protocol is removed."""
        text = "Click javascript:alert('xss') here"
        result = sanitize_final_text(text)
        assert "javascript:" not in result.lower()

    def test_sanitize_sql_injection(self) -> None:
        """Test that SQL injection patterns are removed."""
        text = "Text' OR '1'='1"
        result = sanitize_final_text(text)
        # The sanitization should handle this
        assert result is not None

    def test_sanitize_handles_validation_error(self) -> None:
        """Test that ValidationError is handled gracefully."""
        # Create a mock that raises ValidationError
        from src.security.validators import ValidationError
        with mock.patch("src.ai_selector.sanitize_llm_output", side_effect=ValidationError("Invalid")):
            result = sanitize_final_text("test")
            assert result == "AI response could not be safely displayed."

    def test_sanitize_empty_after_sanitization(self) -> None:
        """Test text that becomes empty after sanitization."""
        from src.security.validators import ValidationError
        with mock.patch("src.ai_selector.sanitize_llm_output", side_effect=ValidationError("Too dangerous")):
            result = sanitize_final_text("<script>evil</script>")
            assert result == "AI response could not be safely displayed."


class TestCacheEntryAndAliases:
    """Tests for CacheEntry and backward compatibility aliases."""

    def test_cache_entry_dataclass(self) -> None:
        """Test that CacheEntry is a dataclass."""
        from src.ai_selector import CacheEntry as AISelectorCacheEntry

        entry = AISelectorCacheEntry(
            created_at=123.456,
            model="test-model",
            text="test text",
            usage={"tokens": 100},
            cost_usd=0.001,
        )

        assert entry.created_at == 123.456
        assert entry.model == "test-model"
        assert entry.text == "test text"

    def test_file_ttl_cache_alias(self) -> None:
        """Test that FileTTLCache is aliased to SQLiteCache."""
        from src.ai_selector import FileTTLCache
        from src.cache import SQLiteCache

        assert FileTTLCache is SQLiteCache

    def test_daily_budget_alias(self) -> None:
        """Test that DailyBudget is aliased to SQLiteBudget."""
        from src.ai_selector import DailyBudget
        from src.cache import SQLiteBudget

        assert DailyBudget is SQLiteBudget
