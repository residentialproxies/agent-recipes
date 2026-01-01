"""
Pydantic models for API requests and responses.
"""

from __future__ import annotations

from typing import List, Optional, Union

from pydantic import BaseModel, Field
from pydantic.config import ConfigDict


class SearchRequest(BaseModel):
    q: str = ""
    category: Optional[Union[List[str], str]] = None
    framework: Optional[Union[List[str], str]] = None
    provider: Optional[Union[List[str], str]] = None
    complexity: Optional[Union[List[str], str]] = None
    local_only: bool = False
    sort: Optional[str] = Field(default=None, max_length=40)
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class AISelectRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    max_candidates: int = Field(default=80, ge=10, le=120)
    category: Optional[Union[List[str], str]] = None
    framework: Optional[Union[List[str], str]] = None
    provider: Optional[Union[List[str], str]] = None
    complexity: Optional[Union[List[str], str]] = None
    local_only: bool = False


class WebManusConsultRequest(BaseModel):
    problem: str = Field(min_length=1, max_length=2000)
    max_candidates: int = Field(default=50, ge=10, le=120)
    capability: Optional[str] = Field(default=None, max_length=80)
    pricing: Optional[str] = Field(default=None, max_length=40)
    min_score: float = Field(default=0.0, ge=0.0, le=10.0)


class WebManusRecommendation(BaseModel):
    model_config = ConfigDict(extra="ignore")

    slug: str = Field(min_length=1, max_length=80)
    match_score: float = Field(ge=0.0, le=1.0)
    reason: str = Field(min_length=1, max_length=600)
    name: Optional[str] = Field(default=None, max_length=120)
    tagline: Optional[str] = Field(default=None, max_length=240)


class WebManusConsultResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    recommendations: List[WebManusRecommendation] = Field(default_factory=list)
    no_match_suggestion: str = Field(default="", max_length=800)
