# DIP Studio

A Next.js + FastAPI application that runs the Digital Image Processing portfolio
projects on an uploaded image. It currently exposes Projects 1 through 6 and is
built to scale to all 20 by adding one backend module per project.

```
dip-studio/
  backend/    FastAPI service (image processing)
  frontend/   Next.js UI (minimal, catalog-driven)
```

## Quick start

### 1. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

The API is now at http://localhost:8000 (catalog at /api/catalog).

### 2. Frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local   # only if your backend is not on localhost:8000
npm run dev
```

Open http://localhost:3000, upload an image, pick an operation, adjust the
sliders, and press Run.

## Supported input

PNG, JPEG, and TIFF, decoded with OpenCV only (no extra imaging library).
Grayscale, RGB, RGBA, and 16-bit inputs are all handled. The upload limit is
600 MB by default. Very large images are downsampled to a 2000 px longest edge
before processing so heavy operations stay responsive; both limits are
configurable through environment variables (see backend/app/config.py).

## How it scales to 20 projects

The backend is a registry. Each project is a module under
`backend/app/operations/` whose functions are decorated with `@operation(...)`.
The decorator records the operation id, its project, description, the maths
involved, and its parameters (sliders and selects). The API serves this as a
catalog, and the frontend renders every control from that catalog.

To add Project 7:

1. Create `backend/app/operations/p7_xxx.py`.
2. Write one or more `@operation`-decorated functions, each returning a
   `Result(images=[(label, ndarray), ...], metrics={...})`.
3. Add `from . import p7_xxx` to `backend/app/operations/__init__.py`.

No frontend change is needed. The new project and its sliders appear
automatically, including the info popup with its description and maths.

## API

- `GET /api/health` -> `{ "status": "ok" }`
- `GET /api/catalog` -> projects, operations, and parameter definitions
- `POST /api/process` (multipart) -> fields: `file`, `operation_id`,
  `params` (JSON). Returns base64 PNG images and any metrics.

## Projects included

1. Image Explorer: channels, grayscale, statistics, histograms
2. Enhancement Studio: brightness/contrast, gamma, contrast stretch, equalization, CLAHE
3. Noise Laboratory: Gaussian / salt-and-pepper / speckle noise with mean / median / Gaussian filters, plus MSE and PSNR
4. Edge Detection: Roberts, Prewitt, Sobel, Laplacian, Canny, and a compare view
5. Fourier Explorer: magnitude spectrum, low-pass, high-pass, band-pass filtering
6. Morphology: erosion, dilation, opening, closing, gradient, top-hat, black-hat
