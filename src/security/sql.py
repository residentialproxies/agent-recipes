"""
SQL injection prevention utilities.

Provides functions to safely escape user input for SQL queries,
particularly for LIKE clauses where wildcard characters need special handling.
"""

import re


def escape_like_pattern(pattern: str, escape_char: str = "\\") -> str:
    """
    Escape user input for safe use in SQL LIKE clauses.

    In SQL LIKE clauses, % matches any number of characters and _
    matches exactly one character. This function escapes these wildcards
    so they are treated as literal characters.

    Attack vector without escaping:
    - Input: "admin' OR '1'='1" -> LIKE '%admin' OR '1'='1%' matches all rows
    - Input: "%" -> matches all rows (data leak)
    - Input: "_" -> matches any single character (unintended results)

    Args:
        pattern: The user input to escape
        escape_char: The character to use as escape (default: backslash)

    Returns:
        Escaped pattern safe for use in LIKE clauses

    Examples:
        >>> escape_like_pattern("test%file")
        "test\\%file"
        >>> escape_like_pattern("user_input")
        "user_input"
        >>> escape_like_pattern("100%")
        "100\\%"

    Security:
        - Always use this before putting user input in LIKE patterns
        - Use the escape character in the LIKE clause: LIKE pattern ESCAPE '\\'
    """
    if not isinstance(pattern, str):
        raise TypeError(f"Pattern must be a string, got {type(pattern).__name__}")

    if not pattern:
        return ""

    # Escape the escape character first
    result = pattern.replace(escape_char, escape_char + escape_char)

    # Then escape SQL LIKE wildcards
    result = result.replace("%", escape_char + "%")
    result = result.replace("_", escape_char + "_")

    return result


def build_like_clause(
    column: str, pattern: str, escape_char: str = "\\", *, _case_sensitive: bool = False
) -> tuple[str, list]:
    """
    Build a safe SQL LIKE clause with escaped user input.

    This function returns both the SQL fragment and the parameter value,
    ensuring the user input is properly escaped for LIKE queries.

    Args:
        column: The column name to search (must be a trusted identifier)
        pattern: The user-supplied search pattern
        escape_char: The escape character to use
        case_sensitive: Whether the search should be case sensitive

    Returns:
        Tuple of (sql_fragment, params) for use with sqlite3

    Examples:
        >>> sql, params = build_like_clause("name", "test%")
        >>> sql
        "name LIKE ? ESCAPE '\\'"
        >>> params
        ['test\\%']
        >>> cursor.execute(f"SELECT * FROM agents WHERE {sql}", params)

    Security:
        - Always use parameterized queries (this function returns params)
        - Never interpolate the pattern directly into SQL
    """
    if not column or not isinstance(column, str):
        raise ValueError("Column must be a non-empty string")

    # Validate column name to prevent SQL injection via column name
    # Only allow alphanumeric, underscore, and dot (for table.column)
    if not re.match(r"^[A-Za-z_][A-Za-z0-9_.]*$", column):
        raise ValueError(f"Invalid column name: {column}")

    escaped_pattern = escape_like_pattern(pattern, escape_char)
    like_pattern = f"%{escaped_pattern}%"

    # Build the SQL fragment
    sql = f"{column} LIKE ? ESCAPE '{escape_char}'"

    return sql, [like_pattern]


def validate_search_input(query: str, *, max_length: int = 200, allowed_chars: set | None = None) -> str:
    """
    Validate and sanitize search query input.

    Provides defense in depth for search inputs by:
    - Enforcing length limits
    - Optionally restricting to allowed characters
    - Removing NULL bytes and control characters

    Args:
        query: The search query to validate
        max_length: Maximum allowed length
        allowed_chars: Set of allowed characters (None = allow all printable)

    Returns:
        Validated query string

    Raises:
        ValueError: If validation fails
    """
    if not isinstance(query, str):
        raise TypeError(f"Query must be a string, got {type(query).__name__}")

    # Enforce length limit
    if len(query) > max_length:
        raise ValueError(f"Query exceeds maximum length of {max_length} characters")

    # Remove NULL bytes and control characters (except tab, newline, carriage return)
    query = "".join(
        char for char in query if char == "\t" or char == "\n" or char == "\r" or (ord(char) >= 32 and ord(char) < 127)
    )

    # Validate against allowed characters if specified
    if allowed_chars is not None and not all(char in allowed_chars for char in query):
        raise ValueError("Query contains disallowed characters")

    return query.strip()
