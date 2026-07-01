"""
Decision Agent (LLM-backed)

Journey phase: final decision / "Still Deciding?" assist.
Deck reference: JTBD framework (functional/emotional/social/financial jobs
per persona), "Still Deciding? Assist" chatbot idea, Confidence Meter.

Takes the top-ranked (by FilterAgent) + trust-scored (by TrustAgent)
products and produces a 2-3 item shortlist with a one-line justification
tied to the inferred persona's actual job-to-be-done, not a generic
"this is popular" statement. This is the agent that directly answers the
deck's stated problem: "customers don't want thousands of options, they
want clarity on the right option for them."
"""
from __future__ import annotations

from app.core.llm_client import call_json
from app.core.schemas import Intent, Product, ShortlistItem

SYSTEM_PROMPT = """You are the Decision Agent for wireless earphones on Amazon India. Your job is to help a
shopper who is overwhelmed by choice pick with confidence -- not to just repeat specs back at them.

Given the user's inferred persona + intent, and a short list of already-filtered, trust-scored candidate
products, select and rank the best 2-3 and justify each pick in ONE sentence tied to the persona's actual
motivation (not a generic "great product" line).

Persona motivations to draw on:
- rational_buyer: wants a quick, low-effort, reliable pick
- value_seeker: wants best long-term value for money, fears missing a better deal
- tech_enthusiast: wants cutting-edge specs, fears buying something already outdated
- gifter: wants a safe, well-liked choice with minimal personal research
- lifestyle_shopper: wants something that fits their aesthetic/personality, not generic
- unknown: default to rational_buyer framing but keep it neutral

Respond ONLY with a JSON array (max 3 items) in ranked order:
[{"asin": string or null, "rank": number, "justification": string (max ~25 words),
  "persona_fit": string (max ~10 words describing why this fits the inferred persona)}]

Only choose from the products given. Do not invent products.
"""


async def run(intent: Intent, candidates: list[Product]) -> list[ShortlistItem]:
    if not candidates:
        return []

    top = candidates[:6]  # keep the LLM's context small and cheap
    payload_lines = []
    for p in top:
        payload_lines.append(
            f"- asin={p.asin}, title=\"{p.title}\", price={p.price}, rating={p.rating}, "
            f"trust_score={p.trust_score}, kept_pct={p.kept_pct}, matched_specs={p.matched_specs}"
        )

    user_msg = (
        f"Persona: {intent.persona}\nUse case: {intent.use_case}\nBudget band: {intent.budget_band}\n"
        f"Is gift: {intent.is_gift}\n\nCandidates:\n" + "\n".join(payload_lines)
    )

    try:
        data = await call_json(SYSTEM_PROMPT, user_msg, max_tokens=600)
        if isinstance(data, dict) and "items" in data:
            data = data["items"]
    except Exception:
        return _fallback_shortlist(top)

    by_asin = {p.asin: p for p in top}
    items: list[ShortlistItem] = []
    for entry in data[:3]:
        product = by_asin.get(entry.get("asin"))
        if not product:
            continue
        items.append(ShortlistItem(
            product=product,
            rank=entry.get("rank", len(items) + 1),
            justification=entry.get("justification", ""),
            persona_fit=entry.get("persona_fit", ""),
        ))
    return items or _fallback_shortlist(top)


def _fallback_shortlist(candidates: list[Product]) -> list[ShortlistItem]:
    ranked = sorted(candidates, key=lambda p: (-(p.trust_score or 0), -(p.match_score or 0)))[:3]
    return [
        ShortlistItem(
            product=p,
            rank=i + 1,
            justification=f"High trust score ({p.trust_score}) and matches {len(p.matched_specs)} priority specs.",
            persona_fit="Deterministic fallback ranking (LLM offline).",
        )
        for i, p in enumerate(ranked)
    ]
