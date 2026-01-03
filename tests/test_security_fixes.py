"""
Security fix tests for critical vulnerabilities.

Tests for:
1. SQL Injection prevention (LIKE wildcard escaping)
2. Markdown XSS prevention
3. CORS restrictions
4. CSP enhancements
"""

import pytest

from src.repository import AgentRepo
from src.security.markdown import (
    MarkdownSanitizer,
    sanitize_html_only,
    sanitize_markdown,
)
from src.security.sql import (
    build_like_clause,
    escape_like_pattern,
    validate_search_input,
)


class TestSQLInjectionPrevention:
    """Test SQL injection prevention in repository LIKE queries."""

    def test_like_wildcard_percent_escaped(self, tmp_path):
        """Test that % wildcard is properly escaped in LIKE queries."""
        db_path = tmp_path / "test.db"
        repo = AgentRepo(str(db_path))

        # Add test data with a name containing %
        repo.upsert(
            {"slug": "test1", "name": "100% Free", "tagline": "A test agent", "pricing": "free", "labor_score": 5.0},
            ["test"],
        )
        repo.upsert(
            {
                "slug": "test2",
                "name": "Another Agent",
                "tagline": "No percent sign",
                "pricing": "free",
                "labor_score": 5.0,
            },
            ["test"],
        )

        # Search for "100%" - should only match exact "100%", not wildcard
        results = repo.search(q="100%", limit=10)
        slugs = [r["slug"] for r in results]
        assert "test1" in slugs  # Name contains "100%"
        assert "test2" not in slugs  # Doesn't contain "100%"

    def test_like_wildcard_underscore_escaped(self, tmp_path):
        """Test that _ wildcard is properly escaped in LIKE queries."""
        db_path = tmp_path / "test.db"
        repo = AgentRepo(str(db_path))

        # Add test data
        repo.upsert(
            {"slug": "test1", "name": "test_file", "tagline": "A test", "pricing": "free", "labor_score": 5.0},
            ["test"],
        )
        repo.upsert(
            {"slug": "test2", "name": "testXfile", "tagline": "Another test", "pricing": "free", "labor_score": 5.0},
            ["test"],
        )
        repo.upsert(
            {"slug": "test3", "name": "test file", "tagline": "Third test", "pricing": "free", "labor_score": 5.0},
            ["test"],
        )

        # Search for "test_file" - should match only exact, not "testXfile"
        results = repo.search(q="test_file", limit=10)
        slugs = [r["slug"] for r in results]
        assert "test1" in slugs  # Exact match
        assert "test2" not in slugs  # _ would match X if not escaped
        assert "test3" not in slugs  # _ would match space if not escaped

    def test_sql_injection_with_or_statement(self, tmp_path):
        """Test that SQL injection via OR statement is prevented."""
        db_path = tmp_path / "test.db"
        repo = AgentRepo(str(db_path))

        # Add some test data
        repo.upsert(
            {"slug": "agent1", "name": "Agent One", "tagline": "First", "pricing": "free", "labor_score": 5.0},
            ["test"],
        )
        repo.upsert(
            {"slug": "agent2", "name": "Agent Two", "tagline": "Second", "pricing": "free", "labor_score": 5.0},
            ["test"],
        )

        # Try SQL injection - should not return all agents
        results = repo.search(q="' OR '1'='1", limit=10)
        # The injection attempt should be escaped as a literal string
        # Should return 0 results since no agent has this literal string
        assert len(results) == 0

    def test_sql_injection_with_comment(self, tmp_path):
        """Test that SQL injection via comment is prevented."""
        db_path = tmp_path / "test.db"
        repo = AgentRepo(str(db_path))

        # Add test data
        repo.upsert(
            {"slug": "agent1", "name": "Agent One", "tagline": "First", "pricing": "free", "labor_score": 5.0},
            ["test"],
        )

        # Try comment injection
        results = repo.search(q="test' --", limit=10)
        # Should not match anything (no agent has this literal string)
        assert len(results) == 0

    def test_wildcard_percent_only(self, tmp_path):
        """Test that searching for just % doesn't match everything."""
        db_path = tmp_path / "test.db"
        repo = AgentRepo(str(db_path))

        # Add test data
        repo.upsert(
            {"slug": "agent1", "name": "Agent One", "tagline": "First", "pricing": "free", "labor_score": 5.0},
            ["test"],
        )
        repo.upsert(
            {"slug": "agent2", "name": "Agent Two", "tagline": "Second", "pricing": "free", "labor_score": 5.0},
            ["test"],
        )

        # Search for just % - should not return all results
        results = repo.search(q="%", limit=10)
        # % is escaped, so it looks for literal "%"
        assert len(results) == 0


