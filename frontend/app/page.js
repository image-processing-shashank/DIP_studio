"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { getCatalog, processImage } from "./lib/api";
import Controls from "./components/Controls";
import ResultView from "./components/ResultView";
import InfoModal from "./components/InfoModal";

export default function Page() {
  const [catalog, setCatalog] = useState(null);
  const [error, setError] = useState("");
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [thumbOk, setThumbOk] = useState(true);     // does the browser preview render?
  const [opId, setOpId] = useState(null);
  const [values, setValues] = useState({});
  const [result, setResult] = useState(null);
  const [busy, setBusy] = useState(false);
  const [infoOp, setInfoOp] = useState(null);
  const [imageInfo, setImageInfo] = useState(null);
  const [drag, setDrag] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [auto, setAuto] = useState(false);
  const [zoomImg, setZoomImg] = useState(null);

  const fileInputRef = useRef(null);
  const abortRef = useRef(null);
  const debounceRef = useRef(null);

  useEffect(() => {
    getCatalog().then(setCatalog).catch((e) => setError(e.message));
  }, []);

  const opsById = useMemo(() => {
    const map = {};
    catalog?.projects.forEach((g) => g.operations.forEach((o) => (map[o.id] = o)));
    return map;
  }, [catalog]);

  const currentOp = opId ? opsById[opId] : null;

  function selectOp(id) {
    setOpId(id);
    const op = opsById[id];
    const defs = {};
    op.params.forEach((p) => (defs[p.name] = p.default));
    setValues(defs);
    setResult(null);
    if (window.innerWidth <= 860) setSidebarOpen(false);
  }

  function loadFile(f) {
    if (!f) return;
    setFile(f);
    setThumbOk(true);                         // assume it renders until onError says otherwise
    setPreview(URL.createObjectURL(f));
    setResult(null);
    setImageInfo(null);
  }

  function onFile(e) { loadFile(e.target.files[0]); }

  function onDrop(e) {
    e.preventDefault();
    setDrag(false);
    const f = e.dataTransfer.files?.[0];
    if (f) loadFile(f);
  }

  async function run() {
    if (!file || !currentOp) return;
    if (abortRef.current) abortRef.current.abort();
    const controller = new AbortController();
    abortRef.current = controller;
    setBusy(true);
    setError("");
    try {
      const res = await processImage(file, currentOp.id, values, controller.signal);
      setResult(res);
      if (res.image_info) setImageInfo(res.image_info);
    } catch (e) {
      if (e.name !== "AbortError") setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  useEffect(() => {
    if (!auto || !file || !currentOp) return;
    clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(run, 350);
    return () => clearTimeout(debounceRef.current);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [values, opId, auto, file]);

  useEffect(() => {
    const onKey = (e) => {
      if (e.key === "Enter" && !busy && file && currentOp && !infoOp && !zoomImg) {
        if (document.activeElement?.tagName !== "INPUT" || document.activeElement?.type === "range") run();
      }
      if (e.key === "Escape") { setZoomImg(null); }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [busy, file, currentOp, values, infoOp, zoomImg]);

  const showThumb = preview && thumbOk;

  return (
    <div className="shell">
      <header className="topbar">
        <div className="brand">
          {catalog && (
            <button className="menu-btn" onClick={() => setSidebarOpen((v) => !v)} aria-label="Toggle sidebar">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round">
                <path d="M3 6h18M3 12h18M3 18h18" />
              </svg>
            </button>
          )}
          <div className="logo-mark">DIP</div>
          <div>
            <h1>DIP Studio</h1>
            <div className="sub">Image Processing Pipeline · IIT Delhi mPragati</div>
          </div>
        </div>
        <div className="topbar-right">
          <span className="kbd-hint"><span className="kbd">Enter</span> to run</span>
        </div>
      </header>

      <div className="container">
        {error && <div className="error" style={{ marginBottom: 12 }}>⚠ {error}</div>}

        {!catalog && !error && <p className="muted">Loading operations…</p>}

        {catalog && (
          <div className={"layout" + (sidebarOpen ? "" : " rail")}>
            {sidebarOpen && <div className="scrim" onClick={() => setSidebarOpen(false)} />}
            <aside className={"sidebar" + (sidebarOpen ? " open" : " collapsed")}>
              <div className="sidebar-scroll">
                {catalog.projects.map((g) => {
                  const hasActive = g.operations.some((o) => o.id === opId);
                  return (
                    <div className={"proj" + (hasActive ? " proj-active" : "")} key={g.order}>
                      <div className="proj-title">
                        <span className="proj-num">{g.order}</span>
                        <span className="proj-name">{g.project}</span>
                      </div>
                      <div className="proj-ops">
                        {g.operations.map((o) => (
                          <div key={o.id} className={"op-row" + (o.id === opId ? " active" : "")}>
                            <button className="op-btn" onClick={() => selectOp(o.id)}>{o.name}</button>
                          </div>
                        ))}
                      </div>
                    </div>
                  );
                })}
              </div>
            </aside>

            <div className="work">
              <div
                className={"dropzone" + (drag ? " drag" : "") + (file ? " has-file" : "")}
                onDragOver={(e) => { e.preventDefault(); setDrag(true); }}
                onDragLeave={() => setDrag(false)}
                onDrop={onDrop}
                onClick={() => !file && fileInputRef.current?.click()}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/png,image/jpeg,image/tiff,.tif,.tiff,.ppm,.pgm,.pbm"
                  onChange={onFile}
                  style={{ display: "none" }}
                />
                {!file ? (
                  <>
                    <div className="dz-icon">
                      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M12 16V4M12 4l-4 4M12 4l4 4" strokeLinecap="round" strokeLinejoin="round" />
                        <path d="M4 16v2a2 2 0 002 2h12a2 2 0 002-2v-2" strokeLinecap="round" />
                      </svg>
                    </div>
                    <div className="dz-text">
                      <div className="dz-title">Drop an image here, or click to browse</div>
                      <div className="dz-sub">PNG · JPEG · TIFF · PPM — up to {catalog.limits?.max_upload_mb || 600} MB</div>
                    </div>
                  </>
                ) : (
                  <div className="dz-preview">
                    {showThumb && (
                      <img
                        className="dz-thumb"
                        src={preview}
                        alt="preview"
                        onError={() => setThumbOk(false)}
                      />
                    )}
                    <div className="dz-meta">
                      <div className="dz-filename">{file.name}</div>
                      {imageInfo ? (
                        <div className="badges">
                          <span className={"badge " + (imageInfo.is_color ? "badge-rgb" : "badge-gray")}>
                            {imageInfo.is_color ? "RGB" : "GRAYSCALE"}
                          </span>
                          <span className="badge badge-info">{imageInfo.bit_depth}-bit</span>
                          <span className="badge badge-info">{imageInfo.width}×{imageInfo.height}</span>
                          <span className="badge badge-info">{imageInfo.channels}ch</span>
                        </div>
                      ) : (
                        <div className="dz-sub">Run an operation to inspect type and dimensions.</div>
                      )}
                    </div>
                    <button className="dz-change" onClick={(e) => { e.stopPropagation(); fileInputRef.current?.click(); }}>Change</button>
                  </div>
                )}
              </div>

              {currentOp ? (
                <>
                  <div className="op-head">
                    <div className="op-head-top">
                      <h2>
                        {currentOp.name}
                        <button className="info-sup" onClick={() => setInfoOp(currentOp)} title="About this operation">i</button>
                      </h2>
                      <span className="op-chip">{currentOp.project}</span>
                    </div>
                    <p>{currentOp.description}</p>
                  </div>

                  <Controls
                    params={currentOp.params}
                    values={values}
                    onChange={(k, v) => setValues((s) => ({ ...s, [k]: v }))}
                    onReset={() => {
                      const defs = {};
                      currentOp.params.forEach((p) => (defs[p.name] = p.default));
                      setValues(defs);
                    }}
                  />

                  <div className="action-bar">
                    <button className="run-btn" onClick={run} disabled={!file || busy}>
                      {busy ? <><span className="run-spinner" /> Processing…</> : <>▶ Run operation</>}
                    </button>
                    <label className="auto-toggle">
                      <span className="switch">
                        <input type="checkbox" checked={auto} onChange={(e) => setAuto(e.target.checked)} />
                        <span className="switch-track" />
                      </span>
                      Live preview
                    </label>
                    {!file && <span className="muted">Upload an image to enable Run.</span>}
                  </div>

                  {busy && !result && (
                    <div className="result-card">
                      <div className="skel-grid">
                        <div className="skel skel-card" /><div className="skel skel-card" /><div className="skel skel-card" />
                      </div>
                    </div>
                  )}

                  <ResultView result={result} onZoom={setZoomImg} />
                </>
              ) : (
                <div className="empty-state">
                  <div className="empty-art">
                    <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#167a52" strokeWidth="1.8">
                      <rect x="3" y="3" width="18" height="18" rx="3" /><circle cx="9" cy="9" r="2" /><path d="M21 15l-5-5L5 21" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                  </div>
                  <h3>Pick an operation to begin</h3>
                  <p className="muted">Choose any of the {catalog.projects.reduce((n, g) => n + g.operations.length, 0)} operations from the sidebar.</p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      <InfoModal op={infoOp} onClose={() => setInfoOp(null)} />

      {zoomImg && (
        <div className="lightbox" onClick={() => setZoomImg(null)}>
          <img src={zoomImg.data} alt={zoomImg.label} />
          <div className="lightbox-cap">{zoomImg.label} · click anywhere to close</div>
        </div>
      )}
    </div>
  );
}
