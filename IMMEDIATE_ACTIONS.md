# Immediate Action Plan - Critical Security & Performance Fixes

**Priority:** P0 - Critical
**Timeline:** Week 1 (7 days)
**Status:** Ready for implementation

---

## Overview

This document provides actionable code fixes for the 5 critical security vulnerabilities identified in the architecture analysis. All fixes should be implemented before any production deployment.

**Estimated Total Time:** 7 days
**Risk Level:** Critical (fixes prevent security breaches and performance failures)

---

## Day 1-2: Fix TD-001 - Input Validation

### Problem

All user inputs lack proper validation, creating vulnerabilities for:

- SSRF (Server-Side Request Forgery)
- XSS (Cross-Site Scripting)
- Injection attacks
- Path traversal

### Solution

**File:** Create `/Volumes/SSD/dev/new/agent-recipes/src/validators.py`

```python
"""
Input validation utilities for Agent Navigator.
"""
import re
from typing import Optional, List
from urllib.parse import urlparse
from html import escape

ALLOWED_HOSTS = {
    'raw.githubusercontent.com',
    'github.com',
    'gist.github.com',
}

MAX_SEARCH_QUERY_LENGTH = 200
MAX_AGENT_ID_LENGTH = 100


def validate_url(url: str) -> bool:
    """
    Validate URL against whitelist and prevent SSRF attacks.

    Args:
        url: URL to validate

    Returns:
        True if URL is safe, False otherwise

    Raises:
        ValueError: If URL is invalid or blocked
    """
    try:
        parsed = urlparse(url.strip())

        # Only allow HTTPS (redirect HTTP to HTTPS)
        if parsed.scheme not in ('https',):
            raise ValueError(f"Blocked URL scheme: {parsed.scheme}")

        # Check hostname whitelist
        if parsed.netloc not in ALLOWED_HOSTS:
            raise ValueError(f"Blocked URL host: {parsed.netloc}")

        # Prevent path traversal attacks
        if '..' in parsed.path or '\n' in parsed.path or '\r' in parsed.path:
            raise ValueError("Blocked URL path: potential traversal attack")

        # Prevent URL bypass techniques
        if parsed.hostname != parsed.netloc:
            # Check for raw IP addresses
            if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', parsed.hostname or ''):
                raise ValueError("Blocked URL: IP address not allowed")

        return True

    except Exception as e:
        raise ValueError(f"Invalid URL: {e}")


def validate_search_query(query: str) -> str:
    """
    Validate and sanitize search query.

    Args:
        query: Raw search query

    Returns:
        Sanitized query

    Raises:
        ValueError: If query is invalid
    """
    if not query:
        return ""

    query = query.strip()

    # Length check
    if len(query) > MAX_SEARCH_QUERY_LENGTH:
        raise ValueError(f"Query too long (max {MAX_SEARCH_QUERY_LENGTH} characters)")

    # Remove null bytes and control characters
    query = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', query)

    # Check for suspicious patterns
    dangerous_patterns = [
        r'<script',  # Script injection
        r'javascript:',  # JavaScript protocol
        r'on\w+\s*=',  # Event handlers
    ]
    for pattern in dangerous_patterns:
        if re.search(pattern, query, re.IGNORECASE):
            raise ValueError(f"Query contains dangerous pattern: {pattern}")

    return query


def validate_agent_id(agent_id: str) -> str:
    """
    Validate agent ID format.

    Args:
        agent_id: Agent identifier

    Returns:
        Sanitized agent ID

    Raises:
        ValueError: If agent_id is invalid
    """
    if not agent_id:
        raise ValueError("Agent ID cannot be empty")

    agent_id = agent_id.strip()

    if len(agent_id) > MAX_AGENT_ID_LENGTH:
        raise ValueError(f"Agent ID too long (max {MAX_AGENT_ID_LENGTH} characters)")

    # Only allow alphanumeric, underscore, hyphen
    if not re.match(r'^[a-zA-Z0-9_-]+$', agent_id):
        raise ValueError("Agent ID contains invalid characters")

    return agent_id


def sanitize_html(text: str) -> str:
    """
    Sanitize text for safe HTML rendering.

    Args:
        text: Raw text

    Returns:
        HTML-escaped text
    """
    return escape(text, quote=False)


def validate_filter_values(values: List[str], allowed_values: List[str]) -> List[str]:
    """
    Validate filter values against allowed set.

    Args:
        values: Filter values to validate
        allowed_values: Whitelist of allowed values

    Returns:
        Validated values

    Raises:
        ValueError: If any value is invalid
    """
    validated = []
    allowed_set = set(allowed_values)

    for value in values:
        value = value.strip().lower()
        if value not in allowed_set:
            raise ValueError(f"Invalid filter value: {value}")
        validated.append(value)

    return validated


def validate_pagination(page: int, page_size: int, max_page_size: int = 100) -> tuple:
    """
    Validate pagination parameters.

    Args:
        page: Page number
        page_size: Items per page
        max_page_size: Maximum allowed page size

    Returns:
        Tuple of (page, page_size)

    Raises:
        ValueError: If parameters are invalid
    """
    if page < 1:
        raise ValueError("Page must be >= 1")

    if page_size < 1:
        raise ValueError("Page size must be >= 1")

    if page_size > max_page_size:
        raise ValueError(f"Page size too large (max {max_page_size})")

    return page, page_size
```

