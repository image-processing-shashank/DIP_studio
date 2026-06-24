"use client";

// Modal that explains an operation and the maths involved.
export default function InfoModal({ op, onClose }) {
  if (!op) return null;
  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-head">
          <h3>{op.name}</h3>
          <button className="modal-close" onClick={onClose} aria-label="Close">×</button>
        </div>
        <p className="muted">{op.project}</p>
        <p>{op.description}</p>
        {op.math ? (
          <>
            <div className="modal-label">Maths involved</div>
            <pre className="math">{op.math}</pre>
          </>
        ) : null}
        {op.params && op.params.length ? (
          <>
            <div className="modal-label">Parameters</div>
            <ul className="param-help">
              {op.params.map((p) => (
                <li key={p.name}>
                  <strong>{p.label}</strong>
                  {p.type === "slider" && p.min != null
                    ? ` (range ${p.min} to ${p.max})`
                    : p.type === "select"
                    ? ` (${(p.options || []).join(", ")})`
                    : ""}
                  {p.help ? ` — ${p.help}` : ""}
                </li>
              ))}
            </ul>
          </>
        ) : null}
      </div>
    </div>
  );
}
