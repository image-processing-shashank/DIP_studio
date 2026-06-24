"""Scalable operation registry.

Each project registers operations with the @operation decorator. An operation
declares its parameters (sliders / selects), human-readable description, the
maths involved, and a function that produces a Result. The frontend renders all
controls from the serialized catalog, so adding a new project (7..20) only
requires adding a new module under operations/ and importing it.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Optional

import numpy as np

# Valid values for Operation.requires.
# "any"   – works on grayscale and color equally
# "color" – needs a true RGB source (e.g. channel separation is only meaningful on color)
# "gray"  – explicitly designed for single-channel input
REQUIRES_OPTIONS = ("any", "color", "gray")


@dataclass
class Param:
    name: str
    label: str
    type: str                      # "slider" | "select"
    default: Any
    min: Optional[float] = None
    max: Optional[float] = None
    step: Optional[float] = None
    options: Optional[list] = None  # for "select"
    help: str = ""

    def to_dict(self):
        return {
            "name": self.name, "label": self.label, "type": self.type,
            "default": self.default, "min": self.min, "max": self.max,
            "step": self.step, "options": self.options, "help": self.help,
        }


@dataclass
class Context:
    color: np.ndarray    # BGR uint8, HxWx3
    gray: np.ndarray     # uint8, HxW
    params: dict
    is_color: bool = True  # True when source had real color channels

    # Typed param accessors with safe defaults.
    def f(self, name, default):
        try:
            return float(self.params.get(name, default))
        except (TypeError, ValueError):
            return float(default)

    def i(self, name, default):
        try:
            return int(round(float(self.params.get(name, default))))
        except (TypeError, ValueError):
            return int(default)

    def s(self, name, default):
        v = self.params.get(name, default)
        return str(v) if v is not None else default


@dataclass
class Result:
    images: list           # list of (label, ndarray) where ndarray is gray 2D or RGB 3D
    metrics: dict = field(default_factory=dict)


@dataclass
class Operation:
    id: str
    project_order: int
    project: str
    name: str
    description: str
    math: str
    params: list
    func: Callable[[Context], Result]
    requires: str = "any"   # "any" | "color" | "gray"

    def to_dict(self):
        return {
            "id": self.id, "project": self.project, "name": self.name,
            "description": self.description, "math": self.math,
            "params": [p.to_dict() for p in self.params],
            "requires": self.requires,
        }

    def check_image_type(self, is_color: bool, mode: str):
        """Raise ValueError with a clear message if the image type is incompatible."""
        if self.requires == "color" and not is_color:
            raise ValueError(
                f"'{self.name}' requires a color (RGB) image, but the uploaded "
                f"image was detected as grayscale ({mode}). "
                f"Please upload an RGB image to use this operation."
            )
        if self.requires == "gray" and is_color:
            raise ValueError(
                f"'{self.name}' is designed for grayscale images, but the uploaded "
                f"image was detected as color ({mode}). "
                f"Results may not be meaningful on a color image."
            )


_REGISTRY: dict[str, Operation] = {}


def operation(*, id, project_order, project, name, description,
              math="", params=None, requires="any"):
    """Decorator registering an operation under a stable id."""
    assert requires in REQUIRES_OPTIONS, f"requires must be one of {REQUIRES_OPTIONS}"
    def wrap(func):
        if id in _REGISTRY:
            raise ValueError(f"Duplicate operation id: {id}")
        _REGISTRY[id] = Operation(
            id=id, project_order=project_order, project=project, name=name,
            description=description, math=math, params=params or [],
            func=func, requires=requires,
        )
        return func
    return wrap


def get_operation(op_id: str) -> Operation:
    if op_id not in _REGISTRY:
        raise KeyError(f"Unknown operation: {op_id}")
    return _REGISTRY[op_id]


def build_catalog() -> list:
    """Return operations grouped by project, ordered for the UI."""
    groups: dict[int, dict] = {}
    for op in _REGISTRY.values():
        g = groups.setdefault(op.project_order, {"order": op.project_order,
                                                 "project": op.project,
                                                 "operations": []})
        g["operations"].append(op.to_dict())
    ordered = [groups[k] for k in sorted(groups)]
    return ordered