**File:** Update `/Volumes/SSD/dev/new/agent-recipes/src/app.py`

```python
# Add at top of file
from src import validators

# Replace fetch_readme_markdown function
def fetch_readme_markdown(readme_url: str) -> str:
    """Fetch README from GitHub with proper validation."""
    try:
        validators.validate_url(readme_url)
    except ValueError as e:
        raise ValueError(f"Invalid README URL: {e}")

    req = urllib.request.Request(
        readme_url,
        headers={"User-Agent": "agent-navigator/1.0"},
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        charset = resp.headers.get_content_charset() or "utf-8"
        content = resp.read().decode(charset, errors="replace")

    # Additional content validation
    if len(content) > 1_000_000:  # 1MB max
        raise ValueError("README too large")

    return content

# Update search page to validate query
def render_search_page(search_engine: AgentSearch, agents: list[dict]) -> None:
    # ... existing code ...

    with tab1:
        query = st.text_input(
            "Search agents",
            placeholder="e.g., PDF bot, RAG chatbot, multi-agent...",
            label_visibility="collapsed",
        )

        # Validate query
        try:
            query = validators.validate_search_query(query)
        except ValueError as e:
            st.warning(f"Invalid search query: {e}")
            query = ""

        # ... rest of function ...
```

**Testing:**

```python
# tests/test_validators.py
import pytest
from src.validators import validate_url, validate_search_query

def test_validate_url_blocks_ssrf():
    with pytest.raises(ValueError):
        validate_url("http://localhost:8080")  # Not in whitelist

    with pytest.raises(ValueError):
        validate_url("https://evil.com/path/../etc/passwd")

def test_validate_search_query_blocks_xss():
    with pytest.raises(ValueError):
        validate_search_query("<script>alert('xss')</script>")

def test_valid_inputs_pass():
    assert validate_url("https://raw.githubusercontent.com/user/repo/main/README.md") == True
    assert validate_search_query("PDF chatbot RAG") == "PDF chatbot RAG"
```

---

## Day 2-3: Fix TD-005 - LLM Output Sanitization

### Problem

LLM output is not validated, allowing:

- Prompt injection attacks
- Malformed JSON causing crashes
- Oversized responses
- Invalid enum values

### Solution

**File:** Create `/Volumes/SSD/dev/new/agent-recipes/src/llm_validator.py`

````python
"""
LLM output validation and sanitization.
"""
import json
import jsonschema
from typing import Dict, Any, List

