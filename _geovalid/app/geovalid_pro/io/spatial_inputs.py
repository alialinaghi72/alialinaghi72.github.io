"""Topography and licence-boundary entry points (kept for the engine and older callers).

`read_dem` reads every topography format of `io/topo.py` (grids, point clouds, contours, meshes); `read_polygon` every
boundary format of `io/boundary.py`."""
from __future__ import annotations

from .boundary import Boundary, read_boundary
from .topo import Surface, read_surface

Dem = Surface


def read_dem(path: str, fmt: str | None = None, max_dist: float | None = None) -> Surface:
    return read_surface(path, fmt, max_dist)


def read_polygon(path: str, fmt: str | None = None) -> Boundary:
    return read_boundary(path, fmt)
