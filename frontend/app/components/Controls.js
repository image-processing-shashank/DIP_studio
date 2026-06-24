"use client";

// Renders sliders and selects driven entirely by the operation's param metadata.
export default function Controls({ params, values, onChange }) {
  if (!params || params.length === 0) {
    return <p className="muted">This operation has no parameters.</p>;
  }
  return (
    <div className="controls">
      {params.map((p) => {
        const val = values[p.name];
        if (p.type === "select") {
          return (
            <div className="ctrl-row" key={p.name}>
              <label>{p.label}</label>
              <select
                value={val}
                onChange={(e) => onChange(p.name, e.target.value)}
              >
                {(p.options || []).map((o) => (
                  <option key={String(o)} value={o}>
                    {String(o)}
                  </option>
                ))}
              </select>
            </div>
          );
        }
        // slider
        return (
          <div className="ctrl-row" key={p.name}>
            <label>{p.label}</label>
            <input
              type="range"
              min={p.min}
              max={p.max}
              step={p.step || 1}
              value={val}
              onChange={(e) => onChange(p.name, Number(e.target.value))}
            />
            <span className="ctrl-val">{val}</span>
          </div>
        );
      })}
    </div>
  );
}
