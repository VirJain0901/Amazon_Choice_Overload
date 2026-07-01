const BASE = "/api";

async function handle(resp) {
  if (!resp.ok) {
    const body = await resp.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed: ${resp.status}`);
  }
  return resp.json();
}

export async function search(query, context) {
  const params = new URLSearchParams({ q: query });
  if (context) params.set("context", context);
  const resp = await fetch(`${BASE}/search?${params.toString()}`);
  return handle(resp);
}

export async function refine(query, selectedSpecs, asinsInView) {
  const resp = await fetch(`${BASE}/refine`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      query,
      selected_specs: selectedSpecs,
      asins_in_view: asinsInView || [],
    }),
  });
  return handle(resp);
}