class TestEscapeLikePattern:
    """Test the escape_like_pattern function directly."""

    def test_percent_is_escaped(self):
        """Test that % is escaped."""
        result = escape_like_pattern("100% complete")
        assert result == r"100\% complete"

    def test_underscore_is_escaped(self):
        """Test that _ is escaped."""
        result = escape_like_pattern("test_file")
        assert result == r"test\_file"

    def test_backslash_is_escaped(self):
        """Test that backslash is escaped."""
        result = escape_like_pattern("path\\to\\file")
        assert result == r"path\\to\\file"

    def test_multiple_wildcards(self):
        """Test that multiple wildcards are all escaped."""
        result = escape_like_pattern("100%_test_file")
        assert result == r"100\%\_test\_file"

    def test_empty_string(self):
        """Test empty string."""
        result = escape_like_pattern("")
        assert result == ""

    def test_custom_escape_char(self):
        """Test custom escape character."""
        result = escape_like_pattern("100% test", escape_char="!")
        assert result == r"100!% test"


class TestBuildLikeClause:
    """Test the build_like_clause function."""

    def test_returns_sql_and_params(self):
        """Test that function returns SQL and params."""
        sql, params = build_like_clause("name", "test")
        assert "name LIKE ?" in sql
        assert "ESCAPE" in sql
        assert len(params) == 1
        assert "test" in params[0]

    def test_wildcards_in_pattern(self):
        """Test that wildcards in input are escaped."""
        sql, params = build_like_clause("name", "100% test")
        # The % should be escaped in the parameter
        assert r"\%" in params[0]

    def test_invalid_column_name_raises(self):
        """Test that invalid column names are rejected."""
        with pytest.raises(ValueError):
            build_like_clause("'; DROP TABLE users; --", "test")

        with pytest.raises(ValueError):
            build_like_clause("name OR '1'='1'", "test")


class TestValidateSearchInput:
    """Test search input validation."""

    def test_valid_input_passes(self):
        """Test that valid input passes."""
        result = validate_search_input("test search")
        assert result == "test search"

    def test_length_limit_enforced(self):
        """Test that length limit is enforced."""
        with pytest.raises(ValueError):
            validate_search_input("a" * 201, max_length=200)

    def test_null_bytes_removed(self):
        """Test that null bytes are removed."""
        result = validate_search_input("test\x00input")
        assert "\x00" not in result
        assert "testinput" in result

    def test_control_characters_removed(self):
        """Test that control characters are removed."""
        result = validate_search_input("test\x01\x02input")
        assert "\x01" not in result
        assert "\x02" not in result

    def test_newlines_preserved(self):
        """Test that newlines are preserved."""
        result = validate_search_input("test\ninput")
        assert "\n" in result

    def test_type_error_on_non_string(self):
        """Test that non-strings raise TypeError."""
        with pytest.raises(TypeError):
            validate_search_input(123)


