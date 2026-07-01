from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class Product(BaseModel):
    asin: str | None = None
    title: str
    brand: str
    price: float | None = None
    original_price: float | None = None
    rating: float | None = None
    reviews_count: int | None = None
    thumbnail_url: str | None = None
    is_prime: bool = False
    is_sponsored: bool = False
    position: int
    delivery_info: str | None = None
    bought_past_month: str | None = None
    link: str | None = None

    # enriched fields, filled in by later agents
    specs: dict[str, str] = Field(default_factory=dict)
    trust_score: float | None = None
    kept_pct: float | None = None
    match_score: float | None = None
    matched_specs: list[str] = Field(default_factory=list)
    badges: list[str] = Field(default_factory=list)


class Intent(BaseModel):
    raw_query: str
    use_case: str | None = None            # e.g. "gaming", "office calls", "gym"
    persona: Literal[
        "rational_buyer", "value_seeker", "tech_enthusiast", "gifter", "lifestyle_shopper", "unknown"
    ] = "unknown"
    budget_band: Literal["under_1000", "1000_3000", "3000_8000", "8000_plus", "unspecified"] = "unspecified"
    priority_specs: list[str] = Field(default_factory=list)
    is_gift: bool = False
    confidence: float = 0.5
    reasoning: str = ""


class ComparisonEntry(BaseModel):
    asin: str | None
    title: str
    highlights: list[str]
    tradeoffs: list[str]


class TrustSummary(BaseModel):
    asin: str | None
    trust_score: float
    kept_pct: float | None
    sentiment_summary: str
    flags: list[str] = Field(default_factory=list)


class ShortlistItem(BaseModel):
    product: Product
    rank: int
    justification: str
    persona_fit: str


class AgentTraceStep(BaseModel):
    agent: str
    summary: str
    data: dict[str, Any] = Field(default_factory=dict)


class SearchResponse(BaseModel):
    query: str
    intent: Intent
    products: list[Product]
    comparison: list[ComparisonEntry] = Field(default_factory=list)
    shortlist: list[ShortlistItem] = Field(default_factory=list)
    trace: list[AgentTraceStep] = Field(default_factory=list)


class SpecSelectionRequest(BaseModel):
    query: str
    selected_specs: list[str]
    asins_in_view: list[str] = Field(default_factory=list)
