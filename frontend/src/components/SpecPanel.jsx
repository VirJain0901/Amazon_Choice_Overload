const ALL_SPECS = [
  "battery_life", "noise_cancellation", "bass_quality", "comfort",
  "latency", "call_quality", "water_resistance", "build_quality", "brand_trust", "price",
];

const LABELS = {
  battery_life: "Battery Life",
  noise_cancellation: "Noise Cancelling",
  bass_quality: "Bass / Sound",
  comfort: "Comfort",
  latency: "Low Latency",
  call_quality: "Call Quality",
  water_resistance: "Water Resistant",
  build_quality: "Build Quality",
  brand_trust: "Trusted Brand",
  price: "Best Price",
};

export default function SpecPanel({ selected, onToggle, inferred }) {
  return (
    <div className="spec-panel">
      <h4>
        What matters most to you? Pick up to 3 specs — products re-rank instantly.
        {inferred && inferred.length > 0 && (
          <span style={{ fontWeight: 400, fontSize: 12, marginLeft: 8, color: "#565959" }}>
            (auto-suggested from your search: {inferred.map((s) => LABELS[s] || s).join(", ")})
          </span>
        )}
      </h4>
      {ALL_SPECS.map((spec) => (
        <span
          key={spec}
          className={`spec-chip${selected.includes(spec) ? " selected" : ""}`}
          onClick={() => onToggle(spec)}
        >
          {LABELS[spec] || spec}
        </span>
      ))}
    </div>
  );
}

export { LABELS };
