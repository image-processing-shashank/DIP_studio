"""Project 5: Fourier Transform Explorer."""
import numpy as np

from ..registry import Context, Param, Result, operation

PROJECT = "Fourier Explorer"
ORDER = 5


def _fft(gray):
    return np.fft.fftshift(np.fft.fft2(gray.astype(np.float32)))


def _spectrum(fshift):
    return np.log1p(np.abs(fshift))


def _reconstruct(fshift):
    img = np.abs(np.fft.ifft2(np.fft.ifftshift(fshift)))
    return np.clip(img, 0, 255).astype(np.uint8)


def _dist(shape):
    rows, cols = shape
    u = np.arange(rows).reshape(-1, 1) - rows // 2
    v = np.arange(cols).reshape(1, -1) - cols // 2
    return np.sqrt(u ** 2 + v ** 2)


@operation(
    id="p5.spectrum",
    project_order=ORDER, project=PROJECT,
    name="Magnitude Spectrum",
    description="Shows the log-scaled magnitude spectrum. Center is low frequency, edges high.",
    math="F(u,v) = sum_x sum_y f(x,y) e^(-j2pi(ux/M + vy/N));  display log(1 + |F|)",
    params=[],
)
def spectrum(ctx: Context) -> Result:
    f = _fft(ctx.gray)
    return Result([("Original", ctx.gray), ("Magnitude spectrum", _spectrum(f))])


@operation(
    id="p5.lowpass",
    project_order=ORDER, project=PROJECT,
    name="Low-Pass Filter",
    description="Keeps central low frequencies inside the cutoff radius. Smooths the image.",
    math="H(u,v) = 1 if D(u,v) <= radius else 0;  D = distance from spectrum center",
    params=[Param("radius", "Cutoff radius", "slider", 40, 1, 400, 1)],
)
def lowpass(ctx: Context) -> Result:
    f = _fft(ctx.gray)
    mask = (_dist(ctx.gray.shape) <= ctx.i("radius", 40)).astype(np.float32)
    filt = f * mask
    return Result([("Filtered spectrum", _spectrum(filt)), ("Reconstructed", _reconstruct(filt))])


@operation(
    id="p5.highpass",
    project_order=ORDER, project=PROJECT,
    name="High-Pass Filter",
    description="Removes central low frequencies. Keeps edges and fine detail.",
    math="H(u,v) = 1 if D(u,v) > radius else 0",
    params=[Param("radius", "Cutoff radius", "slider", 40, 1, 400, 1)],
)
def highpass(ctx: Context) -> Result:
    f = _fft(ctx.gray)
    mask = (_dist(ctx.gray.shape) > ctx.i("radius", 40)).astype(np.float32)
    filt = f * mask
    return Result([("Filtered spectrum", _spectrum(filt)), ("Reconstructed", _reconstruct(filt))])


@operation(
    id="p5.bandpass",
    project_order=ORDER, project=PROJECT,
    name="Band-Pass Filter",
    description="Keeps a ring of frequencies between an inner and outer radius.",
    math="H(u,v) = 1 if r_inner <= D(u,v) <= r_outer else 0",
    params=[
        Param("r_inner", "Inner radius", "slider", 20, 0, 400, 1),
        Param("r_outer", "Outer radius", "slider", 80, 1, 400, 1),
    ],
)
def bandpass(ctx: Context) -> Result:
    f = _fft(ctx.gray)
    d = _dist(ctx.gray.shape)
    ri, ro = ctx.i("r_inner", 20), ctx.i("r_outer", 80)
    mask = ((d >= ri) & (d <= ro)).astype(np.float32)
    filt = f * mask
    return Result([("Filtered spectrum", _spectrum(filt)), ("Reconstructed", _reconstruct(filt))])
