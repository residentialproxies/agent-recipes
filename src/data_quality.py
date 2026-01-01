"""
Data quality utilities for agent index.
"""

from typing import Optional
import re

# Stop words to filter from tags
_LOW_VALUE_TAGS = {
    "allows", "and", "app", "application", "available", "based", "can", 
    "describing", "detailed", "download", "enter", "etc", "features", 
    "for", "format", "friendly", "generate", "generated", "generation", 
    "input", "instruments", "interface", "listening", "model", "modelslab",
    "mood", "mp3", "music", "output", "prompt", "simple", "this", "they",
    "the", "track", "type", "user", "users", "want", "will", "with",
}

def filter_low_value_tags(tags: list[str]) -> list[str]:
    """Remove low-value generic words from tags."""
    return [t for t in tags if t.lower() not in _LOW_VALUE_TAGS and len(t) > 2]

def generate_seo_description(agent: dict) -> str:
    """Generate SEO-friendly description when empty or too short."""
    category = agent.get("category", "")
    frameworks = agent.get("frameworks", [])
    providers = agent.get("llm_providers", [])
    complexity = agent.get("complexity", "")
    
    templates = {
        "rag": f"Build RAG applications using {frameworks[0] if frameworks else 'Python'} with {providers[0] if providers else 'OpenAI'}. Complete example with vector database integration.",
        "chatbot": f"Create an AI chatbot using {frameworks[0] if frameworks else 'direct API'} with {providers[0] if providers else 'GPT'}. Includes conversation memory and user interface.",
        "multi_agent": f"Multi-agent system using {frameworks[0] if frameworks else 'custom orchestrator'}. Agents collaborate on complex tasks with tool use.",
        "agent": f"LLM agent implementation using {frameworks[0] if frameworks else 'Python'} with {providers[0] if providers else 'OpenAI'}.",
    }
    
    return templates.get(category, f"{category.replace('_', ' ').title()} agent example with code and setup instructions.")

def validate_agent_data(agent: dict) -> tuple[bool, list[str]]:
    """Validate agent data and return (is_valid, list_of_issues)."""
    issues = []
    
    if not agent.get("id"):
        issues.append("Missing required field: id")
    if not agent.get("name"):
        issues.append("Missing required field: name")
    if not agent.get("description"):
        issues.append("Missing description (consider auto-generating)")
    if agent.get("category") == "other":
        issues.append("Uncategorized agent (category='other')")
    
    return len(issues) == 0, issues

def generate_agent_tags(agent: dict) -> list[str]:
    """Generate relevant tags from agent metadata."""
    tags = set()
    
    # Add category
    if cat := agent.get("category"):
        tags.add(cat.replace("_", " "))
    
    # Add frameworks
    for fw in agent.get("frameworks", []):
        if fw != "raw_api":
            tags.add(fw)
    
    # Add providers
    for prov in agent.get("llm_providers", []):
        tags.add(prov)
    
    # Add complexity
    if comp := agent.get("complexity"):
        tags.add(comp)
    
    # Add capability tags
    if agent.get("requires_gpu"):
        tags.add("gpu-required")
    if agent.get("supports_local_models"):
        tags.add("local-models")
    
    return list(tags)
