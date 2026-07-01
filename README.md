# Amazon SERP Agent

An agentic SERP optimization system for **wireless earphones on Amazon.in**, built to address
choice overload across the *entire* buyer journey — not just re-rank a single results page.

Origin: this project operationalizes the problem framing and solution ideas from
["Reducing Choice Overload on Amazon" (Vir Jain, IIT Madras)](./docs/context.md) and the
`amazonchoice.lovable.app` prototype, rebuilt as a real hybrid agentic system with live data.

## Why "agentic," and why "hybrid"

Most choice-overload fixes (including the deck's own prototype) are a single re-rank pass after
the user picks filters. This system instead runs a **pipeline of agents**, each owning one phase
of the journey (query entry → browse → compare → trust-check → decide), coordinated by an
Orchestrator that produces a visible reasoning trace.

Ranking 40–60 SKUs through an LLM on every keystroke would be slow, expensive, and
non-reproducible — so the split is deliberate:

| Deterministic (fast, cheap, reproducible) | LLM-backed (needs real language understanding) |
|---|---|
| Spec matching & re-ranking (`FilterAgent`) | Query → structured intent (`IntentAgent`) |
| Trust scoring from ratings/reviews (`TrustAgent`) | Jargon → plain-language highlights (`ComparisonAgent`) |
| — | Persona-fit shortlist justification (`DecisionAgent`) |

## Live data, not a static dataset

Every search hits **SerpAPI's Amazon Search + Amazon Product engines** at request time (see
`backend/app/core/serpapi_client.py`), so prices, sponsored slots, and rank order reflect the
real current SERP — not a scraped-once snapshot. A short TTL cache (default 15 min) avoids
redundant calls within a session; it is not a persisted dataset.

## Architecture

```
User query
   │
   ▼
IntentAgent (LLM) ──► structured intent (persona, use-case, priority specs)
   │
   ▼
Live SerpAPI search (amazon.in, "wireless earphones")
   │
   ▼
FilterAgent (deterministic) ──► spec-match re-rank
   │
   ▼
Live SerpAPI product details (top-N only) + TrustAgent (deterministic) ──► trust score, kept-%
   │
   ▼
ComparisonAgent (LLM) ──► plain-language highlights/tradeoffs, top 4
   │
   ▼
DecisionAgent (LLM) ──► 2-3 item shortlist with persona-fit justification
   │
   ▼
SearchResponse (products + comparison + shortlist + full agent trace) → frontend
```

Full detail: [`docs/architecture.md`](./docs/architecture.md)

## Repo layout

```
backend/    FastAPI app, agents, SerpAPI + Anthropic clients, tests
frontend/   React + Vite SPA (SRP with spec chips, trust badges, shortlist, trace panel)
docs/       architecture notes, original deck context, roadmap
```

## Running locally

### Backend
```bash
cd backend
cp .env.example .env   # fill in SERPAPI_KEY and ANTHROPIC_API_KEY
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

Frontend dev server proxies `/api` to `localhost:8000` (see `vite.config.js`).

### Docker
```bash
docker compose up --build
```

## Tests

Deterministic agents (`FilterAgent`, `TrustAgent`) have unit tests with no network dependency:
```bash
cd backend && pytest tests/ -v
```
LLM- and SerpAPI-backed agents are not unit-tested with live calls (cost/flakiness); they have
defensive fallbacks (see `_fallback_*` functions in each agent) so the pipeline degrades
gracefully rather than hard-failing if either external API is unavailable.

## Known limitations / honesty about data provenance

- **`kept_pct` is an estimated proxy**, not real Amazon return-rate data — SerpAPI doesn't expose
  that. It's derived from rating + review-volume + verified-purchase signals and labeled "(est.)"
  everywhere it's surfaced. Do not present it as ground truth.
- **Persona inference is a heuristic**, not a verified user profile — it's meant to reduce the
  first-click burden (vs. the original prototype's manual spec-picker), not replace user control.
  The UI always lets the user override selected specs.
- Category scope is **wireless earphones only** (Phase 1). Generalizing to other categories would
  need per-category spec keyword maps (see `filter_agent.SPEC_KEYWORDS`).

## Roadmap (not yet built)

- **FeedbackAgent**: close the loop using post-purchase return/keep outcomes to retrain trust
  scoring weights — this is what would make the system actually learn over time, per the original
  brainstorm.
- Session persistence (currently stateless per request).
- Real returns-data integration if/when available, to replace the `kept_pct` proxy.
