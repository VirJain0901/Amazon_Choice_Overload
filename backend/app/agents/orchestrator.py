"""
Orchestrator

Coordinates the agent pipeline for a single search request:

  IntentAgent -> [live SerpAPI search] -> FilterAgent -> [live SerpAPI product
  details for top-N] -> TrustAgent -> ComparisonAgent -> DecisionAgent

Every step appends an AgentTraceStep so the frontend can render a
transparent "why did you see this" panel (the deck's "mistrust in
platform" pain point is addressed here: showing the reasoning, not just
the result, per the explainable-re-ranking idea from the brainstorm).

Live-data note: both SerpAPI calls happen at request time (via
core/serpapi_client.py), not from a pre-scraped dataset. Product detail
enrichment is deliberately capped to the top N post-filter candidates to
keep latency and SerpAPI usage bounded -- fetching full specs for 40-60
SKUs on every keystroke isn't necessary or affordable.
"""
from __future__ import annotations

import asyncio

from app.agents import comparison_agent, decision_agent, filter_agent, intent_agent, trust_agent
from app.core import serpapi_client
from app.core.schemas import AgentTraceStep, Product, SearchResponse

DETAIL_ENRICH_LIMIT = 8  # how many top-ranked products get live spec+review enrichment


async def run_search(query: str, context: str | None = None, override_specs: list[str] | None = None) -> SearchResponse:
    trace: list[AgentTraceStep] = []

    # 1. Intent Agent
    intent = await intent_agent.run(query, context=context)
    trace.append(AgentTraceStep(
        agent="IntentAgent",
        summary=f"Inferred persona={intent.persona}, use_case={intent.use_case}, "
                f"priority_specs={intent.priority_specs}",
        data=intent.model_dump(),
    ))

    priority_specs = override_specs if override_specs else intent.priority_specs

    # 2. Live SERP search
    raw_products = await serpapi_client.search_amazon(query)
    products = [Product(**p) for p in raw_products if p.get("title")]
    trace.append(AgentTraceStep(
        agent="SerpAPI (live search)",
        summary=f"Fetched {len(products)} live listings for \"{query}\" from amazon.in",
    ))

    # 3. Filter Agent (deterministic re-rank)
    products = filter_agent.run(products, priority_specs)
    trace.append(AgentTraceStep(
        agent="FilterAgent",
        summary=f"Re-ranked by match against {priority_specs}",
        data={"top_asins": [p.asin for p in products[:5]]},
    ))

    # 4. Enrich top-N with live product details + trust scoring
    top_candidates = products[:DETAIL_ENRICH_LIMIT]
    detail_results = await asyncio.gather(
        *[_enrich(p) for p in top_candidates], return_exceptions=True
    )
    enriched = []
    for p, result in zip(top_candidates, detail_results):
        if isinstance(result, Exception):
            trace.append(AgentTraceStep(
                agent="SerpAPI (product details)",
                summary=f"Failed to enrich {p.asin}: {result}",
            ))
            enriched.append(trust_agent.run(p, []))
        else:
            enriched.append(result)
    trace.append(AgentTraceStep(
        agent="TrustAgent",
        summary=f"Scored {len(enriched)} products using rating/volume/verified-purchase signals",
    ))

    enriched_sorted = sorted(enriched, key=lambda p: (-(p.match_score or 0), -(p.trust_score or 0)))

    # 5. Comparison Agent (top few only)
    comparison = await comparison_agent.run(enriched_sorted[:4], priority_specs)
    trace.append(AgentTraceStep(
        agent="ComparisonAgent",
        summary=f"Generated plain-language comparison for top {len(comparison)} products",
    ))

    # 6. Decision Agent
    shortlist = await decision_agent.run(intent, enriched_sorted)
    trace.append(AgentTraceStep(
        agent="DecisionAgent",
        summary=f"Produced {len(shortlist)}-item shortlist for persona={intent.persona}",
    ))

    # merge enriched data back into the full product list for the SRP view
    enriched_by_asin = {p.asin: p for p in enriched_sorted}
    final_products = [enriched_by_asin.get(p.asin, p) for p in products]

    return SearchResponse(
        query=query,
        intent=intent,
        products=final_products,
        comparison=comparison,
        shortlist=shortlist,
        trace=trace,
    )


async def _enrich(product: Product) -> Product:
    if not product.asin:
        return trust_agent.run(product, [])
    details = await serpapi_client.get_product_details(product.asin)
    product.specs = details.get("specs", {})
    return trust_agent.run(product, details.get("reviews_sample", []))
