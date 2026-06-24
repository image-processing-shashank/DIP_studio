"""Image input/output helpers.

Decoding and encoding rely only on OpenCV, which already supports PNG, JPEG,
and TIFF (the opencv wheels bundle libpng, libjpeg, and libtiff). No extra
imaging library is required.
"""
from __future__ import annotations

import base64
from dataclasses import dataclass

import cv2
import numpy as np

from . import config


# ---------------------------------------------------------------------------
# Image type detection
# ---------------------------------------------------------------------------

@dataclass
class ImageMeta:
    """Detected properties of the uploaded image before any processing."""
    mode: str          # "grayscale" | "rgb" | "rgba" | "16bit_gray" | "16bit_rgb"
    is_color: bool     # True if the source had meaningful color information
    channels: int      # channel count in the original file
    bit_depth: int     # 8 or 16
    width: int
    height: int


def _detect(raw: np.ndarray) -> ImageMeta:
    """Inspect the raw decoded array (before any normalization) and return metadata."""
    bit_depth = 16 if raw.dtype in (np.uint16, np.int16) else 8

    if raw.ndim == 2:
        return ImageMeta(
            mode="16bit_gray" if bit_depth == 16 else "grayscale",
            is_color=False, channels=1, bit_depth=bit_depth,
            width=raw.shape[1], height=raw.shape[0],
        )

    ch = raw.shape[2]
    if ch == 1:
        return ImageMeta(
            mode="grayscale", is_color=False, channels=1, bit_depth=bit_depth,
            width=raw.shape[1], height=raw.shape[0],
        )
    if ch == 4:
        return ImageMeta(
            mode="rgba", is_color=True, channels=4, bit_depth=bit_depth,
            width=raw.shape[1], height=raw.shape[0],
        )

    # 3-channel: could still be a grayscale image saved as RGB (R=G=B).
    # Sample up to 10 000 pixels to check.
    flat = raw.reshape(-1, 3)
    sample = flat[::max(1, len(flat) // 10_000)]
    is_true_color = bool(
        np.any(sample[:, 0].astype(np.int32) != sample[:, 1].astype(np.int32)) or
        np.any(sample[:, 1].astype(np.int32) != sample[:, 2].astype(np.int32))
    )
    mode = ("16bit_rgb" if bit_depth == 16 else "rgb") if is_true_color else "grayscale"
    return ImageMeta(
        mode=mode, is_color=is_true_color, channels=3, bit_depth=bit_depth,
        width=raw.shape[1], height=raw.shape[0],
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _limit(img: np.ndarray, max_dim: int) -> np.ndarray:
    if not max_dim:
        return img
    h, w = img.shape[:2]
    longest = max(h, w)
    if longest <= max_dim:
        return img
    scale = max_dim / float(longest)
    new_size = (max(1, int(w * scale)), max(1, int(h * scale)))
    return cv2.resize(img, new_size, interpolation=cv2.INTER_AREA)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def decode_image(data: bytes) -> tuple[np.ndarray, np.ndarray, ImageMeta]:
    """Decode image bytes into (color_bgr, gray, meta), both arrays uint8.

    Handles grayscale, RGB, RGBA, and non-8-bit (e.g. 16-bit TIFF) inputs.
    Returns images already limited to MAX_PROCESS_DIM on the longest edge.
    """
    arr = np.frombuffer(data, np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_UNCHANGED)
    if img is None:
        raise ValueError("Could not decode image. Supported formats: PNG, JPEG, TIFF, PPM.")

    meta = _detect(img)

    # Normalise bit depth to 8-bit for consistent processing.
    if img.dtype != np.uint8:
        img = cv2.normalize(img, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

    if img.ndim == 2:
        color = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    else:
        ch = img.shape[2]
        if ch == 4:
            color = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        elif ch == 1:
            color = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        else:
            color = img[:, :, :3]

    gray = cv2.cvtColor(color, cv2.COLOR_BGR2GRAY)

    color = _limit(color, config.MAX_PROCESS_DIM)
    gray  = _limit(gray,  config.MAX_PROCESS_DIM)
    return color, gray, meta


def to_png_data_uri(img: np.ndarray, max_dim: int | None = None) -> str:
    """Encode a 2D (gray) or 3D (RGB) array as a base64 PNG data URI."""
    a = img
    if a.dtype != np.uint8:
        a = cv2.normalize(a, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    if a.ndim == 3:
        a = cv2.cvtColor(a, cv2.COLOR_RGB2BGR)  # ops produce RGB; encoder wants BGR
    a = _limit(a, max_dim or config.MAX_DISPLAY_DIM)
    ok, buf = cv2.imencode(".png", a)
    if not ok:
        raise ValueError("Failed to encode result image.")
    return "data:image/png;base64," + base64.b64encode(buf).decode("ascii")
