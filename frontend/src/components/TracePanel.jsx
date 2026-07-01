import { useState } from "react";

export default function TracePanel({ trace }) {
  const [open, setOpen] = useState(false);
  if (!trace || trace.length === 0) return null;

  return (
    <div>
      <span className="trace-toggle" onClick={() => setOpen(!open)}>
        {open ? "▾ Hide" : "▸ Show"} agent reasoning trace ({trace.length} steps)
      </span>
      {open && (
        <div className="trace-panel">
          {trace.map((step, i) => (
            <div className="trace-step" key={i}>
              <span className="trace-agent">{step.agent}</span>: {step.summary}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
