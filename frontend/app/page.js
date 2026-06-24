"use client";

import { useEffect, useMemo, useState } from "react";
import { getCatalog, processImage } from "./lib/api";
import Controls from "./components/Controls";
import ResultView from "./components/ResultView";
import InfoModal from "./components/InfoModal";

export default function Page() {
  const [catalog, setCatalog] = useState(null);
  const [error, setError] = useState("");
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [opId, setOpId] = useState(null);
  const [values, setValues] = useState({});
  const [result, setResult] = useState(null);
  const [busy, setBusy] = useState(false);
  const [infoOp, setInfoOp] = useState(null);
  const [imageInfo, setImageInfo] = useState(null);

  useEffect(() => {
    getCatalog().then(setCatalog).catch((e) => setError(e.message));
  }, []);

  // Flat lookup of operations by id.
  const opsById = useMemo(() => {
    const map = {};
    catalog?.projects.forEach((g) =>
      g.operations.forEach((o) => (map[o.id] = o))
    );
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
  }

  function onFile(e) {
    const f = e.target.files[0];
    if (!f) return;
    setFile(f);
    setPreview(URL.createObjectURL(f));
    setResult(null);
    setImageInfo(null);
  }

  async function run() {
    if (!file || !currentOp) return;
    setBusy(true);
    setError("");
    try {
      const res = await processImage(file, currentOp.id, values);
      setResult(res);
      if (res.image_info) setImageInfo(res.image_info);
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="page">
      <header className="topbar">
        <div>
          <h1>DIP Studio</h1>
          <p className="muted">Digital Image Processing pipeline · IIT Delhi mPragati</p>
        </div>
      </header>

      {error && <div className="error">{error}</div>}

      <section className="upload">
        <label className="file-btn">
          {file ? "Change image" : "Upload image (PNG / JPEG / TIFF / PPM)"}
          <input type="file" accept="image/png,image/jpeg,image/tiff,.tif,.tiff,.ppm,.pgm,.pbm" onChange={onFile} />
        </label>
        {preview && (
          <div className="preview-wrap">
            <img className="preview" src={preview} alt="input preview" />
            {imageInfo && (
              <div className="img-badges">
                <span className={"img-badge " + (imageInfo.is_color ? "badge-rgb" : "badge-gray")}>
                  {imageInfo.is_color ? "RGB" : "Grayscale"}
                </span>
                <span className="img-badge badge-info">{imageInfo.bit_depth}-bit</span>
                <span className="img-badge badge-info">{imageInfo.width} × {imageInfo.height}</span>
                <span className="img-badge badge-info">{imageInfo.channels}ch</span>
              </div>
            )}
          </div>
        )}
      </section>

      {!catalog && !error && <p className="muted">Loading operations…</p>}

      {catalog && (
        <div className="layout">
          <aside className="sidebar">
            {catalog.projects.map((g) => (
              <div className="proj" key={g.order}>
                <div className="proj-title">
                  {g.order}. {g.project}
                </div>
                {g.operations.map((o) => (
                  <div
                    key={o.id}
                    className={"op-row" + (o.id === opId ? " active" : "")}
                  >
                    <button className="op-btn" onClick={() => selectOp(o.id)}>
                      {o.name}
                    </button>
                    <button
                      className="info-sup"
                      title="What is this?"
                      onClick={() => setInfoOp(o)}
                    >
                      i
                    </button>
                  </div>
                ))}
              </div>
            ))}
          </aside>

          <div className="work">
            {currentOp ? (
              <>
                <div className="op-head">
                  <h2>
                    {currentOp.name}
                    <button className="info-sup" onClick={() => setInfoOp(currentOp)} title="What is this?">
                      i
                    </button>
                  </h2>
                  <p className="muted">{currentOp.description}</p>
                </div>

                <Controls
                  params={currentOp.params}
                  values={values}
                  onChange={(k, v) => setValues((s) => ({ ...s, [k]: v }))}
                />

                <button className="run-btn" onClick={run} disabled={!file || busy}>
                  {busy ? "Processing…" : "Run"}
                </button>

                {!file && <p className="muted">Upload an image to run this operation.</p>}

                <ResultView result={result} />
              </>
            ) : (
              <p className="muted">Select an operation from the left to begin.</p>
            )}
          </div>
        </div>
      )}

      <InfoModal op={infoOp} onClose={() => setInfoOp(null)} />
    </main>
  );
}
