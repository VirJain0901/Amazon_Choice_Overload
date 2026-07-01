"""
Trust Agent (deterministic)

Journey phase: trust-check (before add-to-cart).
Deck reference: "Most Returned vs. Most Kept Label", "Review Validator",
Airbnb case study ("users rely on summarized trust indicators, not 500
raw reviews").

Computes a 0-100 trust_score per product from signals actually available
via SerpAPI (rating, review volume, verified-purchase ratio in the review
sample) rather than an LLM guessing at trustworthiness. A "kept_pct" proxy
is derived since SerpAPI doesn't expose Amazon's internal return-rate data
directly -- documented clearly as a proxy, not fabricated as real return data.
"""
from __future__ import annotations

from app.core.schemas import Product

RATING_WEIGHT = 0.5
VOLUME_WEIGHT = 0.2
VERIFIED_WEIGHT = 0.3


def _volume_score(reviews_count: int | None) -> float:
    if not reviews_count:
        return 0.0
    # log-ish scaling: 100 reviews -> ~0.5, 10k+ -> ~1.0
    import math
    return min(1.0, math.log10(max(reviews_count, 1) + 1) / 4.0)


def run(product: Product, review_sample: list[dict] | None = None) -> Product:
    review_sample = review_sample or []

    rating_score = (product.rating or 0) / 5.0
    volume_score = _volume_score(product.reviews_count)

    if review_sample:
        verified_ratio = sum(1 for r in review_sample if r.get("verified_purchase")) / len(review_sample)
    else:
        verified_ratio = 0.5  # neutral prior when no sample available

    trust_score = round(
        100 * (RATING_WEIGHT * rating_score + VOLUME_WEIGHT * volume_score + VERIFIED_WEIGHT * verified_ratio),
        1,
    )

    # Proxy "kept" percentage -- derived from rating+verified signal, NOT real
    # return-rate data (Amazon/SerpAPI doesn't expose that). Clearly labeled
    # as an estimate in the API response and frontend, per the system's
    # honesty-about-data-provenance principle.
    kept_pct = round(min(99.0, 60 + trust_score * 0.35), 1)

    product.trust_score = trust_score
    product.kept_pct = kept_pct

    badges = []
    if trust_score >= 80:
        badges.append("Highly Trusted")
    if kept_pct >= 90:
        badges.append("Most Kept (est.)")
    if (product.reviews_count or 0) < 50:
        badges.append("Limited Review Data")
    if verified_ratio < 0.3 and review_sample:
        badges.append("Low Verified-Purchase Ratio")
    product.badges = list(dict.fromkeys(product.badges + badges))

    return product
