"""Project 2: Enhancement Studio."""
import cv2
import numpy as np

from ..registry import Context, Param, Result, operation

PROJECT = "Enhancement Studio"
ORDER = 2

# Shared "output mode" param. Color is processed the mathematically correct way
# for each operation (see notes per function).
def _mode_param(default="color"):
    return Param(
        "mode", "Output", "select", default, options=["grayscale", "color"],
        help="Grayscale processes the luminance only. Color applies the same enhancement while preserving the image's hues (point operations act per channel; equalization acts on the L channel of LAB so colors are not distorted).",
    )

def _rgb(ctx):
    return cv2.cvtColor(ctx.color, cv2.COLOR_BGR2RGB)


@operation(
    id="p2.brightness_contrast",
    project_order=ORDER, project=PROJECT,
    name="Brightness & Contrast",
    description="Linear intensity transform. Alpha scales contrast, beta shifts brightness.",
    math="g(x, y) = clip( alpha * f(x, y) + beta , 0, 255 )",
    params=[
        Param("alpha", "Contrast (alpha)", "slider", 1.0, 0.1, 3.0, 0.05,
              help="Multiplies every pixel value to stretch or compress contrast. 1.0 leaves the image unchanged, below 1.0 flattens contrast toward mid-grey, above 1.0 pushes darks darker and brights brighter."),
        Param("beta", "Brightness (beta)", "slider", 0, -127, 127, 1,
              help="Adds a fixed amount to every pixel, sliding the whole image lighter or darker. Positive values brighten, negative values darken; extreme values clip detail at black or white."),
        _mode_param(),
    ],
)
def brightness_contrast(ctx: Context) -> Result:
    # Point operation: identical formula applied to each channel. Color is valid.
    a, b = ctx.f("alpha", 1.0), ctx.i("beta", 0)
    if ctx.s("mode", "color") == "color" and ctx.is_color:
        src = _rgb(ctx)
        out = cv2.convertScaleAbs(src, alpha=a, beta=b)
        return Result([("Original", src), ("Adjusted", out)])
    out = cv2.convertScaleAbs(ctx.gray, alpha=a, beta=b)
    return Result([("Original", ctx.gray), ("Adjusted", out)])


@operation(
    id="p2.gamma",
    project_order=ORDER, project=PROJECT,
    name="Gamma Correction",
    description="Nonlinear tone mapping. Gamma below 1 brightens mid-tones, above 1 darkens them.",
    math="s = 255 * ( r / 255 ) ^ gamma",
    params=[
        Param("gamma", "Gamma", "slider", 1.0, 0.1, 3.0, 0.05,
              help="Bends the tone curve. Below 1.0 lifts shadows and mid-tones (brighter), above 1.0 pushes them down (darker). Pure black and white stay fixed while mid-tones shift the most. 2.2 mimics a standard display."),
        _mode_param(),
    ],
)
def gamma(ctx: Context) -> Result:
    # Point operation via a LUT applied per channel. Color is valid.
    g = ctx.f("gamma", 1.0)
    lut = np.array([((i / 255.0) ** g) * 255 for i in range(256)], dtype=np.uint8)
    if ctx.s("mode", "color") == "color" and ctx.is_color:
        src = _rgb(ctx)
        return Result([("Original", src), ("Gamma corrected", cv2.LUT(src, lut))])
    return Result([("Original", ctx.gray), ("Gamma corrected", cv2.LUT(ctx.gray, lut))])


