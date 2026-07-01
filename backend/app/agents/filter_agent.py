"""
Filter Agent (deterministic)

Journey phase: SRP browsing.
Deck reference: "Top 3 Specs Prioritization" solution -- dynamic re-ranking
based on chosen/inferred specs, with visual match highlighting.

Pure scoring code, no LLM. Given the priority specs (from IntentAgent or
explicit user selection) and each product's spec dict (from SerpAPI product
details, fetched live), computes a match_score and matched_specs list, then
re-sorts. Deliberately deterministic: ranking 40-60 SKUs through an LLM
would be slow, expensive, and non-reproducible.
"""
from __future__ import annotations

from app.core.schemas import Product

# Maps our canonical spec names to keyword patterns we look for in the
# free-text spec fields SerpAPI returns (specs are inconsistent across
# listings, so this is intentionally fuzzy).
SPEC_KEYWORDS: dict[str, list[str]] = {
    "battery_life": ["battery", "playback", "hours", "hrs"],
    "noise_cancellation": ["noise cancel", "anc", "enc"],
    "bass_quality": ["bass", "driver", "sound"],
    "comfort": ["comfort", "lightweight", "ergonomic", "in-ear", "over-ear"],
    "latency": ["latency", "low latency", "gaming mode"],
    "call_quality": ["mic", "call", "enc"],
    "water_resistance": ["ipx", "water", "sweat", "splash"],
    "build_quality": ["build", "durable", "warranty"],
    "brand_trust": [],  # handled via brand allowlist, not keyword
}

TRUSTED_BRANDS = {"Sony", "boAt", "JBL", "Samsung", "OnePlus", "Jabra", "Apple", "Bose", "Sennheiser"}


def _spec_hit(product: Product, canonical_spec: str) -> bool:
    if canonical_spec == "brand_trust":
        return product.brand in TRUSTED_BRANDS
    if canonical_spec == "price":
        return product.price is not None

    haystack = " ".join(
        [product.title.lower()] +
        [f"{k} {v}".lower() for k, v in product.specs.items()]
    )
    keywords = SPEC_KEYWORDS.get(canonical_spec, [])
    return any(kw in haystack for kw in keywords)


def run(products: list[Product], priority_specs: list[str]) -> list[Product]:
    """Scores + re-ranks products by how many priority specs they match.
    Mutates and returns the list, sorted descending by match_score, with
    ties broken by original SERP position (respects Amazon's baseline
    relevance signal rather than discarding it)."""
    if not priority_specs:
        return sorted(products, key=lambda p: p.position)

    for product in products:
        matched = [s for s in priority_specs if _spec_hit(product, s)]
        product.matched_specs = matched
        product.match_score = round(len(matched) / len(priority_specs), 3)

    return sorted(products, key=lambda p: (-p.match_score, p.position))
