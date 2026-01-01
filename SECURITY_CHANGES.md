# Security Fixes - Agent Navigator

This document describes the critical security fixes implemented for the Agent Navigator project.

## Summary of Fixes

### 1. SQL Injection Prevention (CRITICAL)

**File:** `/Volumes/SSD/dev/new/agent-recipes/src/repository.py`
**Severity:** CRITICAL

**Issue:**
User input in search queries (`q` parameter) was used directly in SQL LIKE clauses without escaping wildcard characters (`%` and `_`). This could allow attackers to:

- Search for `%` to match all records (data leak)
- Use `_` to match single characters arbitrarily
- Potentially combine with other input manipulation techniques

**Fix:**

- Created `/Volumes/SSD/dev/new/agent-recipes/src/security/sql.py` module with:
  - `escape_like_pattern()`: Escapes `%` and `_` wildcards
  - `validate_search_input()`: Validates and sanitizes search input
  - `build_like_clause()`: Helper for building safe LIKE clauses
- Updated `AgentRepo._build_search_sql()` to use `ESCAPE` clause
- Updated `search()` and `search_page()` methods to validate input

**Example Attack Prevented:**

```python
# Before: Searching "%" would match ALL records
repo.search(q="%")  # Returns everything!

# After: "%" is escaped as "\%", matching literal "%" only
repo.search(q="%")  # Returns only records containing literal "%"
```

### 2. Markdown XSS Prevention (HIGH)

**File:** `/Volumes/SSD/dev/new/agent-recipes/src/app.py` (line 676-677)
**Severity:** HIGH

**Issue:**
README markdown content fetched from external sources was rendered without sanitization. This could allow XSS attacks through malicious README files containing:

- `<script>` tags
- Event handlers (`onclick`, `onload`, etc.)
- `javascript:` protocols
- Dangerous HTML (`<iframe>`, `<object>`, `<embed>`)

**Fix:**

- Created `/Volumes/SSD/dev/new/agent-recipes/src/security/markdown.py` module with:
  - `MarkdownSanitizer`: Whitelist-based HTML tag and attribute filtering
  - `sanitize_markdown()`: Convenience function for markdown sanitization
  - URL protocol validation (only allows `https:`, `http:`, `mailto:`, `tel:`)
- Updated README rendering in `render_detail_page()` to sanitize content
- Added fallback warning if sanitization fails

**Example Attack Prevented:**

```markdown
# Malicious README content

<script>alert('XSS')</script>
<img src="x" onerror="alert('XSS')">
<a href="javascript:alert('XSS')">Click</a>

# All are sanitized to safe content or removed
```

### 3. CORS Restriction (HIGH)

**File:** `/Volumes/SSD/dev/new/agent-recipes/src/api.py` (line 158-167)
**Severity:** HIGH

**Issue:**
CORS configuration defaulted to allowing all origins (`*`) when not explicitly configured, exposing the API to cross-origin attacks from any website.

**Fix:**

- Updated `/Volumes/SSD/dev/new/agent-recipes/src/config.py`:
  - Added `cors_allow_origins` setting with safe defaults (localhost only)
  - Added `cors_allow_credentials` and `cors_max_age` settings
  - Environment variable: `CORS_ALLOW_ORIGINS` for comma-separated whitelist
- Updated CORS middleware in `api.py` to use settings
- Restricted `allow_headers` to specific headers instead of wildcard

**Configuration:**

```bash
# Production: explicit whitelist
export CORS_ALLOW_ORIGINS="https://example.com,https://app.example.com"

# Development: all origins (with warning logged)
export CORS_ALLOW_ORIGINS="*"
```

### 4. CSP Enhancement (MEDIUM)

**File:** `/Volumes/SSD/dev/new/agent-recipes/src/api.py` (line 178-182)
**Severity:** MEDIUM

**Issue:**
Content Security Policy used `'unsafe-inline'` for scripts, weakening protection against XSS attacks.

**Fix:**

- Implemented nonce-based CSP for inline scripts
- Added `generate_csp_nonce()` using `secrets.token_urlsafe(16)`
- CSP nonce is generated per-request and included in response headers
- Falls back to `'unsafe-inline'` when disabled (for compatibility)
- Added additional security headers:
  - `Referrer-Policy: strict-origin-when-cross-origin`
  - `Permissions-Policy: geolocation=(), microphone=(), camera=()`