@operation(
    id="p2.contrast_stretch",
    project_order=ORDER, project=PROJECT,
    name="Contrast Stretching",
    description="Maps the intensity range between two percentiles to the full 0..255 range.",
    math=("low  = percentile(f, low_pct)\n"
          "high = percentile(f, high_pct)\n"
          "g = clip( (f - low) / (high - low) * 255 , 0, 255 )"),
    params=[
        Param("low_pct", "Lower percentile", "slider", 2.0, 0.0, 20.0, 0.5,
              help="The darkest this fraction of pixels is forced to pure black. Raising it deepens shadows and boosts contrast, at the cost of clipping dark detail. 1-2 percent is the usual safe choice."),
        Param("high_pct", "Upper percentile", "slider", 98.0, 80.0, 100.0, 0.5,
              help="The brightest this fraction of pixels is forced to pure white. Lowering it brightens highlights and boosts contrast, at the cost of clipping bright detail. 98-99 percent is typical."),
        _mode_param(),
    ],
)
def contrast_stretch(ctx: Context) -> Result:
    lo_p, hi_p = ctx.f("low_pct", 2.0), ctx.f("high_pct", 98.0)

    def stretch(ch):
        f = ch.astype(np.float32)
        lo = np.percentile(f, lo_p)
        hi = np.percentile(f, hi_p)
        if hi <= lo:
            return np.zeros_like(ch)
        return np.clip((f - lo) / (hi - lo) * 255.0, 0, 255).astype(np.uint8)

    if ctx.s("mode", "color") == "color" and ctx.is_color:
        # Stretch on luminance, then rescale RGB by the same factor so hue is preserved.
        src = _rgb(ctx)
        lab = cv2.cvtColor(src, cv2.COLOR_RGB2LAB)
        lab[:, :, 0] = stretch(lab[:, :, 0])
        out = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)
        return Result([("Original", src), ("Stretched", out)])
    return Result([("Original", ctx.gray), ("Stretched", stretch(ctx.gray))])


@operation(
    id="p2.hist_equalize",
    project_order=ORDER, project=PROJECT,
    name="Histogram Equalization",
    description="Redistributes intensities using the cumulative distribution for global contrast.",
    math="s = round( (L - 1) * CDF(r) )  where L = 256, output range = 0..255\nColour mode equalizes the L channel of LAB so hues are preserved.",
    params=[_mode_param()],
)
def hist_equalize(ctx: Context) -> Result:
    if ctx.s("mode", "color") == "color" and ctx.is_color:
        # Equalizing R, G, B independently shifts colours. The correct approach
        # equalizes only the lightness (L) channel in LAB space.
        src = _rgb(ctx)
        lab = cv2.cvtColor(src, cv2.COLOR_RGB2LAB)
        lab[:, :, 0] = cv2.equalizeHist(lab[:, :, 0])
        out = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)
        return Result([("Original", src), ("Equalized", out)])
    return Result([("Original", ctx.gray), ("Equalized", cv2.equalizeHist(ctx.gray))])


@operation(
    id="p2.clahe",
    project_order=ORDER, project=PROJECT,
    name="CLAHE",
    description="Contrast Limited Adaptive Histogram Equalization. Local equalization with a clip limit.",
    math=("Per tile: equalize the local histogram, but clip any bin above\n"
          "clip_limit and redistribute the excess before building the CDF.\n"
          "Colour mode applies CLAHE to the L channel of LAB."),
    params=[
        Param("clip", "Clip limit", "slider", 2.0, 0.5, 8.0, 0.1,
              help="Caps how much contrast each local tile may add, which limits noise being amplified in flat regions. 1-2 is gentle and clinical, higher values give stronger but noisier enhancement."),
        Param("tile", "Tile grid size", "slider", 8, 2, 32, 1,
              help="Splits the image into this many tiles per side for local equalization. Larger grids adapt to finer regions and reveal more local detail; smaller grids behave closer to a single global equalization."),
        _mode_param(),
    ],
)
def clahe(ctx: Context) -> Result:
    t = ctx.i("tile", 8)
    obj = cv2.createCLAHE(clipLimit=ctx.f("clip", 2.0), tileGridSize=(t, t))
    if ctx.s("mode", "color") == "color" and ctx.is_color:
        src = _rgb(ctx)
        lab = cv2.cvtColor(src, cv2.COLOR_RGB2LAB)
        lab[:, :, 0] = obj.apply(lab[:, :, 0])
        out = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)
        return Result([("Original", src), ("CLAHE", out)])
    return Result([("Original", ctx.gray), ("CLAHE", obj.apply(ctx.gray))])
