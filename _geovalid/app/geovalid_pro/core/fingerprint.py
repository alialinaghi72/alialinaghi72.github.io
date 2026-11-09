"""Dataset fingerprints (v2 brief §5.5): per-hole canonical hashes and a dataset hash.

A hole's hash covers its sorted, normalised records in every table: collar, survey and each interval table (all mapped
fields, analyte values as received and attribute columns). Formatting differences that do not change values
(trailing zeros, column order, row order, case of the hole ID's separators) do not change the hash; any value change does.
Version comparison (P2) uses these hashes to skip unchanged holes.
"""
from __future__ import annotations

import hashlib

import numpy as np
import pandas as pd

from .normalise import hole_key

_SKIP = {"src_row", "length_m", "mid_m", "qc_class"}


def _fmt(s: pd.Series) -> pd.Series:
    if pd.api.types.is_numeric_dtype(s):
        v = s.astype(float)
        out = v.map(lambda x: "" if not np.isfinite(x) else f"{x:.6g}")
        return out
    return s.astype("string").fillna("").str.strip()


def _table_strings(name: str, df: pd.DataFrame, sort_cols: list[str]) -> pd.Series:
    cols = sorted(c for c in df.columns if c not in _SKIP and not c.endswith("_raw") and c != "hole_id")
    if df.empty:
        return pd.Series(dtype=object)
    key = df["hole_id"].map(hole_key)
    parts = [_fmt(df[c]) for c in cols]
    rec = parts[0].str.cat(parts[1:], sep="\x1f") if parts else pd.Series("", index=df.index)
    order = df.sort_values([c for c in sort_cols if c in df.columns] or ["hole_id"], kind="stable").index
    frame = pd.DataFrame({"k": key, "r": name + "\x1e" + "|".join(cols) + "\x1e" + rec}).loc[order]
    frame = frame[frame["k"].notna()]
    return frame.groupby("k", sort=False)["r"].agg("\x1d".join)


def hole_hashes(ctx) -> pd.DataFrame:
    """One row per hole key: hole_id (as in the collar when present) and SHA-256 of its records in all tables."""
    pieces = []
    if ctx.collar is not None:
        pieces.append(_table_strings("collar", ctx.collar.df, ["hole_id"]))
    if ctx.survey is not None:
        pieces.append(_table_strings("survey", ctx.survey.df, ["hole_id", "depth_m"]))
    for t in sorted(ctx.tables, key=lambda t: (t.kind, t.name)):
        df = t.df.copy()
        for a in t.analytes:
            pr = a.parsed
            df["an:" + a.column] = (pr["flag"].astype(str) + ":" + _fmt(pr["value"]) + ":" + _fmt(pr["dl"]) + ":"
                                    + pr["code"].astype("string").fillna(""))
        pieces.append(_table_strings(t.kind, df, ["hole_id", "from_m", "to_m", "depth_m"]))   # kind, not file name: renamed files keep their hashes
    if not pieces:
        return pd.DataFrame(columns=["hole_key", "hole_id", "hash"])
    allk = pd.concat(pieces, axis=1).fillna("")
    joined = allk.astype(str).agg("\x1c".join, axis=1)
    hashes = joined.map(lambda s: hashlib.sha256(s.encode("utf-8")).hexdigest())
    names = {}
    if ctx.collar is not None:
        for h in ctx.collar_df["hole_id"].dropna():
            names.setdefault(hole_key(h), h)
    out = pd.DataFrame({"hole_key": hashes.index, "hash": hashes.to_numpy()})
    out.insert(1, "hole_id", out["hole_key"].map(lambda k: names.get(k, k)))
    return out.sort_values("hole_key").reset_index(drop=True)


def dataset_hash(hh: pd.DataFrame) -> str:
    blob = "\n".join(f"{k}:{h}" for k, h in zip(hh["hole_key"], hh["hash"]))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()
