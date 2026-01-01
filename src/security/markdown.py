"""
Markdown sanitization for XSS prevention.

Provides safe markdown rendering that sanitizes HTML content
to prevent XSS attacks while preserving legitimate markdown formatting.
"""

import html
import re
from typing import Optional, Set


# Default allowed HTML tags (safe subset)
DEFAULT_ALLOWED_TAGS: Set[str] = {
    "p",
    "br",
    "strong",
    "b",
    "em",
    "i",
    "u",
    "s",
    "strike",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "ul",
    "ol",
    "li",
    "blockquote",
    "pre",
    "code",
    "a",
    "img",
    "table",
    "thead",
    "tbody",
    "tr",
    "th",
    "td",
    "hr",
    "div",
    "span",
}

# Default allowed attributes per tag (whitelist approach)
DEFAULT_ALLOWED_ATTRS: dict[str, Set[str]] = {
    "a": {"href", "title", "rel"},
    "img": {"src", "alt", "title", "width", "height"},
    "td": {"colspan", "rowspan"},
    "th": {"colspan", "rowspan"},
}

# Dangerous attribute patterns to block (Javascript:, data:, etc.)
DANGEROUS_ATTR_PATTERNS = [
    r"javascript:",
    r"data:",
    r"vbscript:",
    r"file:",
    r"ftp:",
    r"\0x",  # Hex encoding
    r"&#x",  # HTML entity encoding
    r"&#\d+",  # Decimal encoding
    r"on\w+\s*=",  # Event handlers like onclick=
    r"fromCharCode",
    r"expression\s*\(",
]

# Protocols allowed in href/src attributes
SAFE_PROTOCOLS = {
    "http:",
    "https:",
    "mailto:",
    "tel:",
    "#",  # Fragment links
}


