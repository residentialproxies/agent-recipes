#!/usr/bin/env python3
"""
Data quality report generator for agents.json.

Analyzes the agent index and reports:
- Empty descriptions count
- Uncategorized agents count  
- Missing GitHub stars
- Agents with minimal data
- Tag quality issues
"""

import argparse
import json
import sys
from pathlib import Path
from collections import Counter, defaultdict


def load_agents(data_path: Path) -> list[dict]:
    """Load agents from JSON file."""
    if not data_path.exists():
        print(f"Error: {data_path} does not exist")
        sys.exit(1)
    return json.loads(data_path.read_text(encoding="utf-8"))


def analyze_descriptions(agents: list[dict]) -> dict:
    """Analyze description quality."""
    empty = 0
    short = 0
    good = 0
    empty_agents = []

    for agent in agents:
        desc = agent.get("description", "")
        if not desc or desc.strip() == "":
            empty += 1
            empty_agents.append(agent.get("id", "unknown"))
        elif len(desc) < 50:
            short += 1
        else:
            good += 1

    return {
        "empty_count": empty,
        "short_count": short,
        "good_count": good,
        "empty_sample": empty_agents[:10],
    }


def analyze_categories(agents: list[dict]) -> dict:
    """Analyze category distribution."""
    category_counts = Counter(a.get("category", "unknown") for a in agents)
    uncategorized = [a for a in agents if a.get("category") == "other"]
    
    return {
        "distribution": dict(category_counts.most_common()),
        "uncategorized_count": len(uncategorized),
        "uncategorized_sample": [a.get("id") for a in uncategorized[:10]],
    }


def analyze_stars(agents: list[dict]) -> dict:
    """Analyze GitHub stars data."""
    missing_stars = [a for a in agents if a.get("stars") is None]
    with_stars = [a for a in agents if a.get("stars") is not None]
    
    # Top agents by stars
    top_by_stars = sorted(with_stars, key=lambda a: a.get("stars", 0), reverse=True)[:10]
    
    return {
        "missing_count": len(missing_stars),
        "with_stars_count": len(with_stars),
        "top_stars": [
            {"id": a.get("id"), "name": a.get("name"), "stars": a.get("stars")}
            for a in top_by_stars
        ],
    }


def analyze_minimal_data(agents: list[dict]) -> dict:
    """Find agents with minimal/missing data."""
    minimal = []
    
    for agent in agents:
        issues = []
        
        if not agent.get("description"):
            issues.append("no_description")
        if agent.get("category") == "other":
            issues.append("uncategorized")
        if not agent.get("frameworks") or agent.get("frameworks") == ["other"]:
            issues.append("no_framework")
        if not agent.get("tags"):
            issues.append("no_tags")
        if not agent.get("quick_start"):
            issues.append("no_quick_start")
            
        if len(issues) >= 2:
            minimal.append({
                "id": agent.get("id"),
                "name": agent.get("name"),
                "issues": issues,
            })
    
    return {
        "count": len(minimal),
        "samples": minimal[:15],
    }


def analyze_tags(agents: list[dict]) -> dict:
    """Analyze tag quality."""
    low_value_tags = {
        "allows", "and", "app", "application", "available", "based", "can",
        "describing", "detailed", "download", "enter", "etc", "features",
        "for", "format", "friendly", "generate", "generated", "generation",
        "input", "instruments", "interface", "listening", "model", "modelslab",
        "mood", "mp3", "music", "output", "prompt", "simple", "this", "they",
        "the", "track", "type", "user", "users", "want", "will", "with",
    }
    
    tag_counts = Counter()
    low_value_counts = Counter()
    empty_tags = 0
    
    for agent in agents:
        tags = agent.get("tags", [])
        if not tags:
            empty_tags += 1
        
        for tag in tags:
            tag_lower = tag.lower()
            tag_counts[tag] += 1
            if tag_lower in low_value_tags or len(tag) <= 2:
                low_value_counts[tag] += 1
    
    return {
        "empty_tags_count": empty_tags,
        "unique_tags": len(tag_counts),
        "most_common_tags": dict(tag_counts.most_common(20)),
        "low_value_sample": dict(low_value_counts.most_common(15)),
    }


def analyze_frameworks(agents: list[dict]) -> dict:
    """Analyze framework distribution."""
    framework_counts = Counter()
    provider_counts = Counter()
    
    for agent in agents:
        for fw in agent.get("frameworks", []):
            framework_counts[fw] += 1
        for prov in agent.get("llm_providers", []):
            provider_counts[prov] += 1
    
    return {
        "frameworks": dict(framework_counts.most_common()),
        "llm_providers": dict(provider_counts.most_common()),
    }


