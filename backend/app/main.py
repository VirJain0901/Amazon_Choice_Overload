from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import search

app = FastAPI(
    title="Amazon SERP Agent",
    description="Agentic SERP optimization for wireless earphones on Amazon.in — "
                 "hybrid deterministic + LLM agent pipeline across the buyer journey.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin, "http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search.router)


@app.get("/")
async def root():
    return {"service": "amazon-serp-agent", "status": "running", "docs": "/docs"}
