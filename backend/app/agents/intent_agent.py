"""
Intent Agent (LLM-backed)

Journey phase: query entry.
Deck reference: "Detect user intent early using search context" (opportunity
identified in the Traditional User Journey table).

Takes the raw query (+ optional lightweight signals like past purchases)
and produces structured Intent: use-case, likely persona, budget band,
and a starter set of priority specs. This replaces the deck's "ask the
user to manually pick 3 specs" step with an inferred starting point --
the user can still override it (handled by FilterAgent).
"""
from __future__ import annotations

from app.core.llm_client import call_json
from app.core.schemas import Intent

SYSTEM_PROMPT = """You are the Intent Agent in an e-commerce search system for wireless earphones on Amazon India.
Given a user's raw search query (and optional context like recent purchases), infer their shopping intent.

Respond ONLY with a JSON object matching this schema, no other text:
{
  "use_case": string or null,          // e.g. "gaming", "office calls", "workout", "commute", "gifting"
  "persona": one of ["rational_buyer", "value_seeker", "tech_enthusiast", "gifter", "lifestyle_shopper", "unknown"],
  "budget_band": one of ["under_1000", "1000_3000", "3000_8000", "8000_plus", "unspecified"],
  "priority_specs": array of up to 3 strings from: ["battery_life", "noise_cancellation", "bass_quality",
      "comfort", "latency", "call_quality", "water_resistance", "build_quality", "price", "brand_trust"],
  "is_gift": boolean,
  "confidence": number 0-1,
  "reasoning": short string explaining the inference
}

Be conservative: if the query is generic ("wireless earphones") with no other context, use "unknown" persona,
"unspecified" budget, and priority_specs based only on what a typical buyer of this category cares about
(battery_life, comfort, price are safe defaults). Do not hallucinate context the user didn't give you.
"""


async def run(query: str, context: str | None = None) -> Intent:
    user_msg = f'Query: "{query}"'
    if context:
        user_msg += f"\nAdditional context: {context}"

    try:
        data = await call_json(SYSTEM_PROMPT, user_msg, max_tokens=400)
    except Exception:
        # Deterministic fallback so the pipeline never hard-fails on LLM issues
        return _fallback_intent(query)

    return Intent(
        raw_query=query,
        use_case=data.get("use_case"),
        persona=data.get("persona", "unknown"),
        budget_band=data.get("budget_band", "unspecified"),
        priority_specs=data.get("priority_specs", [])[:3],
        is_gift=bool(data.get("is_gift", False)),
        confidence=float(data.get("confidence", 0.5)),
        reasoning=data.get("reasoning", ""),
    )


def _fallback_intent(query: str) -> Intent:
    q = query.lower()
    use_case = None
    for kw, uc in [("gaming", "gaming"), ("gym", "workout"), ("workout", "workout"),
                   ("office", "office calls"), ("gift", "gifting")]:
        if kw in q:
            use_case = uc
            break
    return Intent(
        raw_query=query,
        use_case=use_case,
        persona="unknown",
        budget_band="unspecified",
        priority_specs=["battery_life", "comfort", "price"],
        is_gift="gift" in q,
        confidence=0.2,
        reasoning="LLM unavailable; used keyword-based fallback.",
    )
