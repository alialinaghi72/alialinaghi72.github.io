"""Spatial statistics: nearest-neighbour distances, Clark–Evans (Donnelly), point-in-polygon."""
from __future__ import annotations

import numpy as np


def nn_distances(xy: np.ndarray, k: int = 3) -> np.ndarray:
    from scipy.spatial import cKDTree
    if len(xy) < 2:
        return np.full((len(xy), k), np.nan)
    kk = min(k + 1, len(xy))
    d, _ = cKDTree(xy).query(xy, k=kk)
    out = np.full((len(xy), k), np.nan)
    out[:, : kk - 1] = d[:, 1:]
    return out


def clark_evans(xy: np.ndarray) -> dict:
    """R = mean NN / expected NN under CSR with Donnelly (1978) edge correction on the convex hull."""
    from scipy.spatial import ConvexHull
    n = len(xy)
    if n < 10:
        return {"n": n}
    hull = ConvexHull(xy)
    area, perim = hull.volume, hull.area
    r_obs = float(np.nanmean(nn_distances(xy, 1)[:, 0]))
    r_exp = 0.5 * np.sqrt(area / n) + (0.0514 + 0.041 / np.sqrt(n)) * perim / n
    return {"n": n, "R": r_obs / r_exp, "mean_nn": r_obs, "expected_nn": r_exp, "area_m2": area,
            "density_per_km2": n / area * 1e6 if area > 0 else np.nan}


def point_in_polygon(x, y, poly: np.ndarray) -> np.ndarray:
    from matplotlib.path import Path
    return Path(poly).contains_points(np.column_stack([x, y]))


def distance_to_polyline(x, y, poly: np.ndarray) -> np.ndarray:
    px, py = np.asarray(x, float)[:, None], np.asarray(y, float)[:, None]
    ax, ay, bx, by = poly[:-1, 0], poly[:-1, 1], poly[1:, 0], poly[1:, 1]
    dx, dy = bx - ax, by - ay
    t = np.clip(((px - ax) * dx + (py - ay) * dy) / np.maximum(dx * dx + dy * dy, 1e-12), 0, 1)
    return np.sqrt((px - (ax + t * dx)) ** 2 + (py - (ay + t * dy)) ** 2).min(axis=1)
