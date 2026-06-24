"use client";

import { useEffect, useRef } from "react";

function Histogram({ data, color }) {
  const ref = useRef(null);
  useEffect(() => {
    const c = ref.current;
    if (!c || !data) return;
    const ctx = c.getContext("2d");
    c.width = 256;
    c.height = 80;
    ctx.clearRect(0, 0, 256, 80);
    const max = Math.max(...data) || 1;
    ctx.fillStyle = color;
    for (let x = 0; x < 256; x++) {
      const h = Math.round((data[x] / max) * 76);
      ctx.fillRect(x, 80 - h, 1, h);
    }
  }, [data, color]);
  return <canvas ref={ref} className="hist-canvas" />;
}

export default function ResultView({ result }) {
  if (!result) return null;
  const m = result.metrics || {};
  const hasHist = m.hist_gray;

  return (
    <div className="result">
      <div className="img-grid">
        {result.images.map((im, i) => (
          <figure key={i} className="img-card">
            <img src={im.data} alt={im.label} />
            <figcaption>{im.label}</figcaption>
          </figure>
        ))}
      </div>

      {Object.keys(m).length > 0 && (
        <div className="metrics">
          {Object.entries(m)
            .filter(([k]) => !k.startsWith("hist_"))
            .map(([k, v]) => (
              <div className="metric" key={k}>
                <span className="metric-k">{k}</span>
                <span className="metric-v">
                  {typeof v === "object" ? JSON.stringify(v) : String(v)}
                </span>
              </div>
            ))}
        </div>
      )}

      {hasHist && (
        <div className="hist-row">
          <div>
            <div className="muted">Grayscale</div>
            <Histogram data={m.hist_gray} color="#444" />
          </div>
          <div>
            <div className="muted">Red</div>
            <Histogram data={m.hist_r} color="#c0392b" />
          </div>
          <div>
            <div className="muted">Green</div>
            <Histogram data={m.hist_g} color="#27ae60" />
          </div>
          <div>
            <div className="muted">Blue</div>
            <Histogram data={m.hist_b} color="#2980b9" />
          </div>
        </div>
      )}
    </div>
  );
}
