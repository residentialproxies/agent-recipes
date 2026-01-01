"""
Tech combo pSEO pages.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from src.export.data import TECH_COMBOS
from src.export.pages._shared import filter_agents, sort_agents
from src.export.templates import _render_category_landing
from src.export._utils import _write


def generate_tech_combo_pages(
    agents: list[dict],
    output_dir: Path,
    *,
    base_url: Optional[str],
    site_url: str,
    additional_urls: list[str],
) -> None:
    for slug, cfg in TECH_COMBOS.items():
        matched = filter_agents(agents, cfg["criteria"])
        matched = sort_agents(matched, sort_by="stars")

        intro = f"""<section class="about">
<h2>Why this combo?</h2>
<p>{cfg["description"]}</p>
<p>Browse runnable examples below. Each example links to the source with setup instructions.</p>
</section>"""

        _write(
            output_dir / slug / "index.html",
            _render_category_landing(
                slug,
                cfg["title"],
                matched,
                base_url=base_url,
                description=cfg["description"],
                heading=cfg["title"],
                intro_content=intro,
                related_links=[("All Agents", "/"), ("Compare", "/compare/"), ("How-To", "/how-to/")],
            ),
        )
        additional_urls.append(f"{site_url}/{slug}/")

