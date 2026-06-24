"use client";

// Renders sliders, selects, and segmented controls from param metadata.
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

        if (p.type === "select") {
          // Use a segmented control for 2-4 options, dropdown for more.
          const opts = p.options || [];
          if (opts.length <= 4) {
            return (
              <div className="ctrl-row" key={p.name}>
                <span className="ctrl-label">
                  {p.label}
                  {p.help && <span className="ctrl-q" title={p.help}>i</span>}
                </span>
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
              <span className="ctrl-label">
                {p.label}
                {p.help && <span className="ctrl-q" title={p.help}>i</span>}
              </span>
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
            <span className="ctrl-label">
              {p.label}
              {p.help && <span className="ctrl-q" title={p.help}>i</span>}
            </span>
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
