"""Project 1: Image Explorer."""
import cv2
import numpy as np

from ..registry import Context, Param, Result, operation

PROJECT = "Image Explorer"
ORDER = 1


@operation(
    id="p1.explore",
    project_order=ORDER, project=PROJECT,
    name="Channel & Histogram Explorer",
    description=(
        "Inspects how the image is stored: separates the red, green, and blue "
        "channels, converts to grayscale using the luminance weights, and reports "
        "basic statistics and intensity histograms."
    ),
    math=(
        "Grayscale (luminance):\n"
        "  Y = 0.299 R + 0.587 G + 0.114 B\n\n"
        "Histogram:\n"
        "  h(k) = number of pixels with intensity k,  k = 0..255\n\n"
        "Channel display modes:\n"
        "  raw     — true pixel values (scientifically accurate)\n"
        "  stretch — each channel normalized to 0-255 independently\n"
        "            (reveals structure in weak channels, e.g. blue in\n"
        "            retinal images, matching matplotlib cmap behaviour)"
    ),
    requires="color",
    params=[
        Param(
            "channel_display", "Channel display", "select", "both",
            options=["raw", "stretch", "both"],
            help=(
                "raw: true pixel values. "
                "stretch: per-channel normalization to show internal structure. "
                "both: shows raw then stretched side by side for each channel."
            ),
        ),
    ],
)
def explore(ctx: Context) -> Result:
    color_rgb = cv2.cvtColor(ctx.color, cv2.COLOR_BGR2RGB)
    gray = ctx.gray
    r = color_rgb[:, :, 0]
    g = color_rgb[:, :, 1]
    b = color_rgb[:, :, 2]
    zeros = np.zeros_like(r)
    mode = ctx.s("channel_display", "both")

    def norm(ch):
        mn, mx = int(ch.min()), int(ch.max())
        if mx <= mn:
            return ch
        return ((ch.astype(np.float32) - mn) / (mx - mn) * 255).astype(np.uint8)

    def raw_rgb(ch, slot):
        planes = [zeros, zeros, zeros]
        planes[slot] = ch
        return np.stack(planes, axis=-1)

    def stretch_rgb(ch, slot):
        planes = [zeros, zeros, zeros]
        planes[slot] = norm(ch)
        return np.stack(planes, axis=-1)

    channels = [(r, 0, "Red"), (g, 1, "Green"), (b, 2, "Blue")]

    images = [("Original", color_rgb), ("Grayscale", gray)]

    for ch, slot, name in channels:
        if mode == "raw":
            images.append((f"{name} channel", raw_rgb(ch, slot)))
        elif mode == "stretch":
            images.append((f"{name} channel (stretched)", stretch_rgb(ch, slot)))
        else:  # both
            images.append((f"{name} — raw", raw_rgb(ch, slot)))
            images.append((f"{name} — stretched", stretch_rgb(ch, slot)))

    def hist(a):
        return np.histogram(a, bins=256, range=(0, 255))[0].tolist()

    metrics = {
        "width": int(gray.shape[1]),
        "height": int(gray.shape[0]),
        "channels": 3,
        "min": int(gray.min()),
        "max": int(gray.max()),
        "mean": round(float(gray.mean()), 2),
        "std": round(float(gray.std()), 2),
        "hist_gray": hist(gray),
        "hist_r": hist(r),
        "hist_g": hist(g),
        "hist_b": hist(b),
    }
    return Result(images=images, metrics=metrics)
