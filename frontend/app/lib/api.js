// API client. Override the backend URL with NEXT_PUBLIC_API_URL.
const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function getCatalog() {
  const res = await fetch(`${API}/api/catalog`);
  if (!res.ok) throw new Error("Could not reach the backend. Is it running?");
  return res.json();
}

export async function processImage(file, operationId, params, signal) {
  const form = new FormData();
  form.append("file", file);
  form.append("operation_id", operationId);
  form.append("params", JSON.stringify(params));
  const res = await fetch(`${API}/api/process`, { method: "POST", body: form, signal });
  if (!res.ok) {
    let msg = `Request failed (${res.status})`;
    try {
      const j = await res.json();
      if (j.detail) msg = j.detail;
    } catch (_) {}
    throw new Error(msg);
  }
  return res.json();
}