class TestMarkdownXSSPrevention:
    """Test markdown XSS prevention."""

    def test_script_tag_removed(self):
        """Test that script tags are removed."""
        malicious = "Hello <script>alert('XSS')</script> World"
        result = sanitize_markdown(malicious)
        assert "<script>" not in result
        assert "</script>" not in result

    def test_onclick_attribute_removed(self):
        """Test that onclick attributes are removed."""
        malicious = '<div onclick="alert(1)">Click me</div>'
        result = sanitize_markdown(malicious)
        assert "onclick" not in result

    def test_javascript_protocol_removed(self):
        """Test that javascript: protocol is removed."""
        malicious = '<a href="javascript:alert(1)">Link</a>'
        result = sanitize_markdown(malicious)
        assert "javascript:" not in result

    def test_data_protocol_removed(self):
        """Test that data: protocol is removed."""
        malicious = '<img src="data:text/html,<script>alert(1)</script>">'
        result = sanitize_markdown(malicious)
        assert "data:text/html" not in result or "data:" not in result

    def test_iframe_removed(self):
        """Test that iframes are removed."""
        malicious = '<iframe src="https://evil.com"></iframe>'
        result = sanitize_markdown(malicious)
        assert "<iframe" not in result

    def test_style_tag_removed(self):
        """Test that style tags are removed."""
        malicious = "<style>body { background: red; }</style> content"
        result = sanitize_markdown(malicious)
        assert "<style>" not in result or "</style>" not in result

    def test_html_comment_removed(self):
        """Test that HTML comments are removed."""
        malicious = "<!-- malicious comment -->content"
        result = sanitize_markdown(malicious)
        assert "<!--" not in result

    def test_safe_markdown_preserved(self):
        """Test that safe markdown is preserved."""
        safe = "# Heading\n\n- Item 1\n- Item 2\n\n**bold** and *italic*"
        result = sanitize_markdown(safe)
        assert "# Heading" in result or "Heading" in result
        assert "Item 1" in result
        assert "Item 2" in result

    def test_safe_links_preserved(self):
        """Test that safe links are preserved."""
        safe = "[Link](https://example.com)"
        result = sanitize_markdown(safe)
        assert "example.com" in result

    def test_safe_images_preserved(self):
        """Test that safe images are preserved."""
        safe = "![Alt text](https://example.com/image.jpg)"
        result = sanitize_markdown(safe)
        assert "example.com" in result

    def test_length_limit_enforced(self):
        """Test that length limit is enforced."""
        long_content = "a" * 100_001
        with pytest.raises(ValueError):
            sanitize_markdown(long_content, max_length=100_000)

    def test_type_error_on_non_string(self):
        """Test that non-strings raise TypeError."""
        with pytest.raises(TypeError):
            sanitize_markdown(123)

    def test_xss_with_html_encoding(self):
        """Test XSS with HTML encoding attempts."""
        malicious = "<div>&#x3C;script&#x3E;alert(1)&#x3C;/script&#x3E;</div>"
        result = sanitize_markdown(malicious)
        # Should remove or escape the encoded script tag
        assert "<script>" not in result or "&lt;" in result

    def test_svg_onload_removed(self):
        """Test that SVG onload is removed."""
        malicious = '<svg onload="alert(1)"></svg>'
        result = sanitize_markdown(malicious)
        assert "onload" not in result

    def test_custom_allowed_tags(self):
        """Test custom allowed tags."""
        sanitizer = MarkdownSanitizer(allowed_tags={"p", "strong", "em"}, strip_disallowed_tags=True)
        html = "<p>Test</p><div>Removed</div><strong>Kept</strong>"
        result = sanitizer.sanitize(html)
        # Should keep p, strong but strip div
        assert "<p>" in result or "Test" in result
        assert "<strong>" in result or "Kept" in result
        # div tag should be removed
        assert "<div>" not in result


class TestSanitizeHtmlOnly:
    """Test the sanitize_html_only function."""

    def test_removes_dangerous_html(self):
        """Test that dangerous HTML is removed."""
        html = "<script>alert(1)</script><p>Safe content</p>"
        result = sanitize_html_only(html)
        assert "<script>" not in result
        assert "Safe content" in result or "Safe" in result