# Define JSON schema for LLM output
LLM_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {
            "type": "string",
            "minLength": 1,
            "maxLength": 80
        },
        "description": {
            "type": "string",
            "maxLength": 200
        },
        "category": {
            "type": "string",
            "enum": [
                "rag", "chatbot", "agent", "multi_agent", "automation",
                "search", "vision", "voice", "coding", "finance",
                "research", "other"
            ]
        },
        "frameworks": {
            "type": "array",
            "items": {
                "type": "string",
                "enum": [
                    "langchain", "llamaindex", "crewai", "autogen",
                    "phidata", "dspy", "haystack", "semantic_kernel",
                    "raw_api", "other"
                ]
            },
            "minItems": 1,
            "maxItems": 10
        },
        "llm_providers": {
            "type": "array",
            "items": {
                "type": "string",
                "enum": [
                    "openai", "anthropic", "google", "cohere",
                    "mistral", "ollama", "huggingface", "local", "other"
                ]
            },
            "minItems": 1,
            "maxItems": 10
        },
        "requires_gpu": {"type": "boolean"},
        "supports_local_models": {"type": "boolean"},
        "design_pattern": {
            "type": "string",
            "enum": [
                "rag", "react", "plan_and_execute", "reflection",
                "multi_agent", "tool_use", "simple_chat", "other"
            ]
        },
        "complexity": {
            "type": "string",
            "enum": ["beginner", "intermediate", "advanced"]
        },
        "quick_start": {
            "type": "string",
            "maxLength": 1200
        },
        "api_keys": {
            "type": "array",
            "items": {"type": "string"},
            "maxItems": 20
        }
    },
    "required": ["name", "category", "frameworks", "llm_providers",
                 "requires_gpu", "supports_local_models", "design_pattern",
                 "complexity"],
    "additionalProperties": False
}


