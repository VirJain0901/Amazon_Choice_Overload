import { LABELS } from "./SpecPanel";

export default function ProductCard({ product }) {
  const matchPct = product.match_score != null ? Math.round(product.match_score * 100) : null;

  return (
    <div className="product-card">
      <div className="product-thumb">
        {product.thumbnail_url ? (
          <img src={product.thumbnail_url} alt={product.title} style={{ maxWidth: "100%", maxHeight: "100%" }} />
        ) : (
          product.brand
        )}
      </div>
      <div className="product-info">
        {product.is_sponsored && <div className="sponsored-tag">Sponsored</div>}
        <p className="product-title">{product.title}</p>

        <div className="product-badges">
          {product.badges?.map((b) => (
            <span key={b} className={`badge${b.includes("Low") || b.includes("Limited") ? " warn" : ""}`}>
              {b}
            </span>
          ))}
        </div>

        {product.matched_specs?.length > 0 && (
          <div style={{ margin: "6px 0" }}>
            {product.matched_specs.map((s) => (
              <span key={s} className="matched-spec-tick">✓ {LABELS[s] || s}</span>
            ))}
          </div>
        )}

        {matchPct != null && (
          <div>
            <div className="match-score-bar">
              <div className="match-score-fill" style={{ width: `${matchPct}%` }} />
            </div>
            <span style={{ fontSize: 11, color: "#565959" }}>{matchPct}% match to your priorities</span>
          </div>
        )}

        <div style={{ fontSize: 13, margin: "4px 0" }}>
          ⭐ {product.rating ?? "—"} ({product.reviews_count?.toLocaleString?.() ?? "—"})
          {product.trust_score != null && (
            <span style={{ marginLeft: 10, color: "#067d62" }}>
              Trust score: {product.trust_score}/100
              {product.kept_pct != null && ` · ~${product.kept_pct}% kept (est.)`}
            </span>
          )}
        </div>

        <div className="product-price">
          ₹{product.price?.toLocaleString?.() ?? "—"}
          {product.original_price && <span className="strike">₹{product.original_price.toLocaleString()}</span>}
        </div>
      </div>
    </div>
  );
}
