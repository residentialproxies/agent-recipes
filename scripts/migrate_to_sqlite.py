#!/usr/bin/env python3
"""
SQLite Migration Script
=======================
Migrate agents.json to SQLite FTS5 database for better scalability.

Usage:
    python scripts/migrate_to_sqlite.py
    python scripts/migrate_to_sqlite.py --input data/agents.json --output data/agents.db
"""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.search_sqlite import migrate_from_json


def main():
    parser = argparse.ArgumentParser(
        description="Migrate agents.json to SQLite FTS5 database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Default: migrate data/agents.json to data/agents.db
  python scripts/migrate_to_sqlite.py

  # Custom paths
  python scripts/migrate_to_sqlite.py --input my_agents.json --output my_agents.db

After migration:
  1. Test the SQLite backend:
     SEARCH_ENGINE=sqlite uvicorn src.api:app --reload

  2. If everything works, set SEARCH_ENGINE=sqlite in production

Benefits:
  - Supports 100k+ agents (vs 5k limit with BM25)
  - Constant memory usage (~5MB regardless of corpus size)
  - Faster startup (no tokenization overhead)
  - Built-in BM25 ranking
""",
    )

    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/agents.json"),
        help="Input JSON file (default: data/agents.json)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/agents.db"),
        help="Output SQLite database (default: data/agents.db)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing database",
    )

    args = parser.parse_args()

    # Check input file exists
    if not args.input.exists():
        print(f"Error: Input file not found: {args.input}")
        return 1

    # Check output file
    if args.output.exists() and not args.force:
        print(f"Error: Output file already exists: {args.output}")
        print("Use --force to overwrite")
        return 1

    # Perform migration
    try:
        migrate_from_json(args.input, args.output)
        print(f"\n✅ Migration successful!")
        print(f"   Input:  {args.input}")
        print(f"   Output: {args.output}")
        print(f"\nTo use SQLite backend, set: SEARCH_ENGINE=sqlite")
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
