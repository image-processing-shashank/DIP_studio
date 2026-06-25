"""Project 4: Edge Detection Benchmark."""
import cv2
import numpy as np

from ..registry import Context, Param, Result, operation

PROJECT = "Edge Detection"
ORDER = 4


def _norm(img):
    return cv2.normalize(img, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)


def _blur(gray, k):
    if k and k >= 3:
        if k % 2 == 0:
            k += 1
        return cv2.GaussianBlur(gray, (k, k), 0)
    return gray


def _roberts(g):
    kx = np.array([[1, 0], [0, -1]], np.float32)
    ky = np.array([[0, 1], [-1, 0]], np.float32)
    gx = cv2.filter2D(g.astype(np.float32), -1, kx)
    gy = cv2.filter2D(g.astype(np.float32), -1, ky)
    return _norm(np.sqrt(gx ** 2 + gy ** 2))


def _prewitt(g):
    kx = np.array([[-1, 0, 1]] * 3, np.float32)
    ky = np.array([[-1, -1, -1], [0, 0, 0], [1, 1, 1]], np.float32)
    gx = cv2.filter2D(g.astype(np.float32), -1, kx)
    gy = cv2.filter2D(g.astype(np.float32), -1, ky)
    return _norm(np.sqrt(gx ** 2 + gy ** 2))


@operation(
    id="p4.sobel",
    project_order=ORDER, project=PROJECT,
    name="Sobel",
    description="Gradient operator with center weighting. Smoother than Prewitt.",
    math="Gx, Gy via Sobel kernels;  magnitude = sqrt(Gx^2 + Gy^2)",
    params=[
        Param("blur", "Pre-blur kernel", "slider", 3, 0, 15, 1,
              help="Smooths the image before detecting edges, which suppresses noise. 0 disables it. Larger values remove more noise but can soften real edges. Odd sizes only."),
        Param("ksize", "Sobel aperture", "select", 3, options=[1, 3, 5, 7],
              help="Size of the Sobel gradient window. Larger apertures respond to broader, smoother edges and are less sensitive to fine noise."),
    ],
)
def sobel(ctx: Context) -> Result:
    g = _blur(ctx.gray, ctx.i("blur", 3))
    k = ctx.i("ksize", 3)
    gx = cv2.Sobel(g, cv2.CV_64F, 1, 0, ksize=k)
    gy = cv2.Sobel(g, cv2.CV_64F, 0, 1, ksize=k)
    return Result([("Original", ctx.gray), ("Sobel", _norm(np.sqrt(gx ** 2 + gy ** 2)))])


@operation(
    id="p4.laplacian",
    project_order=ORDER, project=PROJECT,
    name="Laplacian",
    description="Second-derivative operator. Highlights fine detail but is noise sensitive.",
    math="L = d2f/dx2 + d2f/dy2;  output = |L|",
    params=[
        Param("blur", "Pre-blur kernel", "slider", 3, 0, 15, 1,
              help="Smooths the image before detecting edges, which suppresses noise. 0 disables it. Larger values remove more noise but can soften real edges. Odd sizes only."),
        Param("ksize", "Laplacian aperture", "select", 3, options=[1, 3, 5, 7],
              help="Size of the Laplacian window. Larger apertures capture coarser intensity changes; smaller ones pick out fine detail but amplify noise."),
    ],
)
def laplacian(ctx: Context) -> Result:
    g = _blur(ctx.gray, ctx.i("blur", 3))
    lap = cv2.Laplacian(g, cv2.CV_64F, ksize=ctx.i("ksize", 3))
    return Result([("Original", ctx.gray), ("Laplacian", _norm(np.abs(lap)))])


@operation(
    id="p4.canny",
    project_order=ORDER, project=PROJECT,
    name="Canny",
    description="Multi-stage detector: smoothing, gradient, non-maximum suppression, hysteresis.",
    math="Keep edges with gradient > high; extend through pixels > low connected to them.",
    params=[
        Param("blur", "Pre-blur kernel", "slider", 3, 0, 15, 1,
              help="Smooths the image before detecting edges, which suppresses noise. 0 disables it. Larger values remove more noise but can soften real edges. Odd sizes only."),
        Param("low", "Low threshold", "slider", 100, 0, 255, 1,
              help="Weak-edge threshold. Pixels above it are kept only if they connect to a strong edge. Lower values keep more faint edges (and more noise)."),
        Param("high", "High threshold", "slider", 200, 0, 255, 1,
              help="Strong-edge threshold. Pixels above it are always kept as edges. A common rule is to set it 2 to 3 times the low threshold."),
    ],
)
def canny(ctx: Context) -> Result:
    g = _blur(ctx.gray, ctx.i("blur", 3))
    edges = cv2.Canny(g, ctx.i("low", 100), ctx.i("high", 200))
    return Result([("Original", ctx.gray), ("Canny", edges)])


@operation(
    id="p4.compare",
    project_order=ORDER, project=PROJECT,
    name="Compare All Detectors",
    description="Runs Roberts, Prewitt, Sobel, Laplacian, and Canny with shared preprocessing.",
    math="Same pre-blur applied to every detector for a fair comparison.",
    params=[
        Param("blur", "Pre-blur kernel", "slider", 3, 0, 15, 1,
              help="Smooths the image before detecting edges, which suppresses noise. 0 disables it. Larger values remove more noise but can soften real edges. Odd sizes only."),
        Param("low", "Canny low", "slider", 100, 0, 255, 1,
              help="Weak-edge threshold for the Canny detector in the comparison. Lower keeps more faint edges."),
        Param("high", "Canny high", "slider", 200, 0, 255, 1,
              help="Strong-edge threshold for the Canny detector in the comparison. Pixels above it are always edges."),
    ],
)
def compare(ctx: Context) -> Result:
    g = _blur(ctx.gray, ctx.i("blur", 3))
    gx = cv2.Sobel(g, cv2.CV_64F, 1, 0, ksize=3)
    gy = cv2.Sobel(g, cv2.CV_64F, 0, 1, ksize=3)
    sob = _norm(np.sqrt(gx ** 2 + gy ** 2))
    lap = _norm(np.abs(cv2.Laplacian(g, cv2.CV_64F, ksize=3)))
    can = cv2.Canny(g, ctx.i("low", 100), ctx.i("high", 200))
    imgs = [("Original", ctx.gray), ("Roberts", _roberts(g)), ("Prewitt", _prewitt(g)),
            ("Sobel", sob), ("Laplacian", lap), ("Canny", can)]

    def density(e):
        return round(float(np.count_nonzero(e > 40)) / e.size, 4)

    metrics = {name: density(im) for name, im in imgs[1:]}
    return Result(imgs, {"edge_density": metrics})
