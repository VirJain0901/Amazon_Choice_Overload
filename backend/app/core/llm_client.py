"""
Thin wrapper around the Anthropic API, used only by the three agents that
genuinely need natural-language understanding or generation:
IntentAgent, ComparisonAgent (explanations), DecisionAgent (justification).

Everything else in this system (filtering, trust scoring, ranking math) is
deterministic Python -- we do not put an LLM in the hot path of scoring
40-60 SKUs. This is the "hybrid" split the system was designed around.
"""
from __future__ import annotations

import json
from typing import Any

from anthropic import AsyncAnthropic

from app.core.config import settings

_client: AsyncAnthropic | None = None


def get_client() -> AsyncAnthropic:
    global _client
    if _client is None:
        if not settings.anthropic_api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is not configured (see backend/.env.example).")
        _client = AsyncAnthropic(api_key=settings.anthropic_api_key)
    return _client


async def call_json(system: str, user: str, max_tokens: int = 1024) -> dict[str, Any]:
    """Call Claude and expect a JSON object back. Strips markdown fences defensively."""
    client = get_client()
    resp = await client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    text = "".join(block.text for block in resp.content if block.type == "text")
    cleaned = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(f"LLM did not return valid JSON: {text[:300]}") from e