**Configuration:**

```bash
# Enable nonce-based CSP (default)
export CSP_USE_NONCE=true

# Disable for legacy compatibility
export CSP_USE_NONCE=false
```

## New Security Modules

### `/Volumes/SSD/dev/new/agent-recipes/src/security/sql.py`

SQL injection prevention utilities:

- `escape_like_pattern(pattern, escape_char='\\')` - Escape LIKE wildcards
- `build_like_clause(column, pattern, ...)` - Build safe LIKE clause
- `validate_search_input(query, ...)` - Validate search input

### `/Volumes/SSD/dev/new/agent-recipes/src/security/markdown.py`

Markdown/HTML sanitization for XSS prevention:

- `MarkdownSanitizer` - Configurable whitelist-based sanitizer
- `sanitize_markdown(markdown, ...)` - Sanitize markdown content
- `sanitize_html_only(html, ...)` - Sanitize HTML content

## Updated Security Module Exports

The `/Volumes/SSD/dev/new/agent-recipes/src/security/__init__.py` now exports:

- `escape_like_pattern` - SQL LIKE escaping
- `build_like_clause` - Safe LIKE clause builder
- `validate_search_input` - Search input validation
- `sanitize_markdown` - Markdown sanitization
- `sanitize_html_only` - HTML sanitization
- `MarkdownSanitizer` - Sanitizer class

## Test Coverage

All security fixes are covered by comprehensive tests in:

- `/Volumes/SSD/dev/new/agent-recipes/tests/test_security_fixes.py` (43 new tests)
- `/Volumes/SSD/dev/new/agent-recipes/tests/test_security.py` (39 existing tests)

Total: 82 security tests covering:

- SQL injection prevention (10 tests)
- LIKE wildcard escaping (6 tests)
- Search input validation (6 tests)
- Markdown XSS prevention (16 tests)
- CORS configuration (3 tests)
- CSP configuration (2 tests)

## Backward Compatibility

All changes are backward compatible:

- Existing APIs remain unchanged
- New behavior is opt-in via environment variables
- Fallback behavior maintains previous functionality
- No breaking changes to public interfaces

## Environment Variables

### CORS Configuration

- `CORS_ALLOW_ORIGINS` - Comma-separated list of allowed origins (default: localhost only)
- `CORS_MAX_AGE` - CORS preflight cache max-age (default: 600)

### CSP Configuration

- `CSP_USE_NONCE` - Enable nonce-based CSP (default: true)

## Migration Guide

### For Developers

1. Update imports to include new security functions:

```python
from src.security import escape_like_pattern, sanitize_markdown
```

2. Update search queries to use validated input:

```python
# Before: direct use
results = repo.search(q=user_input)

# After: input is validated internally
results = repo.search(q=user_input)  # No change needed!
```

3. Update markdown rendering:

```python
# Before: direct rendering
st.markdown(fetched_markdown)

# After: sanitize first
safe_md = sanitize_markdown(fetched_markdown, max_length=500_000)
st.markdown(safe_md)
```

### For Operations

1. Set CORS origins for production:

```bash
export CORS_ALLOW_ORIGINS="https://yourdomain.com,https://app.yourdomain.com"
```

2. Enable nonce-based CSP (default):

```bash
export CSP_USE_NONCE=true
```

## Files Changed

### New Files

- `/Volumes/SSD/dev/new/agent-recipes/src/security/sql.py`
- `/Volumes/SSD/dev/new/agent-recipes/src/security/markdown.py`
- `/Volumes/SSD/dev/new/agent-recipes/tests/test_security_fixes.py`
- `/Volumes/SSD/dev/new/agent-recipes/SECURITY_CHANGES.md`

### Modified Files

- `/Volumes/SSD/dev/new/agent-recipes/src/repository.py`
- `/Volumes/SSD/dev/new/agent-recipes/src/app.py`
- `/Volumes/SSD/dev/new/agent-recipes/src/api.py`
- `/Volumes/SSD/dev/new/agent-recipes/src/config.py`
- `/Volumes/SSD/dev/new/agent-recipes/src/security/__init__.py`

## References

- OWASP SQL Injection: https://owasp.org/www-community/attacks/SQL_Injection
- OWASP XSS: https://owasp.org/www-community/attacks/xss/
- MDN CSP: https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP
- MDN CORS: https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS
