"""
Pydantic models for API requests and responses.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field
from pydantic.config import ConfigDict


# =============================================================================
# Request Models
# =============================================================================


class SearchRequest(BaseModel):
    """Request model for agent search."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "q": "rag chatbot",
                    "category": ["rag", "chatbot"],
                    "framework": ["langchain"],
                    "provider": ["openai"],
                    "complexity": ["beginner"],
                    "local_only": False,
                    "sort": "-stars",
                    "page": 1,
                    "page_size": 20,
                }
            ]
        }
    )

    q: str = Field(default="", description="Search query", max_length=200)
    category: list[str] | str | None = Field(default=None, description="Filter by category")
    framework: list[str] | str | None = Field(default=None, description="Filter by framework")
    provider: list[str] | str | None = Field(default=None, description="Filter by LLM provider")
    complexity: list[str] | str | None = Field(default=None, description="Filter by complexity")
    local_only: bool = Field(default=False, description="Only show agents with local model support")
    sort: str | None = Field(default=None, max_length=40, description="Sort order (e.g., '-stars', 'name')")
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Results per page")


class AISelectRequest(BaseModel):
    """Request model for AI-powered agent selection."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "query": "I need a RAG chatbot for PDF documents that works with OpenAI",
                    "max_candidates": 50,
                    "category": ["rag"],
                    "framework": ["langchain"],
                    "provider": ["openai"],
                    "complexity": ["intermediate"],
                    "local_only": False,
                }
            ]
        }
    )

    query: str = Field(min_length=1, max_length=2000, description="Natural language query")
    max_candidates: int = Field(default=80, ge=10, le=120, description="Max candidates to consider")
    category: list[str] | str | None = Field(default=None, description="Filter by category")
    framework: list[str] | str | None = Field(default=None, description="Filter by framework")
    provider: list[str] | str | None = Field(default=None, description="Filter by LLM provider")
    complexity: list[str] | str | None = Field(default=None, description="Filter by complexity")
    local_only: bool = Field(default=False, description="Only show agents with local model support")


class WebManusConsultRequest(BaseModel):
    """Request model for WebManus consultation."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "problem": "I need to automate customer support responses",
                    "max_candidates": 50,
                    "capability": "automation",
                    "pricing": "free",
                    "min_score": 7.0,
                }
            ]
        }
    )

    problem: str = Field(min_length=1, max_length=2000, description="Problem description")
    max_candidates: int = Field(default=50, ge=10, le=120, description="Max candidates to consider")
    capability: str | None = Field(default=None, max_length=80, description="Filter by capability")
    pricing: str | None = Field(default=None, max_length=40, description="Filter by pricing tier")
    min_score: float = Field(default=0.0, ge=0.0, le=10.0, description="Minimum score threshold")


class FavoriteAddRequest(BaseModel):
    """Request model for adding a favorite."""

    model_config = ConfigDict(
        json_schema_extra={"examples": [{"agent_id": "pdf-chat-agent"}]}
    )

    agent_id: str = Field(min_length=1, max_length=100, description="Agent ID to favorite")


# =============================================================================
# Response Models
# =============================================================================


class AgentResponse(BaseModel):
    """Response model for a single agent."""

    model_config = ConfigDict(extra="allow")

    id: str = Field(description="Unique agent identifier")
    name: str = Field(description="Agent name")
    description: str = Field(description="Agent description")
    category: str = Field(description="Agent category")
    frameworks: list[str] = Field(default_factory=list, description="Frameworks used")
    llm_providers: list[str] = Field(default_factory=list, description="LLM providers")
    complexity: str = Field(description="Complexity level")
    github_url: str = Field(description="GitHub repository URL")
    stars: int | None = Field(None, description="GitHub stars count")
    updated_at: int | None = Field(None, description="Last update timestamp")
    tags: list[str] = Field(default_factory=list, description="Search tags")
    languages: list[str] = Field(default_factory=list, description="Programming languages")


class FilterOptionsResponse(BaseModel):
    """Response model for available filter options."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "categories": ["rag", "chatbot", "agent", "multi_agent"],
                    "frameworks": ["langchain", "llamaindex", "crewai"],
                    "providers": ["openai", "anthropic", "ollama"],
                    "complexities": ["beginner", "intermediate", "advanced"],
                }
            ]
        }
    )

    categories: list[str] = Field(default_factory=list)
    frameworks: list[str] = Field(default_factory=list)
    providers: list[str] = Field(default_factory=list)
    complexities: list[str] = Field(default_factory=list)


class AgentListResponse(BaseModel):
    """Response model for agent list endpoint."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "query": "rag",
                    "total": 42,
                    "page": 1,
                    "page_size": 20,
                    "items": [
                        {
                            "id": "pdf-chat-agent",
                            "name": "PDF Chat Agent",
                            "description": "Chat with your PDF documents",
                            "category": "rag",
                            "frameworks": ["langchain"],
                            "llm_providers": ["openai"],
                            "complexity": "beginner",
                            "github_url": "https://github.com/example/pdf-chat",
                            "stars": 1234,
                        }
                    ],
                }
            ]
        }
    )

    query: str = Field(description="Search query used")
    total: int = Field(description="Total matching agents")
    page: int = Field(description="Current page number")
    page_size: int = Field(description="Items per page")
    items: list[dict[str, Any]] = Field(default_factory=list, description="Agent results")


class AISelectResponse(BaseModel):
    """Response model for AI selection endpoint."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "cached": False,
                    "model": "claude-3-5-sonnet-20241022",
                    "text": "Based on your requirements, I recommend...",
                    "usage": {"input_tokens": 1500, "output_tokens": 800},
                    "cost_usd": 0.0045,
                }
            ]
        }
    )

    cached: bool = Field(description="Whether result was from cache")
    model: str = Field(description="Model used")
    text: str = Field(description="AI response text")
    usage: dict[str, int | None] | None = Field(None, description="Token usage")
    cost_usd: float = Field(description="Estimated cost in USD")


class WebManusRecommendation(BaseModel):
    """Single WebManus recommendation."""

    model_config = ConfigDict(extra="ignore")

    slug: str = Field(min_length=1, max_length=80)
    match_score: float = Field(ge=0.0, le=1.0)
    reason: str = Field(min_length=1, max_length=600)
    name: str | None = Field(default=None, max_length=120)
    tagline: str | None = Field(default=None, max_length=240)


class WebManusConsultResponse(BaseModel):
    """Response model for WebManus consultation."""

    model_config = ConfigDict(extra="ignore")

    recommendations: list[WebManusRecommendation] = Field(default_factory=list)
    no_match_suggestion: str = Field(default="", max_length=800)


class WorkerResponse(BaseModel):
    """Response model for a single worker."""

    model_config = ConfigDict(extra="allow")

    slug: str = Field(description="Unique worker identifier")
    name: str = Field(description="Worker name")
    tagline: str = Field(description="Worker tagline")
    description: str = Field(description="Worker description")
    capability: str = Field(description="Worker capability")
    pricing: str | None = Field(None, description="Pricing tier")
    score: float = Field(description="Relevance score")


class WorkerListResponse(BaseModel):
    """Response model for worker list endpoint."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "total": 15,
                    "items": [
                        {
                            "slug": "web-scraper",
                            "name": "Web Scraper",
                            "tagline": "Scrape any website",
                            "capability": "scraping",
                            "pricing": "free",
                            "score": 8.5,
                        }
                    ],
                }
            ]
        }
    )

    total: int = Field(description="Total matching workers")
    items: list[dict[str, Any]] = Field(default_factory=list, description="Worker results")


class CapabilityListResponse(BaseModel):
    """Response model for capabilities list endpoint."""

    model_config = ConfigDict(
        json_schema_extra={"examples": [["automation", "scraping", "analysis"]]}
    )

    capabilities: list[str] = Field(default_factory=list, description="Available capabilities")


class FavoriteResponse(BaseModel):
    """Response model for favorite operations."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"user_id": "user_123", "agent_id": "pdf-chat-agent", "is_favorite": True}
            ]
        }
    )

    user_id: str
    agent_id: str
    is_favorite: bool


class FavoriteListResponse(BaseModel):
    """Response model for favorites list."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"user_id": "user_123", "agent_ids": ["pdf-chat-agent", "csv-analyzer"]}
            ]
        }
    )

    user_id: str
    agent_ids: list[str] = Field(default_factory=list)


class HistoryItemResponse(BaseModel):
    """Single history item."""

    agent_id: str


class HistoryListResponse(BaseModel):
    """Response model for view history."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "user_id": "user_123",
                    "items": [{"agent_id": "pdf-chat-agent"}, {"agent_id": "csv-analyzer"}],
                }
            ]
        }
    )

    user_id: str
    items: list[HistoryItemResponse] = Field(default_factory=list)


class UserInfoResponse(BaseModel):
    """Response model for user info endpoint."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"user_id": "user_123", "is_anonymous": False},
                {"user_id": "anonymous:127.0.0.1", "is_anonymous": True},
            ]
        }
    )

    user_id: str
    is_anonymous: bool


class HistoryRecordResponse(BaseModel):
    """Response model for recording a view."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"user_id": "user_123", "agent_id": "pdf-chat-agent", "recorded": True}
            ]
        }
    )

    user_id: str
    agent_id: str
    recorded: bool


class ErrorResponse(BaseModel):
    """Standard error response."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"detail": "Agent not found"},
                {"detail": "rate_limited", "retry_after": 30},
                {"detail": "Missing ANTHROPIC_API_KEY"},
            ]
        }
    )

    detail: str
    error_code: str | None = Field(None, description="Machine-readable error code")
    retry_after: int | None = Field(None, description="Seconds before retry")