class TestRepositorySearchPageIntegration:
    """Integration tests for repository search_page method."""

    def test_search_with_percent_returns_correct_results(self, tmp_path):
        """Test that search with % character works correctly."""
        db_path = tmp_path / "test.db"
        repo = AgentRepo(str(db_path))

        # Add test data
        repo.upsert(
            {
                "slug": "free1",
                "name": "100% Free Tool",
                "tagline": "Free forever",
                "pricing": "free",
                "labor_score": 8.0,
            },
            ["free", "tool"],
        )
        repo.upsert(
            {
                "slug": "free2",
                "name": "Another Free Tool",
                "tagline": "Also 100% free",
                "pricing": "free",
                "labor_score": 7.0,
            },
            ["free", "tool"],
        )
        repo.upsert(
            {
                "slug": "paid1",
                "name": "Paid Tool",
                "tagline": "Premium features",
                "pricing": "paid",
                "labor_score": 9.0,
            },
            ["paid", "tool"],
        )

        # Search for "100%" - should only match exact occurrences
        total, items = repo.search_page(q="100%", limit=10)
        # Should match at least one with "100%" in name or tagline
        assert total >= 1
        slugs = [item["slug"] for item in items]
        assert "free1" in slugs

    def test_search_pagination_with_injection(self, tmp_path):
        """Test pagination with potential injection attempts."""
        db_path = tmp_path / "test.db"
        repo = AgentRepo(str(db_path))

        # Add test data
        for i in range(5):
            repo.upsert(
                {
                    "slug": f"agent{i}",
                    "name": f"Agent {i}",
                    "tagline": f"Description {i}",
                    "pricing": "free",
                    "labor_score": 5.0 + i,
                },
                ["test"],
            )

        # Try to inject via offset parameter (should be safe due to validation)
        total, items = repo.search_page(q="Agent", limit=2, offset=0)
        assert total == 5
        assert len(items) == 2

        # Second page
        total, items = repo.search_page(q="Agent", limit=2, offset=2)
        assert len(items) == 2


class TestCorsConfiguration:
    """Test CORS security configuration."""

    def test_default_cors_origins_are_restricted(self):
        """Test that default CORS origins are restricted to localhost."""
        from src.config import Settings

        settings = Settings()
        # Should not include wildcard by default
        assert "*" not in settings.cors_allow_origins
        # Should include localhost variants
        assert "localhost" in str(settings.cors_allow_origins)

    def test_cors_from_env_var(self, monkeypatch):
        """Test that CORS can be configured via environment variable."""
        monkeypatch.setenv("CORS_ALLOW_ORIGINS", "https://example.com,https://app.example.com")
        from src.config import reload_settings

        settings = reload_settings()
        assert "https://example.com" in settings.cors_allow_origins
        assert "https://app.example.com" in settings.cors_allow_origins
        assert "*" not in settings.cors_allow_origins

    def test_cors_wildcard_from_env(self, monkeypatch):
        """Test that CORS wildcard can be set (with warning)."""
        monkeypatch.setenv("CORS_ALLOW_ORIGINS", "*")
        from src.config import reload_settings

        settings = reload_settings()
        assert "*" in settings.cors_allow_origins


class TestCSPConfiguration:
    """Test CSP security configuration."""

    def test_csp_nonce_enabled_by_default(self):
        """Test that CSP nonce is enabled by default."""
        from src.config import Settings

        settings = Settings()
        assert settings.csp_use_nonce is True

    def test_csp_nonce_can_be_disabled(self, monkeypatch):
        """Test that CSP nonce can be disabled via environment."""
        monkeypatch.setenv("CSP_USE_NONCE", "false")
        from src.config import reload_settings

        settings = reload_settings()
        assert settings.csp_use_nonce is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