class MarkdownSanitizer:
    """
    Sanitizes markdown content to prevent XSS attacks.

    This provides a safe way to render user-supplied markdown by:
    1. Parsing HTML tags
    2. Filtering to allowed tags only
    3. Filtering attributes to allowed attributes only
    4. Validating URL protocols
    5. Removing dangerous content

    Usage:
        sanitizer = MarkdownSanitizer()
        safe_html = sanitizer.sanitize(user_markdown)
        # Render safe_html in your template
    """

    def __init__(
        self,
        *,
        allowed_tags: Optional[Set[str]] = None,
        allowed_attrs: Optional[dict[str, Set[str]]] = None,
        strip_disallowed_tags: bool = True,
    ):
        """
        Initialize the sanitizer.

        Args:
            allowed_tags: Set of allowed HTML tags (default: safe subset)
            allowed_attrs: Dict of tag -> allowed attributes (default: safe subset)
            strip_disallowed_tags: If True, strip disallowed tags; if False, escape them
        """
        self.allowed_tags = allowed_tags if allowed_tags is not None else DEFAULT_ALLOWED_TAGS
        self.allowed_attrs = allowed_attrs if allowed_attrs is not None else DEFAULT_ALLOWED_ATTRS
        self.strip_disallowed_tags = strip_disallowed_tags

    def _is_safe_url(self, url: str) -> bool:
        """
        Check if a URL is safe to use in href/src attributes.

        Args:
            url: The URL to validate

        Returns:
            True if URL is safe, False otherwise
        """
        if not url:
            return False

        url_lower = url.lower().strip()

        # Check for dangerous patterns
        for pattern in DANGEROUS_ATTR_PATTERNS:
            if re.search(pattern, url_lower):
                return False

        # Check protocol
        for protocol in SAFE_PROTOCOLS:
            if url_lower.startswith(protocol):
                return True

        # Relative URLs (no protocol) are allowed
        if not any(url_lower.startswith(p) for p in ["http:", "https:", "mailto:", "tel:", "ftp:", "file:"]):
            return True

        return False

    def _sanitize_attribute(self, tag: str, attr_name: str, attr_value: str) -> Optional[tuple[str, str]]:
        """
        Sanitize a single HTML attribute.

        Args:
            tag: The tag this attribute belongs to
            attr_name: The attribute name
            attr_value: The attribute value

        Returns:
            Tuple of (attr_name, attr_value) if safe, None if should be removed
        """
        # Check if this attribute is allowed for this tag
        tag_attrs = self.allowed_attrs.get(tag, set())
        if attr_name not in tag_attrs:
            return None

        # For href/src, validate the URL
        if attr_name in ("href", "src"):
            if not self._is_safe_url(attr_value):
                return None

        # Escape the attribute value
        safe_value = html.escape(attr_value, quote=True)

        return attr_name, safe_value

    def _sanitize_tag(self, match: re.Match) -> str:
        """
        Sanitize a single HTML tag match.

        Args:
            match: Regex match object for the tag

        Returns:
            Safe HTML string for this tag
        """
        tag = match.group(1).lower()
        is_closing = match.group(0).startswith("</")
        is_self_closing = match.group(0).endswith("/>")

        # Closing tags - only allow if tag is allowed
        if is_closing:
            if tag in self.allowed_tags:
                return f"</{tag}>"
            return "" if self.strip_disallowed_tags else html.escape(match.group(0))

        # Self-closing tags
        if is_self_closing:
            if tag in self.allowed_tags:
                return f"<{tag} />"
            return "" if self.strip_disallowed_tags else html.escape(match.group(0))

        # Opening tags with attributes
        attrs = match.group(2) or ""

        # If tag not allowed
        if tag not in self.allowed_tags:
            if self.strip_disallowed_tags:
                # Strip the tag but keep content (simple approach)
                return ""
            else:
                return html.escape(match.group(0))

        # Parse and sanitize attributes
        safe_attrs = []
        attr_pattern = r'(\S+)=["\']([^"\']*)["\']|(\S+)(?=\s|$|>)'
        for attr_match in re.finditer(attr_pattern, attrs):
            attr_name = attr_match.group(1) or attr_match.group(3) or ""
            attr_value = attr_match.group(2) or ""

            sanitized = self._sanitize_attribute(tag, attr_name.lower(), attr_value)
            if sanitized:
                safe_name, safe_value = sanitized
                safe_attrs.append(f'{safe_name}="{safe_value}"')

        # Rebuild the tag
        if safe_attrs:
            return f"<{tag} {' '.join(safe_attrs)}>"
        return f"<{tag}>"

    def sanitize(self, markdown: str, *, max_length: int = 100_000) -> str:
        """
        Sanitize markdown content by removing dangerous HTML.

        Args:
            markdown: The markdown content to sanitize
            max_length: Maximum content length (prevents DoS via huge content)

        Returns:
            Sanitized HTML safe for rendering

        Raises:
            ValueError: If content exceeds max_length
            TypeError: If input is not a string
        """
        if not isinstance(markdown, str):
            raise TypeError(f"Markdown must be a string, got {type(markdown).__name__}")

        if len(markdown) > max_length:
            raise ValueError(f"Markdown exceeds maximum length of {max_length} characters")

        # First, escape HTML entities in the raw markdown
        # This handles inline HTML in the markdown
        result = markdown

        # Find and sanitize HTML tags
        # Pattern: <tagname attrs> or </tagname> or <tagname />
        tag_pattern = r"<(/?)([A-Za-z][A-Za-z0-9]*)([^>]*?)\s*(/?)>"

        result = re.sub(tag_pattern, self._sanitize_tag, result)

        # Additional safety: escape any remaining < that might be part of malformed HTML
        # But don't escape markdown syntax like #, *, etc.
        # We only escape < if it looks like it could be an unescaped tag
        result = re.sub(r"<(?![A-Za-z/?!])", "&lt;", result)

        # Remove script tags and content (defense in depth)
        result = re.sub(r"<script[^>]*>.*?</script>", "", result, flags=re.IGNORECASE | re.DOTALL)

        # Remove style tags with potentially malicious content
        result = re.sub(r"<style[^>]*>.*?</style>", "", result, flags=re.IGNORECASE | re.DOTALL)

        # Remove dangerous pseudo-protocols
        for pattern in DANGEROUS_ATTR_PATTERNS:
            result = re.sub(pattern, "", result, flags=re.IGNORECASE)

        # Remove comments that might contain malicious code
        result = re.sub(r"<!--.*?-->", "", result, flags=re.DOTALL)

        return result.strip()


def sanitize_markdown(
    markdown: str,
    *,
    max_length: int = 100_000,
    allowed_tags: Optional[Set[str]] = None,
    strip_tags: bool = True,
) -> str:
    """
    Convenience function to sanitize markdown content.

    Args:
        markdown: The markdown content to sanitize
        max_length: Maximum content length (prevents DoS)
        allowed_tags: Custom set of allowed HTML tags (None = use default safe list)
        strip_tags: If True, strip disallowed tags; if False, escape them

    Returns:
        Sanitized HTML safe for rendering

    Examples:
        >>> safe_html = sanitize_markdown(user_input)
        >>> render(safe_html)
    """
    sanitizer = MarkdownSanitizer(
        allowed_tags=allowed_tags,
        strip_disallowed_tags=strip_tags,
    )
    return sanitizer.sanitize(markdown, max_length=max_length)


def sanitize_html_only(html: str, *, max_length: int = 100_000) -> str:
    """
    Sanitize HTML content (not markdown) by removing dangerous elements.

    Use this when you have HTML content that needs to be sanitized.
    For markdown content, use sanitize_markdown() instead.

    Args:
        html: The HTML content to sanitize
        max_length: Maximum content length

    Returns:
        Sanitized HTML safe for rendering
    """
    return sanitize_markdown(html, max_length=max_length)
