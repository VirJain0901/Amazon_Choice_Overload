export default function ComparisonPanel({ comparison }) {
  if (!comparison || comparison.length === 0) return null;

  return (
    <div className="comparison-panel">
      <h3 style={{ marginTop: 0, fontSize: 16 }}>🔍 Plain-Language Comparison</h3>
      <div className="comparison-grid">
        {comparison.map((c) => (
          <div className="comparison-card" key={c.asin || c.title}>
            <h5>{c.title}</h5>
            {c.highlights.map((h, i) => (
              <div className="highlight" key={i}>+ {h}</div>
            ))}
            {c.tradeoffs.map((t, i) => (
              <div className="tradeoff" key={i}>− {t}</div>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}
