"""FastAPI application: serves the operation catalog and processes images."""
import json

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from . import config, io_utils, registry
from . import operations  # noqa: F401  (registers all operations on import)

app = FastAPI(title="DIP Studio API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/catalog")
def catalog():
    """Projects, each with its operations and parameter definitions."""
    return {"projects": registry.build_catalog(), "limits": {
        "max_upload_mb": config.MAX_UPLOAD_MB,
        "max_process_dim": config.MAX_PROCESS_DIM,
    }}


@app.post("/api/process")
async def process(
    operation_id: str = Form(...),
    params: str = Form("{}"),
    file: UploadFile = File(...),
):
    data = await file.read()

    size_mb = len(data) / (1024 * 1024)
    if size_mb > config.MAX_UPLOAD_MB:
        raise HTTPException(413, f"File too large: {size_mb:.0f} MB (limit {config.MAX_UPLOAD_MB} MB).")

    try:
        param_dict = json.loads(params) if params else {}
    except json.JSONDecodeError:
        raise HTTPException(400, "params must be valid JSON.")

    try:
        op = registry.get_operation(operation_id)
    except KeyError:
        raise HTTPException(404, f"Unknown operation: {operation_id}")

    try:
        color, gray, meta = io_utils.decode_image(data)
    except ValueError as e:
        raise HTTPException(400, str(e))

    # Early type check: reject incompatible image/operation combinations
    # before any processing happens.
    try:
        op.check_image_type(meta.is_color, meta.mode)
    except ValueError as e:
        raise HTTPException(422, str(e))

    ctx = registry.Context(
        color=color, gray=gray,
        params=param_dict,
        is_color=meta.is_color,
    )
    try:
        result = op.func(ctx)
    except Exception as e:
        raise HTTPException(500, f"Processing failed: {e}")

    images = [{"label": label, "data": io_utils.to_png_data_uri(img)}
              for label, img in result.images]

    return {
        "operation": operation_id,
        "images": images,
        "metrics": result.metrics,
        # Always return what we detected so the frontend can show it.
        "image_info": {
            "mode": meta.mode,
            "is_color": meta.is_color,
            "channels": meta.channels,
            "bit_depth": meta.bit_depth,
            "width": meta.width,
            "height": meta.height,
        },
    }
