"""Project 6: Morphological Operations."""
import cv2
import numpy as np

from ..registry import Context, Param, Result, operation

PROJECT = "Morphology"
ORDER = 6

_SHAPES = {"rect": cv2.MORPH_RECT, "ellipse": cv2.MORPH_ELLIPSE, "cross": cv2.MORPH_CROSS}
_OPS = {
    "erode": cv2.MORPH_ERODE, "dilate": cv2.MORPH_DILATE,
    "open": cv2.MORPH_OPEN, "close": cv2.MORPH_CLOSE,
    "gradient": cv2.MORPH_GRADIENT, "tophat": cv2.MORPH_TOPHAT, "blackhat": cv2.MORPH_BLACKHAT,
}


def _binary(ctx: Context):
    ttype = cv2.THRESH_BINARY_INV if ctx.s("invert", "no") == "yes" else cv2.THRESH_BINARY
    _, b = cv2.threshold(ctx.gray, 0, 255, ttype + cv2.THRESH_OTSU)
    return b


def _kernel(ctx: Context):
    k = ctx.i("ksize", 5)
    if k < 1:
        k = 1
    return cv2.getStructuringElement(_SHAPES.get(ctx.s("shape", "rect"), cv2.MORPH_RECT), (k, k))


_PARAMS = [
    Param("invert", "Invert (white objects)", "select", "no", options=["no", "yes"],
          help="Use 'yes' for dark objects on a light background, e.g. text scans."),
    Param("shape", "Structuring element", "select", "ellipse", options=["rect", "ellipse", "cross"],
          help="Shape of the probe slid across the image. Rect treats all directions through its square corners, ellipse keeps boundaries rounder, cross only affects horizontal and vertical directions."),
    Param("ksize", "Element size", "slider", 5, 1, 31, 1,
          help="Size of the structuring element. Larger elements have a stronger effect, removing or filling bigger features and moving object boundaries further."),
    Param("iterations", "Iterations", "slider", 1, 1, 10, 1,
          help="How many times the operation is applied in sequence. More iterations behave like a larger structuring element."),
]


@operation(
    id="p6.morphology",
    project_order=ORDER, project=PROJECT,
    name="Morphological Operator",
    description=(
        "Thresholds the image to a binary mask (Otsu), then applies a morphological "
        "operator with a chosen structuring element shape, size, and iteration count."
    ),
    math=("Erosion:  A erode B  shrinks foreground\n"
          "Dilation: A dilate B expands foreground\n"
          "Opening = dilate(erode(A))   removes small specks\n"
          "Closing = erode(dilate(A))   fills small holes\n"
          "Gradient = dilation - erosion (outline)"),
    params=[
        Param("op", "Operation", "select", "open",
              options=["erode", "dilate", "open", "close", "gradient", "tophat", "blackhat"],
              help="Which morphological operation to apply. Erode shrinks white regions; dilate grows them; open removes small specks; close fills small holes; gradient outlines edges; tophat isolates small bright features; blackhat isolates small dark features."),
        *_PARAMS,
    ],
)
def morphology(ctx: Context) -> Result:
    binary = _binary(ctx)
    kernel = _kernel(ctx)
    iterations = ctx.i("iterations", 1)
    op = _OPS.get(ctx.s("op", "open"), cv2.MORPH_OPEN)
    if op == cv2.MORPH_ERODE:
        out = cv2.erode(binary, kernel, iterations=iterations)
    elif op == cv2.MORPH_DILATE:
        out = cv2.dilate(binary, kernel, iterations=iterations)
    else:
        out = cv2.morphologyEx(binary, op, kernel, iterations=iterations)
    return Result([("Binary", binary), (ctx.s("op", "open").capitalize(), out)])
