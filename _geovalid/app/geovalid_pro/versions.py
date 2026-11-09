"""Version comparison and accepted snapshots (v2 brief F6, category I).

compare(old, new) — per-hole hashes first: unchanged holes are skipped and counted. For changed holes:
  collars     Δx, Δy, Δz, ΔEOH and other collar fields
  surveys     stations added / removed / modified, and the resulting move of the end-of-hole position (relative to the
              collar, so it isolates the survey change)
  intervals   three-stage diff per hole and table kind:
              (1) exact key match on From–To (within the depth tolerance) → value, code and metadata changes;
              (2) overlap clustering of the remaining intervals → re-segmented clusters (geometry changed);
              (3) what is left → true additions and removals.
Change classes: hole added / deleted, collar moved, survey changed, interval added / removed, re-segmented,
re-assayed (same geometry, value changed), code changed, metadata changed. Metal-weighted deltas Σ(length × grade) per
analyte, per hole and in total, with grade reconciliation for all holes and for the holes common to both versions.

Accepted snapshots: a JSON manifest (file hashes, per-hole hashes, profile hash, app version, reviewer, date, note and
the locked holes). VER-009 reports any change to a locked hole of the last accepted snapshot.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

from .core.normalise import hole_key

SNAPSHOT_FORMAT = "geovalid-snapshot/1"
CHANGE_COLUMNS = ["change_class", "table", "hole_id", "from_m", "to_m", "field", "old", "new", "delta", "detail"]
CATEGORICAL = ("lith_code", "alt_type", "weathering", "sample_type", "drill_method", "campaign", "collar_survey_method")
META_SKIP = {"src_row", "length_m", "mid_m", "qc_class", "hole_id", "from_m", "to_m"}


def _qc_free(df: pd.DataFrame) -> pd.DataFrame:
    from .rules.interval import QC_TYPES
    if "qc_class" in df:
        df = df[~df["qc_class"].isin(QC_TYPES)]
    return df[df["hole_id"].notna() & df["from_m"].notna() & df["to_m"].notna()]


def _vals(t, idx) -> pd.DataFrame:
    """Analyte values of rows `idx` as (flag, value, dl, code) strings, one column per analyte (normalised name)."""
    out = pd.DataFrame(index=idx)
    for a in t.analytes:
        p = a.parsed.loc[idx]
        name = a.analyte + (f" {a.qualifier}" if a.qualifier else "")
        out[name] = (p["flag"].astype(str) + "|" + p["value"].map(lambda v: "" if pd.isna(v) else f"{v:.10g}") + "|"
                     + p["dl"].map(lambda v: "" if pd.isna(v) else f"{v:.10g}") + "|" + p["code"].astype("string").fillna(""))
        out["~" + name] = p["value_policy"].astype(float)
        out["@" + name] = a.unit
    return out


def _txt(v) -> str:
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return ""
    s = str(v)
    return s.split("|")[0] if False else s


def _fmt_assay(s: str) -> str:
    if not isinstance(s, str) or "|" not in s:
        return "" if s is None else str(s)
    flag, v, dl, code = (s.split("|") + ["", "", "", ""])[:4]
    return {"VAL": v, "ODL": f">{v}", "BDL": f"<{dl}", "NA": ""}.get(flag, code or flag)


def _tables_by_kind(ctx) -> dict:
    out = {}
    for t in ctx.tables:
        if t.is_interval:
            out.setdefault(t.kind, []).append(t)
    return out


def _interval_frame(tabs) -> pd.DataFrame:
    """All rows of the tables of one kind, routine only, with analyte strings and the other fields."""
    parts = []
    for t in tabs:
        df = _qc_free(t.df)
        if df.empty:
            continue
        d = df.copy()
        d["_table"] = t.name
        v = _vals(t, df.index)
        d = pd.concat([d, v], axis=1)
        parts.append(d.reset_index(drop=True))
    return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()


def _three_stage(o: pd.DataFrame, n: pd.DataFrame, eps: float):
    """Per hole: exact pairs, overlap clusters and leftovers (indices into o and n)."""
    pairs, clusters, removed, added = [], [], [], []
    ko = list(zip(np.round(o["from_m"] / eps).astype(np.int64), np.round(o["to_m"] / eps).astype(np.int64)))
    kn = list(zip(np.round(n["from_m"] / eps).astype(np.int64), np.round(n["to_m"] / eps).astype(np.int64)))
    pool = {}
    for i, k in zip(o.index, ko):
        pool.setdefault(k, []).append(i)
    rest_n = []
    for j, k in zip(n.index, kn):
        if pool.get(k):
            pairs.append((pool[k].pop(0), j))
        else:
            rest_n.append(j)
    rest_o = [i for lst in pool.values() for i in lst]
    if rest_o and rest_n:
        # stage 2: union-find over old–new overlaps
        parent = {("o", i): ("o", i) for i in rest_o} | {("n", j): ("n", j) for j in rest_n}

        def find(a):
            while parent[a] != a:
                parent[a] = parent[parent[a]]
                a = parent[a]
            return a
        of, ot = o.loc[rest_o, "from_m"].to_numpy(float), o.loc[rest_o, "to_m"].to_numpy(float)
        for j in rest_n:
            f, t = float(n.at[j, "from_m"]), float(n.at[j, "to_m"])
            hit = np.nonzero((np.minimum(ot, t) - np.maximum(of, f)) > eps)[0]
            for h in hit:
                ra, rb = find(("o", rest_o[h])), find(("n", j))
                if ra != rb:
                    parent[ra] = rb
        comp = {}
        for a in parent:
            comp.setdefault(find(a), []).append(a)
        for members in comp.values():
            oi = [i for s, i in members if s == "o"]
            nj = [j for s, j in members if s == "n"]
            if oi and nj:
                clusters.append((oi, nj))
            elif oi:
                removed += oi
            else:
                added += nj
    else:
        removed, added = rest_o, rest_n
    return pairs, clusters, removed, added


def compare(old, new, params: dict | None = None) -> dict:
    """Full comparison of two canonical datasets (Ctx). Returns summary, change log and metal tables."""
    from .core.fingerprint import hole_hashes
    params = params or {}
    p = (params.get("rules") or {}).get("VER-002", {})
    tol_xy, tol_z, tol_eoh = float(p.get("tol_xy_m", 0.05)), float(p.get("tol_z_m", 0.05)), float(p.get("tol_eoh_m", 0.01))
    eps = float(params.get("depth_eps_m", 0.001))
    ho, hn = hole_hashes(old), hole_hashes(new)
    mo, mn = dict(zip(ho["hole_key"], ho["hash"])), dict(zip(hn["hole_key"], hn["hash"]))
    name_o, name_n = dict(zip(ho["hole_key"], ho["hole_id"])), dict(zip(hn["hole_key"], hn["hole_id"]))
    added = sorted(set(mn) - set(mo))
    removed = sorted(set(mo) - set(mn))
    common = sorted(set(mo) & set(mn))
    unchanged = {k for k in common if mo[k] == mn[k]}
    changed = [k for k in common if k not in unchanged]
    log = []

    def add(cls, table, k, fm=None, to=None, field=None, ov=None, nv=None, delta=None, detail=None):
        log.append({"change_class": cls, "table": table, "hole_id": name_n.get(k, name_o.get(k, k)), "from_m": fm, "to_m": to,
                    "field": field, "old": ov, "new": nv, "delta": delta, "detail": detail})

    for k in added:
        add("hole added", "", k)
    for k in removed:
        add("hole deleted", "", k)
    chg = set(changed)
    # ---- collars
    def _ck(ctx):                    # one collar per hole key (duplicates are COL-001's business)
        if ctx.collar is None:
            return pd.DataFrame()
        d = ctx.collar_u.assign(_k=lambda d: d["hole_id"].map(hole_key))
        return d[~d["_k"].duplicated()].set_index("_k")
    co, cn = _ck(old), _ck(new)
    moves = []
    for k in chg:
        if k not in co.index or k not in cn.index:
            continue
        a, b = co.loc[k], cn.loc[k]
        dxyz = [float(b[c] - a[c]) if c in b and c in a and pd.notna(a[c]) and pd.notna(b[c]) else 0.0 for c in ("x", "y", "z")]
        if abs(dxyz[0]) > tol_xy or abs(dxyz[1]) > tol_xy or abs(dxyz[2]) > tol_z:
            d = float(np.sqrt(sum(v * v for v in dxyz)))
            add("collar moved", new.collar.name, k, field="x,y,z", ov=f"{a['x']:.3f}, {a['y']:.3f}, {a['z']:.3f}",
                nv=f"{b['x']:.3f}, {b['y']:.3f}, {b['z']:.3f}", delta=round(d, 3), detail=f"dx {dxyz[0]:+.3f}, dy {dxyz[1]:+.3f}, dz {dxyz[2]:+.3f}")
            moves.append((k, *dxyz))
        for c in sorted(c for c in set(a.index) & set(b.index) - {"x", "y", "z", "src_row", "hole_id"} if not str(c).endswith("_raw")):
            av, bv = a[c], b[c]
            if (pd.isna(av) and pd.isna(bv)) or (isinstance(av, float) and isinstance(bv, float) and abs(av - bv) <= (tol_eoh if c == "eoh_m" else 1e-9)):
                continue
            if str(av) != str(bv):
                cls = "collar moved" if c == "eoh_m" else ("code changed" if c in CATEGORICAL else "metadata changed")
                add(cls, new.collar.name, k, field=c, ov=_txt(av), nv=_txt(bv),
                    delta=round(float(bv) - float(av), 4) if c == "eoh_m" and pd.notna(av) and pd.notna(bv) else None)
    # ---- surveys
    so = old.survey.df if old.survey is not None else pd.DataFrame(columns=["hole_id", "depth_m"])
    sn = new.survey.df if new.survey is not None else pd.DataFrame(columns=["hole_id", "depth_m"])
    so_g = {kk: g for kk, g in so.groupby(so["hole_id"].map(hole_key))} if not so.empty else {}
    sn_g = {kk: g for kk, g in sn.groupby(sn["hole_id"].map(hole_key))} if not sn.empty else {}
    eoh_moves = {}
    for k in chg:
        a, b = so_g.get(k), sn_g.get(k)
        if a is None and b is None:
            continue
        fa = _stations(a)
        fb = _stations(b)
        if fa == fb:
            continue
        da, db = set(fa), set(fb)
        mod = sorted(d for d in da & db if fa[d] != fb[d])
        dpos = _eoh_shift(old, new, name_o.get(k), name_n.get(k))
        eoh_moves[k] = dpos
        add("survey changed", new.survey.name if new.survey is not None else "survey", k, field="stations",
            ov=f"{len(fa)} stations", nv=f"{len(fb)} stations", delta=round(dpos, 3) if dpos is not None else None,
            detail=f"added {len(db - da)}, removed {len(da - db)}, modified {len(mod)}" + (f"; EOH position moves {dpos:.2f} m" if dpos is not None else ""))
    # ---- intervals
    to_, tn = _tables_by_kind(old), _tables_by_kind(new)
    metal_rows, hole_metal = [], []
    for kind in sorted(set(to_) | set(tn)):
        fo, fn = _interval_frame(to_.get(kind, [])), _interval_frame(tn.get(kind, []))
        if fo.empty and fn.empty:
            continue
        tname = (tn.get(kind) or to_.get(kind))[0].name
        fo = fo.assign(_k=fo["hole_id"].map(hole_key)) if not fo.empty else fo
        fn = fn.assign(_k=fn["hole_id"].map(hole_key)) if not fn.empty else fn
        an_cols = sorted({c[1:] for c in list(fo.columns) + list(fn.columns) if isinstance(c, str) and c.startswith("~")})
        fields = sorted((set(fo.columns) | set(fn.columns)) - META_SKIP - {"_k", "_table"} - {c for c in set(fo.columns) | set(fn.columns)
                                                                                          if isinstance(c, str) and c[:1] in "~@"} - set(an_cols)
                        - {c for c in set(fo.columns) | set(fn.columns) if str(c).endswith("_raw")})
        go = {kk: g for kk, g in fo.groupby("_k")} if not fo.empty else {}
        gn = {kk: g for kk, g in fn.groupby("_k")} if not fn.empty else {}
        for k in chg:
            o, n = go.get(k, pd.DataFrame()), gn.get(k, pd.DataFrame())
            if o.empty and n.empty:
                continue
            if o.empty or n.empty:
                for idx in (n.index if o.empty else o.index):
                    r = (n if o.empty else o).loc[idx]
                    add("interval added" if o.empty else "interval removed", tname, k, r["from_m"], r["to_m"])
                continue
            pairs, clusters, rem, addn = _three_stage(o, n, eps)
            for i, j in pairs:
                ro, rn = o.loc[i], n.loc[j]
                for c in an_cols:
                    a, b = ro.get(c), rn.get(c)
                    if isinstance(a, str) and isinstance(b, str) and a != b:
                        va, vb = ro.get("~" + c), rn.get("~" + c)
                        dl = float(vb) - float(va) if pd.notna(va) and pd.notna(vb) else None
                        add("re-assayed", tname, k, rn["from_m"], rn["to_m"], c, _fmt_assay(a), _fmt_assay(b), round(dl, 6) if dl is not None else None)
                for c in fields:
                    a, b = ro.get(c), rn.get(c)
                    if (a is None or (not isinstance(a, str) and pd.isna(a))) and (b is None or (not isinstance(b, str) and pd.isna(b))):
                        continue
                    if isinstance(a, float) and isinstance(b, float) and abs(a - b) <= 1e-9:
                        continue
                    if str(a) != str(b):
                        cls = "code changed" if c in CATEGORICAL else ("re-assayed" if kind in ("geotech", "density") and isinstance(b, (int, float)) else "metadata changed")
                        add(cls, tname, k, rn["from_m"], rn["to_m"], c, _txt(a), _txt(b))
            for oi, nj in clusters:
                f0 = float(min(o.loc[oi, "from_m"].min(), n.loc[nj, "from_m"].min()))
                t0 = float(max(o.loc[oi, "to_m"].max(), n.loc[nj, "to_m"].max()))
                add("re-segmented", tname, k, f0, t0, detail=f"{len(oi)} interval(s) → {len(nj)} interval(s)")
            for i in rem:
                add("interval removed", tname, k, o.at[i, "from_m"], o.at[i, "to_m"])
            for j in addn:
                add("interval added", tname, k, n.at[j, "from_m"], n.at[j, "to_m"])
        # metal and grade reconciliation (all holes; common holes)
        if kind == "assay" and an_cols:
            common_keys = set(common)
            for c in an_cols:
                lo = (fo["to_m"] - fo["from_m"]) if not fo.empty else pd.Series(dtype=float)
                ln = (fn["to_m"] - fn["from_m"]) if not fn.empty else pd.Series(dtype=float)
                vo = fo["~" + c] if "~" + c in fo else pd.Series(np.nan, index=fo.index)
                vn = fn["~" + c] if "~" + c in fn else pd.Series(np.nan, index=fn.index)
                unit = next((u for u in list(fn.get("@" + c, pd.Series(dtype=object)).dropna()[:1]) + list(fo.get("@" + c, pd.Series(dtype=object)).dropna()[:1])), "")
                for scope, mo_, mn_ in (("all holes", pd.Series(True, index=fo.index), pd.Series(True, index=fn.index)),
                                        ("common holes", fo["_k"].isin(common_keys) if not fo.empty else pd.Series(dtype=bool),
                                         fn["_k"].isin(common_keys) if not fn.empty else pd.Series(dtype=bool))):
                    okO, okN = mo_ & vo.notna(), mn_ & vn.notna()
                    mO, mN = float((lo[okO] * vo[okO]).sum()), float((ln[okN] * vn[okN]).sum())
                    LO, LN = float(lo[okO].sum()), float(ln[okN].sum())
                    metal_rows.append({"analyte": c, "unit": unit, "scope": scope, "old_metres": round(LO, 3), "new_metres": round(LN, 3),
                                       "old_metal": mO, "new_metal": mN, "delta_metal": mN - mO,
                                       "delta_pct": 100 * (mN - mO) / mO if mO else None,
                                       "old_grade": mO / LO if LO else None, "new_grade": mN / LN if LN else None})
                if not fo.empty or not fn.empty:
                    a1 = (lo * vo).groupby(fo["_k"]).sum() if not fo.empty else pd.Series(dtype=float)
                    a2 = (ln * vn).groupby(fn["_k"]).sum() if not fn.empty else pd.Series(dtype=float)
                    both = pd.concat([a1.rename("old"), a2.rename("new")], axis=1).fillna(0.0)
                    both = both[(both["old"] - both["new"]).abs() > 1e-9]
                    for kk, r in both.iterrows():
                        hole_metal.append({"hole_id": name_n.get(kk, name_o.get(kk, kk)), "analyte": c, "unit": unit, "old_metal": r["old"],
                                           "new_metal": r["new"], "delta_metal": r["new"] - r["old"]})
    changes = pd.DataFrame(log, columns=CHANGE_COLUMNS)
    classes = changes["change_class"].value_counts().to_dict() if not changes.empty else {}
    summary = {
        "status": "run",
        "holes": {"baseline": len(mo), "current": len(mn), "added": len(added), "deleted": len(removed), "common": len(common),
                  "unchanged": len(unchanged), "changed": len(changed)},
        "added_holes": [name_n[k] for k in added][:200], "deleted_holes": [name_o[k] for k in removed][:200],
        "changed_holes": [name_n.get(k, k) for k in changed][:500],
        "change_classes": {k: int(v) for k, v in classes.items()},
        "metal": [{k: (round(v, 6) if isinstance(v, float) else v) for k, v in r.items()} for r in metal_rows],
    }
    return {"summary": summary, "changes": changes, "metal": pd.DataFrame(metal_rows), "metal_by_hole": pd.DataFrame(hole_metal),
            "collar_moves": moves, "eoh_moves": eoh_moves, "hash_changed": changed, "added": added, "removed": removed,
            "names_old": name_o, "names_new": name_n}


def _stations(g) -> dict:
    if g is None or g.empty:
        return {}
    out = {}
    for r in g.itertuples():
        d = round(float(r.depth_m), 3) if pd.notna(r.depth_m) else None
        out[d] = tuple(None if pd.isna(getattr(r, c, np.nan)) else round(float(getattr(r, c)), 4) for c in ("azimuth", "dip"))
    return out


def _eoh_shift(old, new, ho, hn) -> float | None:
    """Move of the end-of-hole position relative to the collar (survey effect only)."""
    to, tn = old.traces.get(ho), new.traces.get(hn)
    if to is None or tn is None or not len(to) or not len(tn):
        return None
    a = to[["x", "y", "z"]].to_numpy(float)
    b = tn[["x", "y", "z"]].to_numpy(float)
    ra, rb = a[-1] - a[0], b[-1] - b[0]
    return float(np.linalg.norm(rb - ra))


# ---- accepted snapshots ----------------------------------------------------------------------------------------------
def accept(res, path: str, reviewer: str, note: str = "", lock: str | list = "all") -> dict:
    """Write an accepted-snapshot manifest for the validated dataset of `res` (JSON). `lock` = "all", "none" or a list
    of hole IDs; locked holes are those VER-009 protects."""
    from . import __version__
    ctx = res.ctx
    hh = ctx.stats.get("hole_hashes")
    if hh is None or hh.empty:
        raise ValueError("no per-hole hashes: validate the dataset first")
    if lock == "all":
        locked = list(hh["hole_key"])
    elif lock in ("none", None):
        locked = []
    else:
        keys = {hole_key(h) for h in lock}
        locked = [k for k in hh["hole_key"] if k in keys]
    m = {"format": SNAPSHOT_FORMAT, "accepted_at": datetime.now().isoformat(timespec="seconds"), "reviewer": reviewer, "note": note,
         "app_version": __version__, "project": res.spec.project_name, "run_id": res.run_id,
         "dataset_hash": ctx.stats.get("dataset_hash"), "profile_hash": ctx.stats.get("profile_hash"),
         "file_hashes": ctx.stats.get("file_hashes", []),
         "hole_hashes": {k: {"hole_id": h, "hash": s} for k, h, s in zip(hh["hole_key"], hh["hole_id"], hh["hash"])},
         "locked_holes": locked}
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(m, ensure_ascii=False, indent=1), encoding="utf-8")
    return m


def load_snapshot(path: str) -> dict:
    """A manifest file, or a folder of manifests (the latest accepted one is used)."""
    p = Path(path)
    files = sorted(p.glob("*.json")) if p.is_dir() else [p]
    best = None
    for f in files:
        try:
            m = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if m.get("format") != SNAPSHOT_FORMAT:
            continue
        m["_file"] = f.name
        if best is None or str(m.get("accepted_at")) > str(best.get("accepted_at")):
            best = m
    if best is None:
        raise ValueError(f"{p.name}: no accepted-snapshot manifest ({SNAPSHOT_FORMAT}) found")
    return best
