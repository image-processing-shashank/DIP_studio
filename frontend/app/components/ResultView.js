"use client";

import { useEffect, useRef, useState } from "react";

function downloadDataUri(dataUri, name) {
  const a = document.createElement("a");
  a.href = dataUri;
  a.download = name;
  document.body.appendChild(a);
  a.click();
  a.remove();
}

function Histogram({ data, color, title }) {
  const ref = useRef(null);
  useEffect(() => {
    const c = ref.current;
    if (!c || !data) return;
    const dpr = window.devicePixelRatio || 1;
    const w = 256, h = 72;
    c.width = w * dpr; c.height = h * dpr;
    const ctx = c.getContext("2d");
    ctx.scale(dpr, dpr);
    ctx.clearRect(0, 0, w, h);
    const max = Math.max(...data) || 1;
    ctx.fillStyle = color;
    for (let x = 0; x < 256; x++) {
      const bh = (data[x] / max) * (h - 4);
      ctx.fillRect(x, h - bh, 1, bh);
    }
  }, [data, color]);
  return (
    <div className="hist-card">
      <div className="hist-title"><span className="hist-dot" style={{ background: color }} />{title}</div>
      <canvas ref={ref} className="hist-canvas" style={{ width: "100%", height: 72 }} />
    </div>
  );
}

function CompareSlider({ images }) {
  const [aIdx, setAIdx] = useState(0);
  const [bIdx, setBIdx] = useState(images.length > 1 ? 1 : 0);
  const [pos, setPos] = useState(50);
  const wrapRef = useRef(null);
  const dragging = useRef(false);

  const move = (clientX) => {
    const el = wrapRef.current;
    if (!el) return;
    const rect = el.getBoundingClientRect();
    const p = ((clientX - rect.left) / rect.width) * 100;
    setPos(Math.max(0, Math.min(100, p)));
  };

  useEffect(() => {
    const up = () => (dragging.current = false);
    const mv = (e) => dragging.current && move(e.touches ? e.touches[0].clientX : e.clientX);
    window.addEventListener("mouseup", up);
    window.addEventListener("mousemove", mv);
    window.addEventListener("touchend", up);
    window.addEventListener("touchmove", mv);
    return () => {
      window.removeEventListener("mouseup", up);
      window.removeEventListener("mousemove", mv);
      window.removeEventListener("touchend", up);
      window.removeEventListener("touchmove", mv);
    };
  }, []);

  return (
    <div className="compare-wrap">
      <div className="compare-pick">
        <span>Left</span>
        <select value={aIdx} onChange={(e) => setAIdx(Number(e.target.value))}>
          {images.map((im, i) => <option key={i} value={i}>{im.label}</option>)}
        </select>
        <span>Right</span>
        <select value={bIdx} onChange={(e) => setBIdx(Number(e.target.value))}>
          {images.map((im, i) => <option key={i} value={i}>{im.label}</option>)}
        </select>
      </div>
      <div
        className="compare"
        ref={wrapRef}
        onMouseDown={(e) => { dragging.current = true; move(e.clientX); }}
        onTouchStart={(e) => { dragging.current = true; move(e.touches[0].clientX); }}
      >
        <img src={images[bIdx].data} alt={images[bIdx].label} />
        <div className="after-layer" style={{ width: `${pos}%` }}>
          <img src={images[aIdx].data} alt={images[aIdx].label} />
        </div>
        <div className="compare-handle" style={{ left: `${pos}%` }}>
          <div className="compare-knob">⇆</div>
        </div>
      </div>
      <div className="compare-tags">
        <span>{images[aIdx].label}</span>
        <span>{images[bIdx].label}</span>
      </div>
    </div>
  );
}

function MetricValue({ k, v }) {
  if (typeof v === "object" && v !== null) {
    return (
      <div className="metric" key={k}>
        <div className="metric-k">{k.replace(/_/g, " ")}</div>
        <div className="metric-json">
          {Object.entries(v).map(([kk, vv]) => (
            <div className="mj-row" key={kk}><span className="mj-k">{kk}</span><span>{String(vv)}</span></div>
          ))}
        </div>
      </div>
    );
  }
  // split a trailing unit like "dB" for nicer display
  const s = String(v);
  return (
    <div className="metric" key={k}>
      <div className="metric-k">{k.replace(/_/g, " ").replace(/ dB$/i, "")}</div>
      <div className="metric-v">{s}</div>
    </div>
  );
}

export default function ResultView({ result, onZoom }) {
  const [view, setView] = useState("grid");
  if (!result) return null;
  const m = result.metrics || {};
  const hasHist = m.hist_gray;
  const scalar = Object.entries(m).filter(([k]) => !k.startsWith("hist_"));
  const canCompare = result.images.length >= 2;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
      <div className="result-card">
        <div className="result-head">
          <span className="result-title">Output · {result.images.length} image{result.images.length > 1 ? "s" : ""}</span>
          {canCompare && (
            <div className="view-toggle">
              <button className={view === "grid" ? "on" : ""} onClick={() => setView("grid")}>▦ Grid</button>
              <button className={view === "compare" ? "on" : ""} onClick={() => setView("compare")}>⇆ Compare</button>
            </div>
          )}
        </div>

        {view === "grid" ? (
          <div className="img-grid">
            {result.images.map((im, i) => (
              <figure key={i} className="img-card">
                <div className="img-figframe" onClick={() => onZoom(im)}>
                  <img src={im.data} alt={im.label} />
                </div>
                <figcaption className="img-cap">
                  <span>{im.label}</span>
                  <button
                    className="dl-btn"
                    title="Download PNG"
                    onClick={(e) => { e.stopPropagation(); downloadDataUri(im.data, `${result.operation}_${im.label.replace(/\W+/g, "_")}.png`); }}
                  >↓</button>
                </figcaption>
              </figure>
            ))}
          </div>
        ) : (
          <CompareSlider images={result.images} />
        )}
      </div>

      {scalar.length > 0 && (
        <div className="result-card">
          <div className="result-head"><span className="result-title">Metrics</span></div>
          <div className="metrics">
            {scalar.map(([k, v]) => <MetricValue key={k} k={k} v={v} />)}
          </div>
        </div>
      )}

      {hasHist && (
        <div className="result-card">
          <div className="result-head"><span className="result-title">Histograms</span></div>
          <div className="hist-row">
            <Histogram data={m.hist_gray} color="#3a3a38" title="Grayscale" />
            <Histogram data={m.hist_r} color="#c0392b" title="Red" />
            <Histogram data={m.hist_g} color="#27ae60" title="Green" />
            <Histogram data={m.hist_b} color="#2980b9" title="Blue" />
          </div>
        </div>
      )}
    </div>
  );
}
