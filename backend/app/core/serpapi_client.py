"""
Live SerpAPI integration.

This is intentionally NOT a one-time scrape-to-dataset script. Every search
request from the frontend triggers a real-time call (subject to a short TTL
cache) to SerpAPI's Amazon Search + Amazon Product engines, so the agent
pipeline always operates on live SERP state (price changes, sponsored slots,
rank shuffles, stock status).

Caching exists only to avoid redundant calls within the same short window
(e.g. a user adjusting spec filters shouldn't re-hit SerpAPI for the base
SERP each time) -- the cache TTL is short (default 15 min) and keyed by
query+page.
"""
from __future__ import annotations

import asyncio
import re
from typing import Any

import httpx
from cachetools import TTLCache

from app.core.config import settings

_search_cache: TTLCache = TTLCache(maxsize=256, ttl=settings.serpapi_cache_ttl)
_product_cache: TTLCache = TTLCache(maxsize=512, ttl=settings.serpapi_cache_ttl)

SERPAPI_BASE = "https://serpapi.com/search.json"


class SerpApiError(RuntimeError):
    pass


def _brand_from_title(title: str) -> str:
    known_brands = [
        "boAt", "Sony", "JBL", "Samsung", "OnePlus", "Noise", "Skullcandy",
        "ZEBRONICS", "realme", "Jabra", "Apple", "Bose", "Sennheiser",
        "pTron", "Mivi", "Boult",
    ]
    for b in known_brands:
        if b.lower() in title.lower():
            return b
    return title.split()[0] if title else "Unknown"


def _parse_price(raw: str | None) -> float | None:
    if not raw:
        return None
    digits = re.sub(r"[^\d.]", "", raw)
    try:
        return float(digits) if digits else None
    except ValueError:
        return None


async def _get(client: httpx.AsyncClient, params: dict[str, Any]) -> dict[str, Any]:
    params = {**params, "api_key": settings.serpapi_key}
    resp = await client.get(SERPAPI_BASE, params=params, timeout=20)
    if resp.status_code != 200:
        raise SerpApiError(f"SerpAPI returned {resp.status_code}: {resp.text[:300]}")
    data = resp.json()
    if "error" in data:
        raise SerpApiError(f"SerpAPI error: {data['error']}")
    return data


async def search_amazon(query: str, max_pages: int | None = None) -> list[dict[str, Any]]:
    """
    Live Amazon SERP search via SerpAPI (engine=amazon). Returns a normalized
    list of product dicts. Cached briefly per (query, max_pages).
    """
    max_pages = max_pages or settings.serpapi_max_pages
    cache_key = (query, max_pages)
    if cache_key in _search_cache:
        return _search_cache[cache_key]

    if not settings.serpapi_key:
        raise SerpApiError(
            "SERPAPI_KEY is not configured. Set it in backend/.env (see .env.example)."
        )

    products: list[dict[str, Any]] = []
    async with httpx.AsyncClient() as client:
        page_token: str | None = None
        for page_num in range(max_pages):
            params = {
                "engine": "amazon",
                "amazon_domain": settings.amazon_domain,
                "k": query,
            }
            if page_token:
                params["page"] = page_token
            data = await _get(client, params)
            results = data.get("organic_results", [])
            for pos, item in enumerate(results, start=1):
                title = item.get("title", "")
                products.append({
                    "asin": item.get("asin"),
                    "title": title,
                    "brand": _brand_from_title(title),
                    "price": _parse_price(item.get("extracted_price") and str(item["extracted_price"])
                                            or (item.get("price") or {}).get("raw")
                                            if isinstance(item.get("price"), dict) else item.get("price")),
                    "original_price": _parse_price(
                        (item.get("old_price") or {}).get("raw") if isinstance(item.get("old_price"), dict)
                        else item.get("old_price")
                    ),
                    "rating": item.get("rating"),
                    "reviews_count": item.get("reviews") or item.get("ratings_total"),
                    "thumbnail_url": item.get("thumbnail"),
                    "is_prime": bool(item.get("prime")),
                    "is_sponsored": bool(item.get("sponsored")),
                    "position": pos + (page_num * len(results)),
                    "delivery_info": item.get("delivery"),
                    "bought_past_month": item.get("bought_past_month"),
                    "link": item.get("link"),
                })
            page_token = data.get("serpapi_pagination", {}).get("next_page_token")
            if not page_token:
                break

    _search_cache[cache_key] = products
    return products


async def get_product_details(asin: str) -> dict[str, Any]:
    """
    Live product detail + spec pull via SerpAPI (engine=amazon_product),
    cached briefly per ASIN.
    """
    if asin in _product_cache:
        return _product_cache[asin]

    if not settings.serpapi_key:
        raise SerpApiError("SERPAPI_KEY is not configured.")

    async with httpx.AsyncClient() as client:
        data = await _get(client, {
            "engine": "amazon_product",
            "amazon_domain": settings.amazon_domain,
            "asin": asin,
        })

    product = data.get("product_result", {})
    specs_raw = product.get("specifications", []) or product.get("feature_bullets", [])
    specs = _extract_specs(specs_raw, product)

    reviews = data.get("reviews_results", {}).get("reviews", [])

    result = {
        "asin": asin,
        "specs": specs,
        "feature_bullets": product.get("feature_bullets", []),
        "reviews_sample": [
            {
                "rating": r.get("rating"),
                "title": r.get("title"),
                "body": r.get("body"),
                "verified_purchase": r.get("verified_purchase", False),
                "date": r.get("date"),
            }
            for r in reviews[:15]
        ],
        "returns_signal": product.get("return_policy"),
    }
    _product_cache[asin] = result
    return result


def _extract_specs(specs_raw: Any, product: dict[str, Any]) -> dict[str, str]:
    """Normalize SerpAPI's inconsistent spec formats into a flat dict."""
    specs: dict[str, str] = {}
    if isinstance(specs_raw, list):
        for entry in specs_raw:
            if isinstance(entry, dict) and "name" in entry and "value" in entry:
                specs[entry["name"]] = entry["value"]
            elif isinstance(entry, str):
                # feature bullets aren't key/value; keep as free text bucket
                specs.setdefault("_features", "")
                specs["_features"] += entry + " | "
    elif isinstance(specs_raw, dict):
        specs.update({k: str(v) for k, v in specs_raw.items()})

    for key in ("battery_life", "driver_size", "bluetooth_version", "weight", "warranty"):
        if key in product:
            specs[key] = str(product[key])

    return specs
