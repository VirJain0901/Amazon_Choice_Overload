from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.agents import filter_agent, orchestrator
from app.core.schemas import SearchResponse, SpecSelectionRequest

router = APIRouter(prefix="/api", tags=["search"])


@router.get("/search", response_model=SearchResponse)
async def search(
    q: str = Query(..., min_length=2, description="Search query, e.g. 'wireless earphones for gaming'"),
    context: str | None = Query(None, description="Optional lightweight context, e.g. 'recently bought a PS5'"),
):
    try:
        return await orchestrator.run_search(q, context=context)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Search pipeline failed: {e}") from e


@router.post("/refine", response_model=SearchResponse)
async def refine(payload: SpecSelectionRequest):
    """
    Re-runs the pipeline with explicit user-selected specs overriding the
    Intent Agent's inferred priority_specs -- this is the "Top 3 Specs"
    manual override flow from the deck, layered on top of the inferred
    default so users aren't forced to make the first move.
    """
    try:
        return await orchestrator.run_search(payload.query, override_specs=payload.selected_specs)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Refine pipeline failed: {e}") from e


@router.get("/health")
async def health():
    return {"status": "ok"}
