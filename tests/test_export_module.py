import json
from pathlib import Path

from src.export.export import export_site


def test_export_site_uses_raw_agent_id_paths(tmp_path: Path) -> None:
    data_path = tmp_path / "agents.json"
    data_path.write_text(
        json.dumps(
            [
                {
                    "id": "demo_agent_with_underscores",
                    "name": "Demo Agent",
                    "description": "Demo description",
                    "category": "agent",
                    "frameworks": ["langchain"],
                    "llm_providers": ["openai"],
                    "complexity": "beginner",
                    "github_url": "https://github.com/example/repo/tree/main/demo",
                }
            ]
        ),
        encoding="utf-8",
    )

    out_dir = tmp_path / "site"
    export_site(data_path, out_dir, base_url="https://example.com")

    agent_page = out_dir / "agents" / "demo-agent-with-underscores" / "index.html"
    assert agent_page.exists()

    index_html = (out_dir / "index.html").read_text(encoding="utf-8")
    assert "/agents/demo-agent-with-underscores/" in index_html
