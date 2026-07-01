"""
Comparison Agent (hybrid)

Journey phase: PDP comparison / multi-tab compare.
Deck reference: "Add smart comparison layer; unify data view", jargon
complaint ("What is Enx Technology?").

The spec diffing itself is deterministic (just set operations over
matched_specs / raw spec dicts). The LLM is used only for the part that
actually needs language understanding: turning raw spec jargon into
plain-language highlights/tradeoffs a shopper can act on. Runs on the
top N shortlisted products only, not the full SERP, to keep LLM calls cheap.
"""
from __future__ import annotations

from app.core.llm_client import call_json
from app.core.schemas import ComparisonEntry, Product

SYSTEM_PROMPT = """You are the Comparison Agent for wireless earphones on Amazon India.
Given a small set of products (title + raw specs, which may contain jargon like "Enx Technology" or
"ADP true wireless") and the user's priority specs, produce plain-language highlights and tradeoffs
for each product a non-technical shopper can immediately understand.

Respond ONLY with a JSON array, one object per product, in the same order given:
[{"asin": string or null, "highlights": [string, string], "tradeoffs": [string]}]

Rules:
- highlights: max 2 short phrases, translate jargon into plain benefit language (e.g. "Enx Technology" ->
  "clearer calls in noisy environments")
- tradeoffs: max 1 short phrase, an honest limitation relative to the other products shown or to the user's stated priorities
- Do not invent specs that weren't provided. If data is missing, say "spec not listed" rather than guessing.
"""


async def run(products: list[Product], priority_specs: list[str]) -> list[ComparisonEntry]:
    if not products:
        return []

    payload_lines = []
    for p in products:
        spec_str = ", ".join(f"{k}: {v}" for k, v in p.specs.items()) or "no detailed specs available"
        payload_lines.append(f"- asin={p.asin}, title=\"{p.title}\", specs=[{spec_str}]")

    user_msg = (
        f"User priority specs: {priority_specs}\n\nProducts:\n" + "\n".join(payload_lines)
    )

    try:
        data = await call_json(SYSTEM_PROMPT, user_msg, max_tokens=800)
        if isinstance(data, dict) and "items" in data:
            data = data["items"]
    except Exception:
        return _fallback_comparison(products)

    entries: list[ComparisonEntry] = []
    for p, item in zip(products, data):
        entries.append(ComparisonEntry(
            asin=p.asin,
            title=p.title,
            highlights=item.get("highlights", [])[:2],
            tradeoffs=item.get("tradeoffs", [])[:1],
        ))
    return entries


def _fallback_comparison(products: list[Product]) -> list[ComparisonEntry]:
    return [
        ComparisonEntry(
            asin=p.asin,
            title=p.title,
            highlights=[f"Matches {len(p.matched_specs)} of your priority specs"],
            tradeoffs=["Detailed comparison unavailable (LLM offline)"],
        )
        for p in products
    ]
