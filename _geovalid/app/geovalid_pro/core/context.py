"""Validation context: canonical tables, derived products (traces, ΔZ, method inference) and parameters."""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from ..analysis.desurvey import desurvey, stations_for_hole
from .issues import IssueLog
from .normalise import hole_key
from .project import Canon


@dataclass
class Ctx:
    params: dict
    log: IssueLog
    collar: Canon | None = None
    survey: Canon | None = None
    tables: list[Canon] = field(default_factory=list)       # interval and point tables
    dem: object | None = None
    licence: np.ndarray | None = None
    crm_values: pd.DataFrame | None = None
    traces: dict = field(default_factory=dict)               # hole_id -> DataFrame (MIN_CURV)
    traces_tan: dict = field(default_factory=dict)
    stats: dict = field(default_factory=dict)                # numbers and series for the report
    dip_convention: str = "NEGATIVE_DOWN"

    # ---- parameters --------------------------------------------------------------------------
    def p(self, rule_id: str) -> dict:
        return dict(self.params.get("rules", {}).get(rule_id, {}))

    @property
    def eps(self) -> float:
        return float(self.params.get("depth_eps_m", 0.001))

    def add(self, *a, **k):
        self.log.add(*a, **k)

    # ---- convenience -------------------------------------------------------------------------
    @property
    def collar_df(self) -> pd.DataFrame:
        return self.collar.df if self.collar is not None else pd.DataFrame()

    @property
    def collar_u(self) -> pd.DataFrame:
        c = self.collar_df
        if c.empty:
            return c
        return c[c["hole_id"].notna()].drop_duplicates("hole_id").set_index("hole_id", drop=False)

    @property
    def collar_ids(self) -> set:
        return set(self.collar_u.index) if self.collar is not None else set()

    def collar_keys(self) -> dict:
        return {hole_key(h): h for h in self.collar_ids}

    def by_kind(self, *kinds) -> list[Canon]:
        return [t for t in self.tables if t.kind in kinds]

    @property
    def interval_tables(self) -> list[Canon]:
        return [t for t in self.tables if t.is_interval]

    def has(self, need: str) -> bool:
        if need == "collar":
            return self.collar is not None and not self.collar_df.empty
        if need == "survey":
            return self.survey is not None and not self.survey.df.empty
        if need == "intervals":
            return bool(self.interval_tables)
        if need in ("assay", "lithology", "geotech", "density"):
            return bool(self.by_kind(need))
        if need == "logging":
            return any(self.by_kind(k) for k in ("lithology", "alteration", "weathering"))
        if need == "analytes":
            return any(t.analytes for t in self.tables)
        if need == "dem":
            return self.dem is not None
        if need == "licence":
            return self.licence is not None
        if need == "traces":
            return bool(self.traces)
        if need == "qaqc":
            return any(t.kind == "assay" and t.df["sample_type"].notna().any() for t in self.by_kind("assay")
                       if "sample_type" in t.df)
        if need == "crm_values":
            return self.crm_values is not None and not self.crm_values.empty
        return True

    def spatial_collars(self) -> tuple[pd.DataFrame, list]:
        """Collars usable for spatial statistics and maps: finite X/Y, not flagged by COL-006, inside a robust
        extent (median ± max(10·IQR, 5 km)). Returns (collars, excluded hole IDs) so exclusions are reported."""
        c = self.collar_u
        c = c[np.isfinite(c["x"]) & np.isfinite(c["y"])]
        bad = {r["hole_id"] for r in self.log.rows if r["rule_id"] == "COL-006" and r["hole_id"] is not None}
        keep = ~c.index.isin(bad)
        for f in ("x", "y"):
            v = c.loc[keep, f]
            if len(v) >= 4:
                q1, q3 = v.quantile(0.25), v.quantile(0.75)
                lim = max(10 * (q3 - q1), 5000.0)
                keep &= (c[f] - v.median()).abs() <= lim
        return c[keep], sorted(c.index[~keep])

    # ---- derived products ---------------------------------------------------------------------
    def build_traces(self) -> None:
        if self.collar is None:
            return
        c = self.collar_u
        sv = self.survey.df if self.survey is not None else pd.DataFrame(columns=["hole_id", "depth_m", "azimuth", "dip"])
        groups = {h: g for h, g in sv.groupby("hole_id", sort=False)} if not sv.empty else {}
        sentinels = set(self.p("SUR-020").get("sentinels", []))
        for h, row in c.iterrows():
            if not (np.isfinite(row.get("x", np.nan)) and np.isfinite(row.get("y", np.nan))):
                continue
            z0 = row.get("z", np.nan)
            z0 = z0 if np.isfinite(z0) else 0.0
            g = groups.get(h)
            if g is not None:
                d, a, p = g["depth_m"].to_numpy(float), g["azimuth"].to_numpy(float), g["dip"].to_numpy(float)
                bad = np.isin(p, list(sentinels)) | (np.abs(p) > 90) | (d < 0)
                d, a, p = d[~bad], a[~bad], p[~bad]
                a = np.where(np.isin(a, list(sentinels)), np.nan, a)
            else:
                d = a = p = np.array([])
            st = stations_for_hole(d, a, p, row.get("eoh_m"), row.get("azimuth"), row.get("dip"))
            self.traces[h] = desurvey(st, row["x"], row["y"], z0, "MIN_CURV")
            self.traces_tan[h] = desurvey(st, row["x"], row["y"], z0, "TAN")

    def midpoints(self, table: Canon) -> pd.DataFrame:
        """XYZ of interval mid-points (or point depths) from the minimum-curvature traces."""
        from ..analysis.desurvey import position_at
        df = table.df
        depth = (df["from_m"] + df["to_m"]) / 2 if "from_m" in df else df.get("depth_m")
        out = pd.DataFrame(index=df.index, columns=["x", "y", "z"], dtype=float)
        for h, idx in df.groupby("hole_id").groups.items():
            tr = self.traces.get(h)
            if tr is None:
                continue
            out.loc[idx, ["x", "y", "z"]] = position_at(tr, depth.loc[idx].to_numpy(float))
        return out
