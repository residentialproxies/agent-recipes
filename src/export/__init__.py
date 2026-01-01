"""
Agent Navigator - Static Site Export Package
=============================================
Generates a lightweight, SEO-friendly static site from `data/agents.json`.

Usage:
  from src.export import export_site
  export_site(data_path, output_dir, base_url="https://example.com")

Or via CLI:
  python3 -m src.export --output site --base-url https://example.com
"""

from __future__ import annotations

from src.export.export import export_site

__all__ = ["export_site"]
