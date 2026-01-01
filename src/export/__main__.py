"""
CLI entry point for running the export module directly.

Usage:
  python3 -m src.export --output site --base-url https://example.com
"""

from src.export.export import main

if __name__ == "__main__":
    raise SystemExit(main())
