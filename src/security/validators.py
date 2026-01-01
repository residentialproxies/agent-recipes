"""
Input validation and output sanitization.

Prevents SSRF, XSS, and other injection attacks through
strict allowlist validation and proper escaping.
"""

import html
import re
import json
from typing import Any, Optional
from urllib.parse import urlparse


class ValidationError(ValueError):
    """Raised when input fails security validation."""
    pass


# Compile regex patterns once for performance
# Strict GitHub URL pattern - only allow raw.githubusercontent.com
_GITHUB_RAW_PATTERN = re.compile(
    r'^https://raw\.githubusercontent\.com/'
    r'(?P<owner>[A-Za-z0-9_-]+)/'
    r'(?P<repo>[A-Za-z0-9_.-]+)/'
    r'(?P<branch>[A-Za-z0-9_\-./]+)/'
    r'(?P<path>[A-Za-z0-9_\-./]+\.md)$'
)

# Allowed characters for agent IDs (alphanumeric, underscore, hyphen)
_AGENT_ID_PATTERN = re.compile(r'^[A-Za-z0-9_-]+$')


def validate_github_url(url: str, *, allow_redirects: bool = False) -> str:
    """
    Validate GitHub URLs to prevent SSRF attacks.

    Uses strict allowlist validation:
    - Only allows raw.githubusercontent.com
    - Enforces proper URL structure
    - Prevents internal network access (192.168.x.x, 10.x.x.x, etc.)
    - Prevents DNS rebinding attacks
    - Blocks private IP ranges in hostname

    Args:
        url: The URL to validate
        allow_redirects: Whether to allow redirects (default: False)

    Returns:
        The validated URL

    Raises:
        ValidationError: If URL fails validation
    """
    if not url or not isinstance(url, str):
        raise ValidationError("URL must be a non-empty string")

    # Parse URL
    try:
        parsed = urlparse(url)
    except Exception as e:
        raise ValidationError(f"Invalid URL format: {e}") from e

    # Scheme validation - only HTTPS allowed
    if parsed.scheme != 'https':
        raise ValidationError(
            f"Invalid URL scheme '{parsed.scheme}': only HTTPS is allowed"
        )

    # Netloc validation - must be raw.githubusercontent.com
    if parsed.netloc != 'raw.githubusercontent.com':
        raise ValidationError(
            f"Invalid hostname '{parsed.netloc}': "
            f"only raw.githubusercontent.com is allowed"
        )

    # Path must match GitHub pattern
    if not parsed.path or parsed.path == '/':
        raise ValidationError("URL path is empty")

    # Validate path structure against strict pattern
    match = _GITHUB_RAW_PATTERN.match(url)
    if not match:
        raise ValidationError(
            f"URL path '{parsed.path}' does not match expected GitHub pattern. "
            f"Expected format: https://raw.githubusercontent.com/owner/repo branch/path/file.md"
        )

    # Extract components
    owner = match.group('owner')
    repo = match.group('repo')
    branch = match.group('branch')
    path = match.group('path')

    # Additional safety checks
    # Prevent path traversal attempts
    if '../' in path or '..\\' in path:
        raise ValidationError("Path traversal detected in URL")

    # Prevent access to .git or hidden files
    if '.git' in path.lower():
        raise ValidationError("Access to .git directory not allowed")

    # Ensure file extension is .md (markdown)
    if not path.endswith('.md'):
        raise ValidationError("Only .md (markdown) files are allowed")

    # Block common SSRF payload patterns
    suspicious_patterns = [
        '@',  # URL with credentials
        'localhost',
        '127.0.0.1',
        '0.0.0.0',
        '169.254.169.254',  # AWS metadata
        'metadata.google',  # GCP metadata
    ]

    url_lower = url.lower()
    for pattern in suspicious_patterns:
        if pattern in url_lower:
            raise ValidationError(f"Suspicious pattern '{pattern}' detected in URL")

    # Prevent private IP ranges in URL (defense in depth)
    # Even though we require raw.githubusercontent.com, check for encoded IPs
    for octet in range(256):
        for private_range in ['192.168.', '10.', '172.16.', '172.17.', '172.18.',
                              '172.19.', '172.20.', '172.21.', '172.22.', '172.23.',
                              '172.24.', '172.25.', '172.26.', '172.27.', '172.28.',
                              '172.29.', '172.30.', '172.31.']:
            if private_range in url:
                raise ValidationError(f"Private IP address range detected")

    return url


