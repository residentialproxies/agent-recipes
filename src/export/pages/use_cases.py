"""
Use-case landing pages.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from src.export.data import USE_CASES
from src.export.pages._shared import filter_agents, sort_agents
from src.export.templates import _render_category_landing
from src.export._utils import _write


def generate_use_case_pages(
    agents: list[dict],
    output_dir: Path,
    *,
    base_url: Optional[str],
    site_url: str,
    additional_urls: list[str],
) -> None:
    for slug, cfg in USE_CASES.items():
        matched = filter_agents(agents, cfg["criteria"])
        matched = sort_agents(matched, sort_by="stars")

        intro = f"""<section class="about">
<h2>What you can build</h2>
<p>{cfg["description"]}</p>
<h2>Tips</h2>
<ul>
  <li>Start with a beginner-friendly example, then upgrade models/tools.</li>
  <li>Prefer projects with clear READMEs and reproducible setup.</li>
  <li>For production: add monitoring, evals, and rate limiting.</li>
</ul>
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
                related_links=[("All Agents", "/"), ("Comparisons", "/compare/"), ("Tutorials", "/how-to/")],
            ),
        )
        additional_urls.append(f"{site_url}/{slug}/")

