"""
Agent Navigator - Static Site Exporter (Compatibility Shim)
===========================================================

Historically, this project exposed a monolithic `src/export_static.py` module.
The production implementation now lives in the `src.export` package; this file
remains to preserve imports and CLI entrypoints.
"""

from __future__ import annotations

from src.export._utils import (
    _category_icon,
    _iso_date,
    _normalize_record,
    _read_json,
    _write,
)
from src.export._utils import (
    _slug as _slug_impl,
)
from src.export.data import (
    CATEGORY_PAGES,
    COMPARISON_CONFIGS,
    COMPLEXITY_PAGES,
    FRAMEWORK_PAGES,
    PROVIDER_PAGES,
    TUTORIAL_CONFIGS,
    _find_related_agents,
)
from src.export.export import export_site, main
from src.export.schema import (
    _generate_breadcrumb_schema,
    _generate_faq_schema,
    _generate_schema_org,
)
from src.export.seo import (
    _generate_meta_description,
    _generate_open_graph_tags,
)
from src.export.templates import (
    _layout,
    _render_404,
    _render_agent,
    _render_assets,
    _render_category_landing,
    _render_comparison_index,
    _render_comparison_page,
    _render_headers,
    _render_index,
    _render_sitemap,
    _render_tutorial_index,
    _render_tutorial_page,
)


def _slug(value: str) -> str:
    """
    Backward-compatible slug helper.

    The new implementation defaults to shorter slugs for SEO; legacy tests and
    callers expect a longer max length.
    """

    return _slug_impl(value, max_length=80)


__all__ = [
    "export_site",
    "main",
    "_layout",
    "_render_index",
    "_render_agent",
    "_render_category_landing",
    "_render_comparison_page",
    "_render_tutorial_page",
    "_render_comparison_index",
    "_render_tutorial_index",
    "_render_404",
    "_render_assets",
    "_render_headers",
    "_render_sitemap",
    "_generate_meta_description",
    "_generate_open_graph_tags",
    "_generate_schema_org",
    "_generate_faq_schema",
    "_generate_breadcrumb_schema",
    "_find_related_agents",
    "CATEGORY_PAGES",
    "FRAMEWORK_PAGES",
    "PROVIDER_PAGES",
    "COMPLEXITY_PAGES",
    "COMPARISON_CONFIGS",
    "TUTORIAL_CONFIGS",
    "_read_json",
    "_write",
    "_slug",
    "_iso_date",
    "_category_icon",
    "_normalize_record",
]