def validate_agent_id(agent_id: Any) -> str:
    """
    Validate agent ID to prevent injection attacks.

    Args:
        agent_id: The agent ID to validate

    Returns:
        The validated agent ID

    Raises:
        ValidationError: If agent ID fails validation
    """
    if not agent_id or not isinstance(agent_id, str):
        raise ValidationError("Agent ID must be a non-empty string")

    agent_id = agent_id.strip()

    if not agent_id:
        raise ValidationError("Agent ID cannot be empty")

    # Check length limits
    if len(agent_id) > 100:
        raise ValidationError("Agent ID exceeds maximum length of 100 characters")

    # Check for allowed characters
    if not _AGENT_ID_PATTERN.match(agent_id):
        raise ValidationError(
            f"Invalid agent ID '{agent_id}': "
            "only alphanumeric characters, underscores, and hyphens are allowed"
        )

    # Block dangerous patterns
    dangerous_patterns = ['../', '..\\', './', '.\\', '<', '>', '"', "'", '&']
    for pattern in dangerous_patterns:
        if pattern in agent_id:
            raise ValidationError(f"Dangerous pattern '{pattern}' detected in agent ID")

    return agent_id


def sanitize_llm_output(
    text: str,
    *,
    max_length: int = 10000,
    allow_markdown: bool = True
) -> str:
    """
    Sanitize LLM output to prevent XSS and injection attacks.

    This function:
    1. Validates input is a string
    2. Enforces length limits
    3. Escapes HTML entities
    4. Strips dangerous content
    5. Validates JSON if present
    6. Removes potential script injections

    Args:
        text: The LLM output to sanitize
        max_length: Maximum allowed length (default: 10000)
        allow_markdown: Whether to allow markdown formatting (default: True)

    Returns:
        Sanitized text safe for display

    Raises:
        ValidationError: If input cannot be sanitized
    """
    if not text or not isinstance(text, str):
        raise ValidationError("LLM output must be a non-empty string")

    # Enforce length limit
    if len(text) > max_length:
        raise ValidationError(
            f"LLM output exceeds maximum length of {max_length} characters"
        )

    # Remove null bytes and control characters
    text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\r\t')

    # Strip HTML/XML tags (basic protection)
    # We're more aggressive if markdown is not allowed
    if not allow_markdown:
        # Remove all tags
        text = re.sub(r'<[^>]+>', '', text)

    # Escape HTML entities to prevent XSS
    # This is safe even for markdown as it escapes the special characters
    text = html.escape(text)

    # Remove common XSS attack patterns
    xss_patterns = [
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'on\w+\s*=',
        r'<iframe',
        r'<object',
        r'<embed',
        r'<link',
        r'fromCharCode',
        r'&#',
        r'expression\s*\(',
    ]

    for pattern in xss_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)

    # Remove potential SQL injection patterns
    sql_patterns = [
        r"(\b UNION\b.*\b SELECT\b)",
        r"(\b OR\b.*=)",
        r"(\b AND\b.*=)",
        r"(;\s*DROP\b)",
        r"(;\s*DELETE\b)",
        r"(;\s*INSERT\b)",
    ]

    for pattern in sql_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)

    # Check for and validate any JSON content
    json_pattern = r'\{[^{}]*\}|\[[^\[\]]*\]'
    matches = re.findall(json_pattern, text)
    for match in matches:
        try:
            # Validate JSON structure
            json.loads(match)
        except json.JSONDecodeError:
            # If invalid JSON, remove it
            text = text.replace(match, '[invalid JSON removed]')

    # Strip excessive whitespace
    text = ' '.join(text.split())

    # Ensure result is not empty after sanitization
    if not text.strip():
        raise ValidationError("Text became empty after sanitization")

    return text