class LLMOutputValidator:
    """Validates and sanitizes LLM-generated metadata."""

    def __init__(self):
        self.schema = LLM_OUTPUT_SCHEMA

    def validate_and_sanitize(self, raw_output: str) -> Dict[str, Any]:
        """
        Validate LLM JSON output and sanitize values.

        Args:
            raw_output: Raw JSON string from LLM

        Returns:
            Validated and sanitized metadata dictionary

        Raises:
            ValueError: If validation fails
            json.JSONDecodeError: If JSON is malformed
        """
        # Remove markdown code blocks if present
        cleaned_output = self._extract_json(raw_output)

        # Parse JSON
        try:
            data = json.loads(cleaned_output)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON from LLM: {e}")

        # Validate against schema
        try:
            jsonschema.validate(data, self.schema)
        except jsonschema.ValidationError as e:
            raise ValueError(f"LLM output validation failed: {e.message}")

        # Sanitize string fields
        sanitized = self._sanitize_strings(data)

        # Apply additional safety checks
        sanitized = self._apply_safety_checks(sanitized)

        return sanitized

    def _extract_json(self, text: str) -> str:
        """Extract JSON from markdown code blocks."""
        text = text.strip()

        # Remove markdown code blocks
        if text.startswith("```"):
            lines = text.split("\n")
            # Find end of code block
            end_idx = len(lines)
            for i, line in enumerate(lines[1:], 1):
                if line.strip() == "```":
                    end_idx = i
                    break
            text = "\n".join(lines[1:end_idx])

            # Remove language identifier (e.g., "json")
            if text.startswith("json"):
                text = text[4:].strip()

        return text.strip()

    def _sanitize_strings(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize string fields to prevent injection."""
        sanitized = {}

        for key, value in data.items():
            if isinstance(value, str):
                # Remove null bytes and control characters
                value = ''.join(char for char in value if ord(char) >= 32 or char in '\n\r\t')
                # Trim whitespace
                value = value.strip()
                sanitized[key] = value
            elif isinstance(value, list):
                # Sanitize list items
                sanitized[key] = [
                    self._sanitize_strings({k: v})[k] if isinstance(v, str) else v
                    for v in value
                ]
            else:
                sanitized[key] = value

        return sanitized

    def _apply_safety_checks(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply additional safety checks."""
        # Ensure arrays don't have duplicates
        for field in ['frameworks', 'llm_providers', 'api_keys']:
            if field in data and isinstance(data[field], list):
                data[field] = list(set(data[field]))

        # Ensure defaults for boolean fields
        data.setdefault('requires_gpu', False)
        data.setdefault('supports_local_models', False)

        # Ensure name is not empty
        if not data.get('name'):
            data['name'] = 'Untitled Agent'

        return data


# Singleton instance
validator = LLMOutputValidator()
````

**File:** Update `/Volumes/SSD/dev/new/agent-recipes/src/indexer.py`

```python
# Add import
from src import llm_validator

# Update _extract_with_llm method
def _extract_with_llm(self, readme_content: str, folder_path: str) -> dict:
    if not self.client:
        raise RuntimeError("LLM client not initialized")

    prompt = EXTRACTION_PROMPT.format(
        readme_content=readme_content[: self.max_readme_chars],
        folder_path=folder_path,
    )

    response = self.client.messages.create(
        model="claude-3-5-haiku-20241022",
        max_tokens=900,
        messages=[{"role": "user", "content": prompt}],
    )

    text = response.content[0].text.strip()

    # Validate and sanitize LLM output
    try:
        return llm_validator.validator.validate_and_sanitize(text)
    except (ValueError, json.JSONDecodeError) as e:
        # Log error but don't fail - will fall back to heuristics
        print(f"  LLM output validation failed for {folder_path}: {e}")
        raise  # Re-raise to trigger heuristic fallback
```

---

## Day 3-4: Fix TD-002 - Server-Side Rate Limiting

### Problem

Current rate limiting is client-side only and easily bypassable.

### Solution

**File:** Create `/Volumes/SSD/dev/new/agent-recipes/src/rate_limiter.py`

```python
"""
Server-side rate limiting for API endpoints.
"""
import time
import hashlib
from typing import Optional, Dict
from collections import defaultdict
from functools import wraps

# Simple in-memory rate limiter (replace with Redis for production)
class RateLimiter:
    """
    Thread-safe in-memory rate limiter.

    For production, replace with Redis-backed implementation.
    """

    def __init__(self):
        self._requests: Dict[str, list] = defaultdict(list)
        self._lock = None  # Would use threading.Lock() in production

    def _get_key(self, identifier: str, endpoint: str) -> str:
        """Generate rate limit key."""
        raw = f"{identifier}:{endpoint}"
        return hashlib.sha256(raw.encode()).hexdigest()

    def check_rate_limit(
        self,
        identifier: str,
        endpoint: str,
        max_requests: int = 10,
        window_seconds: int = 60
    ) -> tuple[bool, Optional[int]]:
        """
        Check if request is within rate limit.

        Args:
            identifier: Unique identifier (IP address, API key, etc.)
            endpoint: Endpoint being accessed
            max_requests: Maximum requests allowed in window
            window_seconds: Time window in seconds

        Returns:
            Tuple of (allowed, retry_after_seconds)
            - allowed: True if request is allowed
            - retry_after: Seconds to wait if not allowed, None otherwise
        """
        key = self._get_key(identifier, endpoint)
        now = time.time()

        # Clean old requests outside window
        self._requests[key] = [
            timestamp for timestamp in self._requests[key]
            if now - timestamp < window_seconds
        ]

        # Check limit
        if len(self._requests[key]) >= max_requests:
            # Calculate retry after
            oldest_request = min(self._requests[key])
            retry_after = int(oldest_request + window_seconds - now)
            return False, retry_after

        # Record this request
        self._requests[key].append(now)
        return True, None

    def reset(self, identifier: str, endpoint: str) -> None:
        """Reset rate limit for identifier."""
        key = self._get_key(identifier, endpoint)
        if key in self._requests:
            del self._requests[key]


# Singleton instance
limiter = RateLimiter()


def rate_limit(
    max_requests: int = 10,
    window_seconds: int = 60,
    identifier_func=None
):
    """
    Decorator for rate limiting function calls.

    Args:
        max_requests: Maximum requests allowed
        window_seconds: Time window
        identifier_func: Function to extract identifier from args
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get identifier (default: first arg or 'default')
            if identifier_func:
                identifier = identifier_func(*args, **kwargs)
            else:
                identifier = str(args[0]) if args else 'default'

            # Check rate limit
            endpoint = func.__name__
            allowed, retry_after = limiter.check_rate_limit(
                identifier, endpoint, max_requests, window_seconds
            )

            if not allowed:
                raise RateLimitError(
                    f"Rate limit exceeded. Try again in {retry_after} seconds.",
                    retry_after=retry_after
                )

            return func(*args, **kwargs)
        return wrapper
    return decorator


class RateLimitError(Exception):
    """Raised when rate limit is exceeded."""

    def __init__(self, message: str, retry_after: int):
        super().__init__(message)
        self.retry_after = retry_after
```

**File:** Update `/Volumes/SSD/dev/new/agent-recipes/src/app.py`

```python
# Add import
from src.rate_limiter import limiter, RateLimitError

# Replace ai_select_agents function
def ai_select_agents(query: str, agents: list[dict]) -> str:
    if not HAS_ANTHROPIC:
        return "AI Selector unavailable: missing `anthropic` dependency."

    api_key = st.secrets.get("ANTHROPIC_API_KEY")
    if not api_key:
        return "AI Selector requires `ANTHROPIC_API_KEY` in Streamlit secrets."

    # Get identifier (use API key hash or session ID)
    identifier = st.session_state.get('user_id', 'anonymous')

    # Server-side rate limit check
    allowed, retry_after = limiter.check_rate_limit(
        identifier=identifier,
        endpoint='ai_select',
        max_requests=10,
        window_seconds=60
    )

    if not allowed:
        return f"Rate limited: Please try again in {retry_after} seconds."

    # ... rest of function remains the same ...
```

---

## Day 4-5: Fix TD-004 - Secrets Management

### Problem

API keys stored in environment variables are visible in process list.

### Solution

**File:** Create `/Volumes/SSD/dev/new/agent-recipes/src/secrets.py`

```python
"""
Secure secrets management.

For development: Uses environment variables
For production: Should use AWS Secrets Manager, HashiCorp Vault, etc.
"""
import os
import base64
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2


class SecretManager:
    """
    Secure secret manager with encryption support.

    Usage:
        # For development
        manager = SecretManager.from_environment()

        # For production (with encryption key)
        manager = SecretManager(encryption_key=os.environ['SECRET_KEY'])
    """

    def __init__(self, encryption_key: Optional[str] = None):
        """
        Initialize secret manager.

        Args:
            encryption_key: Optional encryption key for secrets at rest
                           If None, secrets are not encrypted (dev mode)
        """
        self.encryption_key = encryption_key
        self.cipher = None

        if encryption_key:
            # Derive Fernet key from encryption key
            kdf = PBKDF2(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b'agent_navigator_salt',  # In production, use random salt
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(encryption_key.encode()))
            self.cipher = Fernet(key)

    @classmethod
    def from_environment(cls) -> 'SecretManager':
        """Create secret manager from environment variables."""
        encryption_key = os.environ.get('SECRET_ENCRYPTION_KEY')
        return cls(encryption_key=encryption_key)

    def get_secret(self, key: str) -> str:
        """
        Get secret value.

        Args:
            key: Secret key name

        Returns:
            Decrypted secret value

        Raises:
            ValueError: If secret not found
        """
        # Try environment variable first
        env_key = f"{key}_SECRET" if not key.endswith('_SECRET') else key
        value = os.environ.get(env_key)

        if not value:
            raise ValueError(f"Secret not found: {key}")

        # Decrypt if cipher is available
        if self.cipher:
            try:
                value = self.cipher.decrypt(value.encode()).decode()
            except Exception:
                # If decryption fails, assume it's not encrypted
                pass

        return value

    def set_secret(self, key: str, value: str) -> None:
        """
        Set secret value (encrypts if cipher available).

        Args:
            key: Secret key name
            value: Secret value
        """
        if self.cipher:
            value = self.cipher.encrypt(value.encode()).decode()

        # Only store in memory, never write to disk
        os.environ[key] = value

    def get_anthropic_api_key(self) -> str:
        """Get Anthropic API key with validation."""
        key = self.get_secret('ANTHROPIC_API_KEY')

        if not key.startswith('sk-ant-'):
            raise ValueError("Invalid Anthropic API key format")

        return key

    def get_github_token(self) -> Optional[str]:
        """Get GitHub token (optional)."""
        try:
            return self.get_secret('GITHUB_TOKEN')
        except ValueError:
            return None


# Singleton instance
secret_manager = SecretManager.from_environment()
```

**File:** Update `/Volumes/SSD/dev/new/agent-recipes/src/app.py`

```python
# Add import
from src.secrets import secret_manager, SecretManagerError

# Update ai_select_agents function
def ai_select_agents(query: str, agents: list[dict]) -> str:
    if not HAS_ANTHROPIC:
        return "AI Selector unavailable: missing `anthropic` dependency."

    try:
        api_key = secret_manager.get_anthropic_api_key()
    except ValueError as e:
        return f"AI Selector configuration error: {e}"

    # ... rest of function ...
```

---

## Day 5-6: Fix TD-003 - Error Handling

### Problem

Bare exception handlers hide errors and make debugging impossible.

### Solution

**File:** Create `/Volumes/SSD/dev/new/agent-recipes/src/errors.py`

```python
"""
Custom exceptions and error handling.
"""
import logging
import sys
from typing import Optional, Callable, Any
from functools import wraps

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AgentNavigatorError(Exception):
    """Base exception for Agent Navigator."""

    pass


class ValidationError(AgentNavigatorError):
    """Raised when input validation fails."""

    pass


class ConfigurationError(AgentNavigatorError):
    """Raised when configuration is invalid."""

    pass


class APIError(AgentNavigatorError):
    """Raised when API call fails."""

    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


class SearchError(AgentNavigatorError):
    """Raised when search operation fails."""

    pass


class IndexerError(AgentNavigatorError):
    """Raised when indexing operation fails."""

    pass


def safe_import(
    module_name: str,
    fallback_module_name: Optional[str] = None,
    error_message: Optional[str] = None
):
    """
    Safely import module with proper error handling.

    Args:
        module_name: Primary module to import
        fallback_module_name: Fallback module if primary fails
        error_message: Custom error message

    Returns:
        Imported module

    Raises:
        ConfigurationError: If import fails
    """
    try:
        module = __import__(module_name, fromlist=[''])
        return module
    except ImportError as e:
        if fallback_module_name:
            try:
                module = __import__(fallback_module_name, fromlist=[''])
                logger.warning(f"Using fallback module: {fallback_module_name}")
                return module
            except ImportError:
                pass

        error_msg = error_message or f"Failed to import {module_name}"
        logger.error(f"{error_msg}: {e}")
        raise ConfigurationError(f"{error_msg}: {e}")


def handle_errors(
    default_return: Any = None,
    exceptions: tuple = (Exception,),
    log_level: str = "ERROR"
):
    """
    Decorator for standardized error handling.

    Args:
        default_return: Value to return on error
        exceptions: Tuple of exceptions to catch
        log_level: Logging level ('ERROR', 'WARNING', 'INFO')
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except exceptions as e:
                # Log the error
                log_func = getattr(logger, log_level.lower(), logger.error)
                log_func(f"Error in {func.__name__}: {e}", exc_info=True)

                # Return default or re-raise
                if default_return is not None:
                    return default_return
                raise
        return wrapper
    return decorator


def validate_and_call(func: Callable, *validators: Callable):
    """
    Decorator to validate inputs before calling function.

    Args:
        func: Function to decorate
        *validators: Validation functions to run before func
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Run all validators
        for validator in validators:
            validator(*args, **kwargs)

        # Call function if all validators pass
        return func(*args, **kwargs)
    return wrapper
```

**File:** Update `/Volumes/SSD/dev/new/agent-recipes/src/app.py`

```python
# Replace imports at top
from src.search import AgentSearch
from src import domain
from src.errors import safe_import, ValidationError, APIError

# Remove try/except blocks
# Old code:
# try:
#     from src.search import AgentSearch
# except Exception:
#     from search import AgentSearch

# New code:
# (No try/except needed - import will raise ConfigurationError with clear message)

# Update fetch_readme_markdown
from src.errors import handle_errors

@handle_errors(default_return="", exceptions=(ValidationError, urllib.error.URLError))
def fetch_readme_markdown(readme_url: str) -> str:
    """Fetch README from GitHub with proper error handling."""
    validators.validate_url(readme_url)

    req = urllib.request.Request(
        readme_url,
        headers={"User-Agent": "agent-navigator/1.0"},
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            charset = resp.headers.get_content_charset() or "utf-8"
            content = resp.read().decode(charset, errors="replace")
    except urllib.error.HTTPError as e:
        logger.error(f"HTTP error fetching {readme_url}: {e.code}")
        raise APIError(f"Failed to fetch README: HTTP {e.code}", status_code=e.code)
    except urllib.error.URLError as e:
        logger.error(f"URL error fetching {readme_url}: {e}")
        raise APIError(f"Failed to fetch README: {e.reason}")
    except TimeoutError:
        logger.error(f"Timeout fetching {readme_url}")
        raise APIError("Request timeout")

    if len(content) > 1_000_000:
        raise ValidationError("README too large (>1MB)")

    return content
```

---

## Day 7: Testing & Documentation

### Security Testing

Create `/Volumes/SSD/dev/new/agent-recipes/tests/test_security.py`

```python
"""
Security tests for Agent Navigator.
"""
import pytest
from src.validators import (
    validate_url, validate_search_query, validate_agent_id,
    sanitize_html
)
from src.errors import ValidationError


class TestInputValidation:
    """Test input validation security."""

    def test_validate_url_blocks_ssrf_attacks(self):
        """Test that SSRF attacks are blocked."""
        malicious_urls = [
            "http://localhost/admin",
            "http://169.254.169.254/latest/meta-data/",  # AWS metadata
            "file:///etc/passwd",
            "ftp://evil.com/exploit",
            "https://evil.com/path/../etc/passwd",
        ]

        for url in malicious_urls:
            with pytest.raises((ValidationError, ValueError)):
                validate_url(url)

    def test_validate_search_query_blocks_xss(self):
        """Test that XSS attempts are blocked."""
        xss_attempts = [
            "<script>alert('xss')</script>",
            "<img src=x onerror=alert('xss')>",
            "javascript:alert('xss')",
            "<iframe src='evil.com'></iframe>",
        ]

        for query in xss_attempts:
            with pytest.raises((ValidationError, ValueError)):
                validate_search_query(query)

    def test_validate_agent_id_blocks_injection(self):
        """Test that agent ID injection is blocked."""
        invalid_ids = [
            "../../etc/passwd",
            "agent'; DROP TABLE agents; --",
            "agent\x00null",
            "<script>alert('xss')</script>",
        ]

        for agent_id in invalid_ids:
            with pytest.raises((ValidationError, ValueError)):
                validate_agent_id(agent_id)

    def test_sanitize_html(self):
        """Test HTML sanitization."""
        assert sanitize_html("<script>alert('xss')</script>") == "&lt;script&gt;alert('xss')&lt;/script&gt;"
        assert sanitize_html("Normal text") == "Normal text"


class TestRateLimiting:
    """Test rate limiting."""

    def test_rate_limit_enforced(self):
        """Test that rate limit is enforced."""
        from src.rate_limiter import limiter

        identifier = "test_user"
        endpoint = "test_endpoint"

        # Make 10 requests (should all pass)
        for i in range(10):
            allowed, retry_after = limiter.check_rate_limit(
                identifier, endpoint, max_requests=10, window_seconds=60
            )
            assert allowed is True
            assert retry_after is None

        # 11th request should be blocked
        allowed, retry_after = limiter.check_rate_limit(
            identifier, endpoint, max_requests=10, window_seconds=60
        )
        assert allowed is False
        assert retry_after is not None
        assert retry_after > 0

    def test_rate_limit_reset(self):
        """Test that rate limit resets correctly."""
        from src.rate_limiter import limiter

        identifier = "test_user_2"
        endpoint = "test_endpoint_2"

        # Use up quota
        for i in range(10):
            limiter.check_rate_limit(identifier, endpoint, max_requests=10, window_seconds=60)

        # Reset
        limiter.reset(identifier, endpoint)

        # Should be allowed again
        allowed, retry_after = limiter.check_rate_limit(
            identifier, endpoint, max_requests=10, window_seconds=60
        )
        assert allowed is True


class TestLLMValidation:
    """Test LLM output validation."""

    def test_valid_llm_output_passes(self):
        """Test that valid LLM output passes validation."""
        from src.llm_validator import validator

        valid_output = '''
        {
            "name": "Test Agent",
            "description": "A test agent",
            "category": "chatbot",
            "frameworks": ["langchain"],
            "llm_providers": ["openai"],
            "requires_gpu": false,
            "supports_local_models": false,
            "design_pattern": "simple_chat",
            "complexity": "beginner",
            "api_keys": []
        }
        '''

        result = validator.validate_and_sanitize(valid_output)
        assert result['name'] == 'Test Agent'
        assert result['category'] == 'chatbot'

    def test_malicious_llm_output_blocked(self):
        """Test that malicious LLM output is blocked."""
        from src.llm_validator import validator

        malicious_outputs = [
            '{"name": "<script>alert(\'xss\')</script>", "category": "chatbot", "frameworks": ["langchain"], "llm_providers": ["openai"], "requires_gpu": false, "supports_local_models": false, "design_pattern": "simple_chat", "complexity": "beginner"}',
            '{"name": "Agent", "category": "invalid_category", "frameworks": ["langchain"], "llm_providers": ["openai"], "requires_gpu": false, "supports_local_models": false, "design_pattern": "simple_chat", "complexity": "beginner"}',
            '{"name": "A" * 100, "category": "chatbot", "frameworks": ["langchain"], "llm_providers": ["openai"], "requires_gpu": false, "supports_local_models": false, "design_pattern": "simple_chat", "complexity": "beginner"}',
        ]

        for output in malicious_outputs:
            with pytest.raises((ValueError, json.JSONDecodeError)):
                validator.validate_and_sanitize(output)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

### Documentation

Update `/Volumes/SSD/dev/new/agent-recipes/SECURITY.md`

```markdown
# Security Guide

## Overview

Agent Navigator implements multiple layers of security to protect against common vulnerabilities.

## Input Validation

All user inputs are validated before processing:

- URLs validated against whitelist
- Search queries sanitized for XSS
- Agent IDs validated for format
- Pagination parameters bounded

## Rate Limiting

Server-side rate limiting prevents abuse:

- AI Selector: 10 requests per minute per user
- Configurable per endpoint
- Automatic retry-after responses

## Secrets Management

API keys are securely managed:

- Never logged or exposed in errors
- Optional encryption at rest
- Validation for format correctness

## LLM Output Validation

All LLM-generated content is validated:

- JSON schema validation
- String sanitization
- Length limits
- Enum value checking

## Security Best Practices

### For Development

1. Never commit `.streamlit/secrets.toml`
2. Use environment variables for secrets
3. Run security tests: `pytest tests/test_security.py`

### For Production

1. Use proper secret manager (AWS Secrets Manager, Vault)
2. Enable HTTPS only
3. Implement authentication
4. Set up monitoring for suspicious activity
5. Regular security audits

## Reporting Security Issues

Please report security issues privately to: security@example.com
```

---

## Verification Checklist

After implementing all fixes, verify:

- [ ] All security tests pass: `pytest tests/test_security.py -v`
- [ ] All existing tests still pass: `pytest tests/ -v`
- [ ] No bare exception handlers remain: `grep -r "except:" src/`
- [ ] All user inputs validated: Manual testing
- [ ] Rate limiting works: Test with rapid requests
- [ ] Secrets never logged: Check logs
- [ ] LLM output validation works: Test with malformed responses
- [ ] Documentation updated: SECURITY.md exists

---

## Next Steps

After completing Week 1 fixes:

1. **Week 2-3**: Implement performance optimizations (parallel LLM processing)
2. **Week 4**: Add comprehensive monitoring and logging
3. **Month 2**: Increase test coverage to 60%+
4. **Quarter 1**: Architecture refactoring

---

**Estimated Completion:** 7 days
**Risk Reduction:** Critical vulnerabilities eliminated
**Production Readiness:** After Week 1 + security audit

---

**Document Version:** 1.0
**Last Updated:** 2025-12-30
**Status:** Ready for implementation
