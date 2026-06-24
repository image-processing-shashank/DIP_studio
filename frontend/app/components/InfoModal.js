"use client";

import { useEffect } from "react";

export default function InfoModal({ op, onClose }) {
  useEffect(() => {
    if (!op) return;
    const onKey = (e) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [op, onClose]);

  if (!op) return null;
  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-head">
          <h3>{op.name}</h3>
          <button className="modal-close" onClick={onClose} aria-label="Close">×</button>
        </div>
        <span className="modal-project">{op.project}</span>
        <p className="modal-desc">{op.description}</p>

        {op.math && (
          <>
            <div className="modal-section-label">Maths involved</div>
            <pre className="math">{op.math}</pre>
          </>
        )}

        {op.params && op.params.length > 0 && (
          <>
            <div className="modal-section-label">Parameters</div>
            <ul className="param-list">
              {op.params.map((p) => (
                <li className="param-item" key={p.name}>
                  <span className="param-name">{p.label}</span>
                  {p.type === "slider" && p.min != null && (
                    <span className="param-range">{p.min} – {p.max} · step {p.step}</span>
                  )}
                  {p.type === "select" && (
                    <span className="param-range">{(p.options || []).join(" / ")}</span>
                  )}
                  {p.help && <span className="param-help">{p.help}</span>}
                </li>
              ))}
            </ul>
          </>
        )}
      </div>
    </div>
  );
}
