"""Project 2: Enhancement Studio."""
import cv2
import numpy as np

from ..registry import Context, Param, Result, operation

PROJECT = "Enhancement Studio"
ORDER = 2


@operation(
    id="p2.brightness_contrast",
    project_order=ORDER, project=PROJECT,
    name="Brightness & Contrast",
    description="Linear intensity transform. Alpha scales contrast, beta shifts brightness.",
    math="g(x, y) = clip( alpha * f(x, y) + beta , 0, 255 )",
    params=[
        Param("alpha", "Contrast (alpha)", "slider", 1.0, 0.1, 3.0, 0.05),
        Param("beta", "Brightness (beta)", "slider", 0, -127, 127, 1),
    ],
)
def brightness_contrast(ctx: Context) -> Result:
    out = cv2.convertScaleAbs(ctx.gray, alpha=ctx.f("alpha", 1.0), beta=ctx.i("beta", 0))
    return Result([("Original", ctx.gray), ("Adjusted", out)])


@operation(
    id="p2.gamma",
    project_order=ORDER, project=PROJECT,
    name="Gamma Correction",
    description="Nonlinear tone mapping. Gamma below 1 brightens mid-tones, above 1 darkens them.",
    math="s = 255 * ( r / 255 ) ^ gamma",
    params=[Param("gamma", "Gamma", "slider", 1.0, 0.1, 3.0, 0.05)],
)
def gamma(ctx: Context) -> Result:
    g = ctx.f("gamma", 1.0)
    lut = np.array([((i / 255.0) ** g) * 255 for i in range(256)], dtype=np.uint8)
    out = cv2.LUT(ctx.gray, lut)
    return Result([("Original", ctx.gray), ("Gamma corrected", out)])


@operation(
    id="p2.contrast_stretch",
    project_order=ORDER, project=PROJECT,
    name="Contrast Stretching",
    description="Maps the intensity range between two percentiles to the full 0..255 range.",
    math=("low  = percentile(f, low_pct)\n"
          "high = percentile(f, high_pct)\n"
          "g = clip( (f - low) / (high - low) * 255 , 0, 255 )"),
    params=[
        Param("low_pct", "Lower percentile", "slider", 2.0, 0.0, 20.0, 0.5),
        Param("high_pct", "Upper percentile", "slider", 98.0, 80.0, 100.0, 0.5),
    ],
)
def contrast_stretch(ctx: Context) -> Result:
    f = ctx.gray.astype(np.float32)
    lo = np.percentile(f, ctx.f("low_pct", 2.0))
    hi = np.percentile(f, ctx.f("high_pct", 98.0))
    if hi <= lo:
        out = np.zeros_like(ctx.gray)
    else:
        out = np.clip((f - lo) / (hi - lo) * 255.0, 0, 255).astype(np.uint8)
    return Result([("Original", ctx.gray), ("Stretched", out)])


@operation(
    id="p2.hist_equalize",
    project_order=ORDER, project=PROJECT,
    name="Histogram Equalization",
    description="Redistributes intensities using the cumulative distribution for global contrast.",
    math="s = round( (L - 1) * CDF(r) ),  L = 256",
    params=[],
)
def hist_equalize(ctx: Context) -> Result:
    out = cv2.equalizeHist(ctx.gray)
    return Result([("Original", ctx.gray), ("Equalized", out)])


@operation(
    id="p2.clahe",
    project_order=ORDER, project=PROJECT,
    name="CLAHE",
    description="Contrast Limited Adaptive Histogram Equalization. Local equalization with a clip limit.",
    math=("Per tile: equalize the local histogram, but clip any bin above\n"
          "clip_limit and redistribute the excess before building the CDF."),
    params=[
        Param("clip", "Clip limit", "slider", 2.0, 0.5, 8.0, 0.1),
        Param("tile", "Tile grid size", "slider", 8, 2, 32, 1),
    ],
)
def clahe(ctx: Context) -> Result:
    t = ctx.i("tile", 8)
    obj = cv2.createCLAHE(clipLimit=ctx.f("clip", 2.0), tileGridSize=(t, t))
    out = obj.apply(ctx.gray)
    return Result([("Original", ctx.gray), ("CLAHE", out)])
