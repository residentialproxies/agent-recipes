"""
Pytest configuration and shared fixtures for agent-recipes tests.
"""

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict

import pytest


# Add src to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def sample_agents() -> list[Dict[str, Any]]:
    """Sample agent data for testing."""
    return [
        {
            "id": "pdf_assistant",
            "name": "PDF Document Assistant",
            "description": "Chat with your PDF documents using RAG",
            "category": "rag",
            "frameworks": ["langchain"],
            "llm_providers": ["openai"],
            "design_pattern": "rag",
            "complexity": "beginner",
            "supports_local_models": False,
            "requires_gpu": False,
            "api_keys": ["OPENAI_API_KEY"],
            "github_url": "https://github.com/foo/bar/tree/main/pdf_assistant",
            "folder_path": "pdf_assistant",
            "readme_relpath": "pdf_assistant/README.md",
            "stars": 1234,
            "updated_at": 1704067200,
            "languages": ["python"],
            "tags": ["pdf", "rag", "document"],
        },
        {
            "id": "finance_agent",
            "name": "Financial Analyst Agent",
            "description": "AI agent for stock analysis and portfolio management",
            "category": "finance",
            "frameworks": ["crewai", "langchain"],
            "llm_providers": ["openai", "anthropic"],
            "design_pattern": "multi_agent",
            "complexity": "advanced",
            "supports_local_models": False,
            "requires_gpu": True,
            "api_keys": ["OPENAI_API_KEY", "ANTHROPIC_API_KEY"],
            "github_url": "https://github.com/foo/bar/tree/main/finance_agent",
            "folder_path": "finance_agent",
            "readme_relpath": "finance_agent/README.md",
            "stars": 567,
            "updated_at": 1704153600,
            "languages": ["python", "javascript"],
            "tags": ["finance", "trading", "stocks"],
        },
        {
            "id": "local_chat",
            "name": "Local LLM Chatbot",
            "description": "Run chatbot completely offline with Ollama",
            "category": "chatbot",
            "frameworks": ["raw_api"],
            "llm_providers": ["ollama"],
            "design_pattern": "simple_chat",
            "complexity": "beginner",
            "supports_local_models": True,
            "requires_gpu": False,
            "api_keys": [],
            "github_url": "https://github.com/foo/bar/tree/main/local_chat",
            "folder_path": "local_chat",
            "readme_relpath": "local_chat/README.md",
            "stars": 890,
            "updated_at": 1704240000,
            "languages": ["python"],
            "tags": ["chatbot", "local", "offline"],
        },
    ]


@pytest.fixture
def sample_readme_content() -> str:
    """Sample README content for testing extraction."""
    return """
# Local RAG Agent

This project is a RAG chatbot that uses embeddings and a vector database.
Runs locally with Ollama + GGUF. Requires GPU if you want speed.

Set OPENAI_API_KEY if using OpenAI.

## Features

- LangChain integration
- ChromaDB vector store
- Support for local models via Ollama

## Quick Start

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Configuration

Create a `.env` file with:
```
OPENAI_API_KEY=your_key_here
```
"""


@pytest.fixture
def sample_readme_rag() -> str:
    """Sample README for a RAG application."""
    return """
# PDF RAG Assistant

A RAG-based assistant for querying PDF documents using LangChain and OpenAI.

## Setup

```bash
pip install langchain openai chromadb
export OPENAI_API_KEY=sk-...
python app.py
```

## Features

- PDF document processing
- Vector embeddings with ChromaDB
- Retrieval-augmented generation
"""


@pytest.fixture
def sample_readme_chatbot() -> str:
    """Sample README for a chatbot application."""
    return """
# Customer Support Chatbot

A simple chatbot for customer support using OpenAI GPT-4.

## Installation

```bash
npm install
npm start
```

Set your OPENAI_API_KEY in .env file.
"""


@pytest.fixture
def tmp_repo_dir(tmp_path: Path) -> Path:
    """Create a temporary repository structure for testing."""
    repo = tmp_path / "test_repo"
    repo.mkdir()

    # Create some agent directories with READMEs
    agents = {
        "agent_one": "# Agent One\n\nA simple agent",
        "agent_two": "# Agent Two\n\nAnother agent with more features\n\nUses LangChain and OpenAI.",
    }

    for agent_name, readme_content in agents.items():
        agent_dir = repo / agent_name
        agent_dir.mkdir()
        (agent_dir / "README.md").write_text(readme_content, encoding="utf-8")
        (agent_dir / "main.py").write_text("print('hello')", encoding="utf-8")

    # Create nested agent
    nested_dir = repo / "nested" / "deep_agent"
    nested_dir.mkdir(parents=True)
    (nested_dir / "README.md").write_text("# Deep Agent\n\nNested agent", encoding="utf-8")

    # Create excluded directory
    excluded_dir = repo / "node_modules" / "package"
    excluded_dir.mkdir(parents=True)
    (excluded_dir / "README.md").write_text("# Excluded", encoding="utf-8")

    return repo


@pytest.fixture
def agents_json_path(tmp_path: Path, sample_agents: list[Dict[str, Any]]) -> Path:
    """Create a temporary agents.json file for testing."""
    agents_file = tmp_path / "agents.json"
    agents_file.write_text(json.dumps(sample_agents), encoding="utf-8")
    return agents_file


@pytest.fixture
def mock_anthropic_response() -> Dict[str, Any]:
    """Mock Anthropic API response for LLM extraction."""
    return {
        "name": "Test Agent",
        "description": "A test agent from LLM",
        "category": "rag",
        "frameworks": ["langchain"],
        "llm_providers": ["openai"],
        "requires_gpu": False,
        "supports_local_models": False,
        "design_pattern": "rag",
        "complexity": "intermediate",
        "quick_start": "pip install -r requirements.txt\npython app.py",
        "api_keys": ["OPENAI_API_KEY"],
    }
