# Architecture

## Agent contracts

### IntentAgent (`backend/app/agents/intent_agent.py`)
- **Input:** raw query string, optional lightweight context string
- **Output:** `Intent` — persona, use_case, budget_band, priority_specs (≤3), is_gift, confidence
- **Model:** Claude (`claude-sonnet-4-6`), JSON-only response
- **Fallback:** keyword-matched heuristic intent if the LLM call fails, so the pipeline never
  hard-fails on this step

### FilterAgent (`backend/app/agents/filter_agent.py`)
- **Input:** product list + priority specs
- **Output:** same list, annotated with `match_score` / `matched_specs`, sorted
- **Logic:** keyword-based fuzzy matching against each product's spec text (SerpAPI spec fields
  are inconsistent across listings, hence fuzzy rather than exact-key matching), ties broken by
  original SERP position — this preserves Amazon's own relevance signal rather than discarding it
  entirely, addressing the deck's "more options ≠ better" insight without throwing away existing
  ranking information

### TrustAgent (`backend/app/agents/trust_agent.py`)
- **Input:** single product + a sample of its reviews (from live SerpAPI product details)
- **Output:** `trust_score` (0-100), `kept_pct` (estimated proxy), badges
- **Logic:** weighted combination of rating (50%), review volume via log scaling (20%),
  verified-purchase ratio in the sample (30%)

### ComparisonAgent (`backend/app/agents/comparison_agent.py`)
- **Input:** top ~4 products (post-filter, post-trust) + priority specs
- **Output:** per-product plain-language highlights/tradeoffs
- **Model:** Claude, JSON-only, capped to a small candidate set to bound cost/latency
- **Fallback:** generic "matches N of your priority specs" text if LLM unavailable

### DecisionAgent (`backend/app/agents/decision_agent.py`)
- **Input:** `Intent` + top ~6 ranked/trust-scored candidates
- **Output:** ranked shortlist (≤3) with a persona-motivated one-line justification each
- **Model:** Claude, JSON-only
- **Fallback:** deterministic sort by trust_score/match_score if LLM unavailable

### Orchestrator (`backend/app/agents/orchestrator.py`)
Sequences the above, does the live SerpAPI calls (search, then product-detail enrichment capped
at `DETAIL_ENRICH_LIMIT=8` products), and assembles an `AgentTraceStep` list surfaced to the
frontend's trace panel — this is the "explainable re-ranking" idea from the brainstorm: every
re-rank is inspectable, not a black box, directly targeting the deck's "mistrust in platform"
pain point.

## Journey-phase mapping

| Journey phase (from deck's user journey table) | Agent(s) | Deck friction point addressed |
|---|---|---|
| Query entry | IntentAgent | "No personalization; ads clutter results" |
| SRP browsing | FilterAgent | "Too many similar-looking listings" |
| PDP comparison | ComparisonAgent | "Specs are hard to compare; UX inconsistency" |
| Trust check | TrustAgent | "Review overload, fake or unhelpful reviews" |
| Decision | DecisionAgent | "No 'safe bet' surfaced" |
| (Phase 2, not built) | FeedbackAgent | "Abandons cart or postpones" — closing the loop |

## Data flow / live integration

`GET /api/search?q=...` and `POST /api/refine` both run the full pipeline synchronously per
request (`orchestrator.run_search`). Two live external calls happen per pipeline run:
1. `serpapi_client.search_amazon` — Amazon Search engine, up to 3 pages
2. `serpapi_client.get_product_details` — Amazon Product engine, called concurrently
   (`asyncio.gather`) for the top `DETAIL_ENRICH_LIMIT` post-filter candidates only

Both are wrapped in short `TTLCache` instances to prevent redundant calls when a user toggles
spec chips rapidly within the same session — this is a request-debouncing cache, not a
pre-scraped dataset; cold queries always hit SerpAPI live.
