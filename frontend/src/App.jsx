import { useState } from "react";
import { search as apiSearch, refine as apiRefine } from "./lib/api";
import SpecPanel from "./components/SpecPanel";
import ProductCard from "./components/ProductCard";
import ShortlistPanel from "./components/ShortlistPanel";
import ComparisonPanel from "./components/ComparisonPanel";
import TracePanel from "./components/TracePanel";

export default function App() {
  const [query, setQuery] = useState("wireless earphones");
  const [result, setResult] = useState(null);
  const [selectedSpecs, setSelectedSpecs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function runSearch(q) {
    setLoading(true);
    setError(null);
    try {
      const data = await apiSearch(q);
      setResult(data);
      setSelectedSpecs(data.intent.priority_specs || []);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  async function toggleSpec(spec) {
    let next;
    if (selectedSpecs.includes(spec)) {
      next = selectedSpecs.filter((s) => s !== spec);
    } else if (selectedSpecs.length >= 3) {
      next = [...selectedSpecs.slice(1), spec];
    } else {
      next = [...selectedSpecs, spec];
    }
    setSelectedSpecs(next);

    setLoading(true);
    setError(null);
    try {
      const data = await apiRefine(query, next);
      setResult(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  function onSubmit(e) {
    e.preventDefault();
    runSearch(query);
  }

  return (
    <div>
      <div className="topbar">
        <div className="logo">amazon<span style={{ color: "#ff9900" }}>.in</span></div>
        <form className="searchbar" onSubmit={onSubmit}>
          <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search wireless earphones..." />
          <button type="submit">🔍</button>
        </form>
        <div style={{ fontSize: 12 }}>Agentic SERP Demo</div>
      </div>
      <div className="subbar">
        {result ? `1-${result.products.length} of live results for "${result.query}"` : "Search to begin"}
      </div>

      <div className="container">
        <div className="sidebar">
          <p style={{ fontSize: 13, color: "#565959" }}>
            This SERP is powered by a live agent pipeline (Intent → SerpAPI → Filter → Trust → Comparison → Decision),
            not a static dataset. Data is pulled from SerpAPI's Amazon India engine at request time.
          </p>
        </div>

        <div className="main">
          {error && <div className="error-box">{error}</div>}
          {loading && <div className="loading">Agents are working…</div>}

          {result && !loading && (
            <>
              <SpecPanel selected={selectedSpecs} onToggle={toggleSpec} inferred={result.intent.priority_specs} />
              <TracePanel trace={result.trace} />
              <ShortlistPanel shortlist={result.shortlist} persona={result.intent.persona} />
              <ComparisonPanel comparison={result.comparison} />
              {result.products.map((p) => (
                <ProductCard key={p.asin || p.position} product={p} />
              ))}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