def generate_report(agents: list[dict]) -> str:
    """Generate comprehensive data quality report."""
    total = len(agents)
    
    descriptions = analyze_descriptions(agents)
    categories = analyze_categories(agents)
    stars = analyze_stars(agents)
    minimal = analyze_minimal_data(agents)
    tags = analyze_tags(agents)
    frameworks = analyze_frameworks(agents)
    
    lines = [
        "=" * 70,
        "DATA QUALITY REPORT",
        "=" * 70,
        f"Total agents: {total}",
        "",
        "-" * 70,
        "DESCRIPTIONS",
        "-" * 70,
        f"  Empty:     {descriptions['empty_count']:4d} ({descriptions['empty_count']*100//total}%)" if total else "  Empty:     0",
        f"  Short:     {descriptions['short_count']:4d} ({descriptions['short_count']*100//total}%)" if total else "  Short:     0",
        f"  Good:      {descriptions['good_count']:4d} ({descriptions['good_count']*100//total}%)" if total else "  Good:      0",
    ]
    
    if descriptions["empty_sample"]:
        lines.append("\n  Sample agents with empty descriptions:")
        for aid in descriptions["empty_sample"][:5]:
            lines.append(f"    - {aid}")
    
    lines.extend([
        "",
        "-" * 70,
        "CATEGORIES",
        "-" * 70,
        f"  Uncategorized: {categories['uncategorized_count']} ({categories['uncategorized_count']*100//total}%)" if total else "  Uncategorized: 0",
        "",
        "  Distribution:",
    ])
    
    for cat, count in categories["distribution"].items():
        pct = count * 100 // total if total else 0
        lines.append(f"    {cat:15s}: {count:4d} ({pct}%)")
    
    lines.extend([
        "",
        "-" * 70,
        "GITHUB STARS",
        "-" * 70,
        f"  With stars:    {stars['with_stars_count']}",
        f"  Missing stars: {stars['missing_count']}",
    ])
    
    if stars["top_stars"]:
        lines.append("\n  Top agents by stars:")
        for agent in stars["top_stars"][:5]:
            lines.append(f"    {agent['stars']:6d} - {agent['name']}")
    
    lines.extend([
        "",
        "-" * 70,
        "MINIMAL DATA ISSUES",
        "-" * 70,
        f"  Agents with 2+ issues: {minimal['count']}",
    ])
    
    if minimal["samples"]:
        lines.append("\n  Sample agents with data issues:")
        for agent in minimal["samples"][:5]:
            lines.append(f"    {agent['id']}: {', '.join(agent['issues'])}")
    
    lines.extend([
        "",
        "-" * 70,
        "TAGS",
        "-" * 70,
        f"  Agents without tags: {tags['empty_tags_count']}",
        f"  Unique tags:         {tags['unique_tags']}",
        "",
        "  Most common tags:",
    ])
    
    for tag, count in list(tags["most_common_tags"].items())[:10]:
        lines.append(f"    {tag:20s}: {count:4d}")
    
    if tags["low_value_sample"]:
        lines.extend([
            "",
            "  Low-value tags found (should be filtered):",
        ])
        for tag, count in list(tags["low_value_sample"].items())[:8]:
            lines.append(f"    {tag:20s}: {count:4d}")
    
    lines.extend([
        "",
        "-" * 70,
        "FRAMEWORKS & LLM PROVIDERS",
        "-" * 70,
        "  Frameworks:",
    ])
    
    for fw, count in frameworks["frameworks"].items():
        lines.append(f"    {fw:20s}: {count:4d}")
    
    lines.extend([
        "",
        "  LLM Providers:",
    ])
    
    for prov, count in frameworks["llm_providers"].items():
        lines.append(f"    {prov:20s}: {count:4d}")
    
    lines.extend([
        "",
        "=" * 70,
    ])
    
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate data quality report for agents.json",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--data",
        type=Path,
        default=Path("data/agents.json"),
        help="Path to agents.json file",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON instead of text",
    )
    
    args = parser.parse_args()
    
    agents = load_agents(args.data)
    
    if args.json:
        report = {
            "total_agents": len(agents),
            "descriptions": analyze_descriptions(agents),
            "categories": analyze_categories(agents),
            "stars": analyze_stars(agents),
            "minimal_data": analyze_minimal_data(agents),
            "tags": analyze_tags(agents),
            "frameworks": analyze_frameworks(agents),
        }
        print(json.dumps(report, indent=2))
    else:
        print(generate_report(agents))
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