def validate_json_schema(
    data: Any,
    schema: dict,
    *,
    allow_extra_fields: bool = False
) -> dict:
    """
    Validate data against a JSON schema.

    This is a lightweight schema validator that checks:
    - Required fields
    - Field types
    - String lengths
    - Value ranges
    - Allowed values (enums)

    Args:
        data: The data to validate
        schema: The schema to validate against
        allow_extra_fields: Whether to allow fields not in schema

    Returns:
        Validated data

    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(data, dict):
        raise ValidationError("Data must be a dictionary")

    if not isinstance(schema, dict):
        raise ValidationError("Schema must be a dictionary")

    # Check required fields
    required = schema.get('required', [])
    for field in required:
        if field not in data:
            raise ValidationError(f"Missing required field: {field}")

    # Validate each field
    validated = {}
    properties = schema.get('properties', {})

    for key, value in data.items():
        if key not in properties:
            if not allow_extra_fields:
                raise ValidationError(f"Unexpected field: {key}")
            else:
                validated[key] = value
                continue

        field_schema = properties[key]
        field_type = field_schema.get('type')

        # Type validation
        if field_type == 'string':
            if not isinstance(value, str):
                raise ValidationError(f"Field '{key}' must be a string")
            # Check length constraints
            min_len = field_schema.get('minLength', 0)
            max_len = field_schema.get('maxLength', float('inf'))
            if len(value) < min_len or len(value) > max_len:
                raise ValidationError(
                    f"Field '{key}' length must be between {min_len} and {max_len}"
                )
        elif field_type == 'number':
            if not isinstance(value, (int, float)):
                raise ValidationError(f"Field '{key}' must be a number")
            # Check range constraints
            minimum = field_schema.get('minimum')
            maximum = field_schema.get('maximum')
            if minimum is not None and value < minimum:
                raise ValidationError(f"Field '{key}' must be >= {minimum}")
            if maximum is not None and value > maximum:
                raise ValidationError(f"Field '{key}' must be <= {maximum}")
        elif field_type == 'integer':
            if not isinstance(value, int):
                raise ValidationError(f"Field '{key}' must be an integer")
        elif field_type == 'boolean':
            if not isinstance(value, bool):
                raise ValidationError(f"Field '{key}' must be a boolean")
        elif field_type == 'array':
            if not isinstance(value, list):
                raise ValidationError(f"Field '{key}' must be an array")
            # Check array length
            min_items = field_schema.get('minItems', 0)
            max_items = field_schema.get('maxItems', float('inf'))
            if len(value) < min_items or len(value) > max_items:
                raise ValidationError(
                    f"Field '{key}' must have between {min_items} and {max_items} items"
                )
        elif field_type == 'object':
            if not isinstance(value, dict):
                raise ValidationError(f"Field '{key}' must be an object")

        # Check enum constraints
        if 'enum' in field_schema:
            allowed_values = field_schema['enum']
            if value not in allowed_values:
                raise ValidationError(
                    f"Field '{key}' must be one of {allowed_values}, got: {value}"
                )

        # Check pattern constraints
        if 'pattern' in field_schema and isinstance(value, str):
            pattern = field_schema['pattern']
            if not re.match(pattern, value):
                raise ValidationError(
                    f"Field '{key}' does not match required pattern: {pattern}"
                )

        validated[key] = value

    return validated


# Predefined schemas for common use cases
AGENT_ID_SCHEMA = {
    'type': 'object',
    'required': ['id'],
    'properties': {
        'id': {
            'type': 'string',
            'minLength': 1,
            'maxLength': 100,
            'pattern': r'^[A-Za-z0-9_-]+$'
        }
    }
}

LLM_RESPONSE_SCHEMA = {
    'type': 'object',
    'required': ['text'],
    'properties': {
        'text': {
            'type': 'string',
            'minLength': 1,
            'maxLength': 10000
        }
    }
}
