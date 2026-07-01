export default function ShortlistPanel({ shortlist, persona }) {
  if (!shortlist || shortlist.length === 0) return null;

  return (
    <div className="shortlist">
      <h3>🎯 Your Best Matches {persona && persona !== "unknown" ? `(for a ${persona.replace("_", " ")})` : ""}</h3>
      {shortlist.map((item) => (
        <div className="shortlist-item" key={item.product.asin || item.rank}>
          <div className="shortlist-rank">{item.rank}</div>
          <div className="product-thumb" style={{ width: 60, height: 60, fontSize: 10 }}>
            {item.product.thumbnail_url ? (
              <img src={item.product.thumbnail_url} alt="" style={{ maxWidth: "100%", maxHeight: "100%" }} />
            ) : (
              item.product.brand
            )}
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ fontWeight: 600, fontSize: 13 }}>{item.product.title}</div>
            <div className="shortlist-justification">{item.justification}</div>
            <div className="shortlist-persona">{item.persona_fit}</div>
          </div>
          <div style={{ fontWeight: 700 }}>₹{item.product.price?.toLocaleString?.() ?? "—"}</div>
        </div>
      ))}
    </div>
  );
}
