"""
Secure secrets management.

Provides secure loading of API keys and other secrets
without exposing them in process lists or environment variables.

Uses file-based configuration with restricted permissions.
"""

import json
import logging
import os
import stat
from pathlib import Path

logger = logging.getLogger(__name__)


class SecretsManager:
    """
    Manages secrets securely from file-based configuration.

    Security benefits:
    - Secrets not exposed in process list (ps aux)
    - Secrets not exposed in environment variables
    - File permissions restricted to owner-only (600)
    - Secrets loaded only when needed
    - Clear error messages for misconfiguration

    Usage:
        # Create secrets file at .streamlit/secrets.json:
        # {
        #   "ANTHROPIC_API_KEY": "sk-ant-...",
        #   "OPENAI_API_KEY": "sk-..."
        # }

        manager = SecretsManager()
        api_key = manager.get("ANTHROPIC_API_KEY")
    """

    def __init__(self, secrets_path: str | Path | None = None):
        """
        Initialize the secrets manager.

        Args:
            secrets_path: Path to secrets file. If None, searches standard locations.
        """
        self.secrets_path = self._find_secrets_file(secrets_path)
        self._secrets_cache: dict[str, str] | None = None

    def _find_secrets_file(self, provided_path: str | Path | None) -> Path | None:
        """
        Find the secrets file in standard locations.

        Search order:
        1. Provided path (if given)
        2. .streamlit/secrets.json
        3. .secrets.json
        4. Secrets from Streamlit secrets (if available)

        Args:
            provided_path: Explicitly provided path

        Returns:
            Path to secrets file, or None if using Streamlit secrets
        """
        if provided_path:
            path = Path(provided_path)
            if path.exists():
                self._validate_secrets_file(path)
                return path
            else:
                # Will be created if it doesn't exist
                return path

        # Check standard locations
        standard_paths = [
            Path(".streamlit/secrets.json"),
            Path(".secrets.json"),
        ]

        for path in standard_paths:
            if path.exists():
                self._validate_secrets_file(path)
                return path

        # No file found - will use Streamlit secrets or environment
        return None

    def _validate_secrets_file(self, path: Path) -> None:
        """
        Validate secrets file permissions.

        Ensures file is not readable by group/others.

        Args:
            path: Path to secrets file

        Raises:
            PermissionError: If file permissions are too permissive
        """
        if not path.exists():
            return

        file_stat = path.stat()
        file_mode = file_stat.st_mode

        # Check if group or others have read permissions
        if file_mode & (stat.S_IRGRP | stat.S_IROTH):
            raise PermissionError(f"Secrets file {path} has insecure permissions. " f"Please run: chmod 600 {path}")

        # Check if group or others have write permissions
        if file_mode & (stat.S_IWGRP | stat.S_IWOTH):
            raise PermissionError(f"Secrets file {path} has insecure permissions. " f"Please run: chmod 600 {path}")

    def _load_secrets(self) -> dict[str, str]:
        """
        Load secrets from file or Streamlit.

        This is the only place where secrets are actually read from storage.
        After loading, they are cached in memory.

        Returns:
            Dictionary of secret name to value

        Raises:
            PermissionError: If file permissions are insecure
            json.JSONDecodeError: If file contains invalid JSON
        """
        # Use cached value if available
        if self._secrets_cache is not None:
            return self._secrets_cache

        secrets = {}

        # Try loading from file
        if self.secrets_path and self.secrets_path.exists():
            self._validate_secrets_file(self.secrets_path)

            try:
                with open(self.secrets_path) as f:
                    secrets = json.load(f)
            except json.JSONDecodeError as e:
                raise json.JSONDecodeError(
                    f"Invalid JSON in secrets file {self.secrets_path}: {e.msg}",
                    e.doc,
                    e.pos,
                ) from e
        else:
            # Try Streamlit secrets as fallback
            try:
                from streamlit import secrets as st_secrets

                # Streamlit secrets is a dict-like object
                secrets = dict(st_secrets)
            except ImportError:
                pass
            except Exception as exc:
                # Streamlit secrets not available - ignore
                logger.debug("Streamlit secrets unavailable: %s", exc)

        # Also check environment variables (with security warning)
        # We prefer file-based loading over env vars
        env_prefixes = ["ANTHROPIC_", "OPENAI_", "GROQ_", "COHERE_"]
        for key in os.environ:
            if any(key.startswith(prefix) for prefix in env_prefixes) and key not in secrets:
                # Note: Env vars are less secure than file-based
                # but we allow them for compatibility
                secrets[key] = os.environ[key]

        self._secrets_cache = secrets
        return secrets

    def get(self, key: str, default: str | None = None) -> str | None:
        """
        Get a secret value.

        Args:
            key: Secret name
            default: Default value if secret not found

        Returns:
            Secret value, or default if not found
        """
        secrets = self._load_secrets()
        return secrets.get(key, default)

    def get_required(self, key: str) -> str:
        """
        Get a required secret value.

        Args:
            key: Secret name

        Returns:
            Secret value

        Raises:
            KeyError: If secret not found
        """
        secrets = self._load_secrets()
        if key not in secrets:
            raise KeyError(f"Required secret '{key}' not found in secrets configuration")

        return secrets[key]

    def set(self, key: str, value: str) -> None:
        """
        Set a secret value.

        This will create or update the secrets file.

        Args:
            key: Secret name
            value: Secret value
        """
        if self._secrets_cache is None:
            self._secrets_cache = {}

        self._secrets_cache[key] = value

        # Save to file
        if not self.secrets_path:
            self.secrets_path = Path(".streamlit/secrets.json")

        self.secrets_path.parent.mkdir(parents=True, exist_ok=True)

        # Write with restricted permissions
        # Write to temp file first
        temp_path = self.secrets_path.with_suffix(".tmp")
        with open(temp_path, "w") as f:
            json.dump(self._secrets_cache, f, indent=2)

        # Set restrictive permissions (600 - owner read/write only)
        temp_path.chmod(0o600)

        # Atomic rename
        temp_path.replace(self.secrets_path)

    def has(self, key: str) -> bool:
        """
        Check if a secret exists.

        Args:
            key: Secret name

        Returns:
            True if secret exists
        """
        secrets = self._load_secrets()
        return key in secrets

    def list_secrets(self) -> list[str]:
        """
        List all available secret names.

        Returns:
            List of secret names
        """
        secrets = self._load_secrets()
        return list(secrets.keys())

    def create_example_config(self, path: str | Path | None = None) -> Path:
        """
        Create an example secrets configuration file.

        Args:
            path: Path to create example file at

        Returns:
            Path to created file
        """
        path = Path(".streamlit/secrets.example.json") if path is None else Path(path)

        path.parent.mkdir(parents=True, exist_ok=True)

        example_config = {
            "ANTHROPIC_API_KEY": "sk-ant-your-key-here",
            "OPENAI_API_KEY": "sk-your-key-here",
            "GROQ_API_KEY": "gsk-your-key-here",
            "COHERE_API_KEY": "your-key-here",
            "_comment": "Replace these with your actual API keys. Never commit this file!",
        }

        with open(path, "w") as f:
            json.dump(example_config, f, indent=2)

        return path


# Global secrets manager instance
_secrets_manager: SecretsManager | None = None


def get_secrets_manager(secrets_path: str | Path | None = None) -> SecretsManager:
    """
    Get the global secrets manager instance.

    Args:
        secrets_path: Path to secrets file

    Returns:
        SecretsManager instance
    """
    global _secrets_manager

    if _secrets_manager is None:
        _secrets_manager = SecretsManager(secrets_path)

    return _secrets_manager


def get_api_key(provider: str) -> str | None:
    """
    Convenience function to get an API key for a provider.

    Args:
        provider: Provider name (e.g., 'anthropic', 'openai')

    Returns:
        API key, or None if not found
    """
    manager = get_secrets_manager()
    key_name = f"{provider.upper()}_API_KEY"
    return manager.get(key_name)
