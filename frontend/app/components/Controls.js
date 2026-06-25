"use client";

import { useEffect, useRef, useState } from "react";

// Small click popover anchored to a parameter's info button.
function ParamInfo({ param }) {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    if (!open) return;
    const onClick = (e) => { if (ref.current && !ref.current.contains(e.target)) setOpen(false); };
    const onKey = (e) => e.key === "Escape" && setOpen(false);
    document.addEventListener("mousedown", onClick);
    document.addEventListener("keydown", onKey);
    return () => { document.removeEventListener("mousedown", onClick); document.removeEventListener("keydown", onKey); };
  }, [open]);

  const range =
    param.type === "slider"
      ? `Range ${param.min} to ${param.max}, step ${param.step}. Default ${param.default}.`
      : param.type === "select"
      ? `Options: ${(param.options || []).join(", ")}. Default ${param.default}.`
      : "";

  return (
    <span className="param-info-wrap" ref={ref}>
      <button
        type="button"
        className="ctrl-q"
        aria-label={`About ${param.label}`}
        onClick={() => setOpen((v) => !v)}
      >i</button>
      {open && (
        <span className="param-pop" role="tooltip">
          <span className="param-pop-title">{param.label}</span>
          {param.help && <span className="param-pop-help">{param.help}</span>}
          <span className="param-pop-range">{range}</span>
        </span>
      )}
    </span>
  );
}

export default function Controls({ params, values, onChange, onReset }) {
  if (!params || params.length === 0) {
    return <p className="no-params">This operation runs directly with no adjustable parameters.</p>;
  }

  const isDefault = params.every((p) => String(values[p.name]) === String(p.default));

  return (
    <div className="controls">
      <div className="controls-head">
        <span className="controls-title">Parameters</span>
        <button className="reset-btn" onClick={onReset} disabled={isDefault} style={{ opacity: isDefault ? 0.4 : 1 }}>
          Reset
        </button>
      </div>

      {params.map((p) => {
        const val = values[p.name];

        const label = (
          <span className="ctrl-label">
            {p.label}
            <ParamInfo param={p} />
          </span>
        );

        if (p.type === "select") {
          const opts = p.options || [];
          if (opts.length <= 4) {
            return (
              <div className="ctrl-row" key={p.name}>
                {label}
                <div className="seg">
                  {opts.map((o) => (
                    <button
                      key={String(o)}
                      className={String(val) === String(o) ? "on" : ""}
                      onClick={() => onChange(p.name, o)}
                    >
                      {String(o)}
                    </button>
                  ))}
                </div>
              </div>
            );
          }
          return (
            <div className="ctrl-row" key={p.name}>
              {label}
              <select value={val} onChange={(e) => onChange(p.name, e.target.value)}>
                {opts.map((o) => (
                  <option key={String(o)} value={o}>{String(o)}</option>
                ))}
              </select>
            </div>
          );
        }

        // slider
        const dp = p.step < 0.01 ? 3 : p.step < 1 ? 2 : 0;
        const display = Number(val).toFixed(dp);
        return (
          <div className="ctrl-row" key={p.name}>
            {label}
            <div className="slider-wrap">
              <input
                type="range"
                min={p.min}
                max={p.max}
                step={p.step || 1}
                value={val}
                onChange={(e) => onChange(p.name, Number(e.target.value))}
              />
              <span className="ctrl-val">{display}</span>
            </div>
          </div>
        );
      })}
    </div>
  );
}
