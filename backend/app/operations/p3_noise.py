"""Project 3: Noise Laboratory."""
import cv2
import numpy as np

from ..registry import Context, Param, Result, operation

PROJECT = "Noise Laboratory"
ORDER = 3


def _mse(a, b):
    a = a.astype(np.float32); b = b.astype(np.float32)
    return float(np.mean((a - b) ** 2))


def _psnr(a, b):
    e = _mse(a, b)
    return float("inf") if e == 0 else float(10.0 * np.log10((255.0 ** 2) / e))


def _add_noise(gray, model, ctx):
    rng = np.random.default_rng(ctx.i("seed", 42))
    if model == "gaussian":
        n = rng.normal(ctx.f("mean", 0.0), ctx.f("sigma", 25.0), gray.shape)
        return np.clip(gray.astype(np.float32) + n, 0, 255).astype(np.uint8)
    if model == "salt_pepper":
        amount = ctx.f("amount", 0.05)
        ratio = ctx.f("salt_ratio", 0.5)
        out = gray.copy()
        total = gray.size
        ns = int(total * amount * ratio)
        npp = int(total * amount * (1 - ratio))
        if ns:
            out[tuple(rng.integers(0, s, ns) for s in gray.shape)] = 255
        if npp:
            out[tuple(rng.integers(0, s, npp) for s in gray.shape)] = 0
        return out
    # speckle
    n = rng.normal(0.0, ctx.f("speckle_sigma", 0.25), gray.shape)
    return np.clip(gray.astype(np.float32) * (1 + n), 0, 255).astype(np.uint8)


def _filter(noisy, ftype, ctx):
    k = ctx.i("ksize", 3)
    if k % 2 == 0:
        k += 1
    if ftype == "mean":
        return cv2.blur(noisy, (k, k))
    if ftype == "median":
        return cv2.medianBlur(noisy, k)
    return cv2.GaussianBlur(noisy, (k, k), ctx.f("filter_sigma", 0.0))


@operation(
    id="p3.noise_restore",
    project_order=ORDER, project=PROJECT,
    name="Noise & Restoration",
    description=(
        "Adds a chosen synthetic noise model to the clean image, then restores it "
        "with a chosen filter. Reports MSE and PSNR against the clean reference."
    ),
    math=("MSE  = (1/MN) * sum( (I - K)^2 )\n"
          "PSNR = 10 * log10( 255^2 / MSE )   (decibels)"),
    params=[
        Param("noise", "Noise model", "select", "gaussian",
              options=["gaussian", "salt_pepper", "speckle"]),
        Param("sigma", "Gaussian sigma", "slider", 25.0, 1.0, 100.0, 1.0),
        Param("mean", "Gaussian mean", "slider", 0.0, -50.0, 50.0, 1.0),
        Param("amount", "Salt&pepper amount", "slider", 0.05, 0.0, 0.30, 0.005),
        Param("salt_ratio", "Salt ratio", "slider", 0.5, 0.0, 1.0, 0.05),
        Param("speckle_sigma", "Speckle sigma", "slider", 0.25, 0.05, 0.60, 0.01),
        Param("seed", "Random seed", "slider", 42, 0, 9999, 1),
        Param("filter", "Restoration filter", "select", "median",
              options=["mean", "median", "gaussian"]),
        Param("ksize", "Filter kernel size", "slider", 3, 1, 31, 2),
        Param("filter_sigma", "Gaussian filter sigma", "slider", 0.0, 0.0, 20.0, 0.5),
    ],
)
def noise_restore(ctx: Context) -> Result:
    gray = ctx.gray
    noisy = _add_noise(gray, ctx.s("noise", "gaussian"), ctx)
    restored = _filter(noisy, ctx.s("filter", "median"), ctx)
    metrics = {
        "MSE_noisy": round(_mse(gray, noisy), 3),
        "PSNR_noisy_dB": round(_psnr(gray, noisy), 2),
        "MSE_restored": round(_mse(gray, restored), 3),
        "PSNR_restored_dB": round(_psnr(gray, restored), 2),
    }
    return Result([("Clean", gray), ("Noisy", noisy), ("Restored", restored)], metrics)
