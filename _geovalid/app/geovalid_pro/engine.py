"""Validation engine: inputs → canonical tables → derived products → rules → results. Sources are read-only."""
from __future__ import annotations

import copy
import traceback
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from importlib import resources
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from . import __version__
from .core.context import Ctx
from .core.issues import IssueLog, rules_meta
from .core.normalise import header_key, parse_numbers
from .core.project import TableInput, build_canonical
from .io.mapping import propose_mapping, detect_kind
from .io.readers import read_file, sha256_of
from .io.spatial_inputs import read_dem, read_polygon
from .rules import REGISTRY
from .rules.qaqc import classify

IMPORT_RULES = ["IMP-003", "IMP-004", "IMP-005", "IMP-010", "IMP-014"]


def default_params() -> dict:
    raw = resources.files("geovalid_pro.resources").joinpath("default_profile.yaml").read_text(encoding="utf-8")
    return yaml.safe_load(raw)


def _merge(a: dict, b: dict) -> dict:
    out = copy.deepcopy(a)
    for k, v in (b or {}).items():
        out[k] = _merge(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else v
    return out


def load_params(profile_path: str | None) -> dict:
    p = default_params()
    if profile_path:
        p = _merge(p, yaml.safe_load(Path(profile_path).read_text(encoding="utf-8")) or {})
    return p


def load_inputs(paths: list[str]) -> list[TableInput]:
    """Read files, detect table types and propose mappings (the user may override both)."""
    out = []
    for path in paths:
        for raw in read_file(path):
            kind = detect_kind(raw.df, raw.name)
            out.append(TableInput(raw, kind, propose_mapping(raw.df, kind) if kind != "ignore" else propose_mapping(raw.df, "ignore")))
    names = {}
    for t in out:
        n = names.get(t.name, 0)
        names[t.name] = n + 1
        if n:
            t.name = f"{t.name}_{n + 1}"
    return out


@dataclass
class ProjectSpec:
    inputs: list[TableInput]
    dem_path: str | None = None
    licence_path: str | None = None
    crm_path: str | None = None
    profile_path: str | None = None
    project_name: str = "GEOVALID project"
    params: dict | None = None


@dataclass
class Result:
    spec: ProjectSpec
    ctx: Ctx
    issues: pd.DataFrame
    matrix: pd.DataFrame
    run_id: str
    started: str
    finished: str = ""
    errors: list[str] = field(default_factory=list)
    outputs: dict = field(default_factory=dict)


def _read_crm(path: str) -> pd.DataFrame:
    df = read_file(path)[0].df
    keys = {c: header_key(c) for c in df.columns}
    def pick(*cands):
        for c, k in keys.items():
            if any(k == x or k.startswith(x) for x in cands):
                return c
        return None
    c_id, c_el = pick("crm", "standard", "std", "crmid"), pick("analyte", "element", "el")
    c_v, c_sd = pick("certified", "expected", "value", "mean", "cert"), pick("sd", "std1", "stdev", "1sd", "sd1")
    if None in (c_id, c_el, c_v, c_sd):
        raise ValueError("CRM file needs columns: crm_id, analyte, certified, sd")
    return pd.DataFrame({"crm_id": df[c_id].str.strip(), "analyte": df[c_el].str.strip(),
                         "certified": parse_numbers(df[c_v])[0], "sd": parse_numbers(df[c_sd])[0]}).dropna()


def run(spec: ProjectSpec, progress=None) -> Result:
    progress = progress or (lambda pct, msg: None)
    run_id = str(uuid.uuid4())
    started = datetime.now().isoformat(timespec="seconds")
    params = spec.params or load_params(spec.profile_path)
    log = IssueLog(run_id)
    ctx = Ctx(params=params, log=log)
    res = Result(spec, ctx, pd.DataFrame(), pd.DataFrame(), run_id, started)
    progress(2, "building canonical tables")
    for inp in spec.inputs:
        if not inp.enabled or inp.kind == "ignore":
            continue
        canon = build_canonical(inp, log)
        if inp.kind in ("collar", "survey"):
            cur = getattr(ctx, inp.kind)
            if cur is None:
                setattr(ctx, inp.kind, canon)
            else:
                cur.df = pd.concat([cur.df, canon.df], ignore_index=False)
                cur.name = f"{cur.name}+{canon.name}"
        else:
            ctx.tables.append(canon)
    for t in ctx.by_kind("assay"):
        st = t.df["sample_type"] if "sample_type" in t.df else pd.Series(pd.NA, index=t.df.index)
        sid = t.df["sample_id"] if "sample_id" in t.df else None
        cls = classify(st, sid)
        if st.notna().any() or (cls != "ORIGINAL").any():
            t.df["qc_class"] = cls
    _dip_convention(ctx)
    progress(10, "reading spatial inputs")
    if spec.dem_path:
        try:
            ctx.dem = read_dem(spec.dem_path)
        except Exception as e:  # reported, never silent
            res.errors.append(f"DEM: {e}")
    if spec.licence_path:
        try:
            ctx.licence = read_polygon(spec.licence_path)
        except Exception as e:
            res.errors.append(f"Licence: {e}")
    if spec.crm_path:
        try:
            ctx.crm_values = _read_crm(spec.crm_path)
        except Exception as e:
            res.errors.append(f"CRM table: {e}")
    if ctx.dem is not None and ctx.has("collar"):
        c = ctx.collar_u
        zt = pd.Series(ctx.dem.sample(c["x"].to_numpy(float), c["y"].to_numpy(float)), index=c.index)
        ctx.stats["z_topo"] = zt
        ctx.stats["dz"] = c["z"] - zt
    progress(15, "desurveying holes")
    ctx.build_traces()
    meta = rules_meta()
    rows = []
    for rid in IMPORT_RULES:
        rows.append({"rule_id": rid, "status": "RUN", "n_issues": log.count(rid), "note": "import stage"})
    n = len(REGISTRY)
    for k, r in enumerate(REGISTRY):
        progress(15 + int(80 * k / n), f"{r.id}")
        missing = [x for x in r.needs if not ctx.has(x)]
        if missing:
            rows.append({"rule_id": r.id, "status": "NOT_APPLICABLE", "n_issues": 0, "note": "missing input: " + ", ".join(missing)})
            continue
        before = log.count(r.id)
        try:
            r.fn(ctx)
            rows.append({"rule_id": r.id, "status": "RUN", "n_issues": log.count(r.id) - before, "note": r.note})
        except Exception as e:
            tb = traceback.format_exc(limit=3)
            res.errors.append(f"{r.id}: {e}")
            rows.append({"rule_id": r.id, "status": "FAILED", "n_issues": log.count(r.id) - before, "note": f"{type(e).__name__}: {e}"})
            res.errors.append(tb)
    matrix = pd.DataFrame(rows)
    matrix["title_en"] = matrix["rule_id"].map(lambda x: meta.get(x, {}).get("title_en", ""))
    matrix["title_fa"] = matrix["rule_id"].map(lambda x: meta.get(x, {}).get("title_fa", ""))
    matrix["jorc"] = matrix["rule_id"].map(lambda x: meta.get(x, {}).get("jorc", ""))
    res.matrix = matrix
    res.issues = log.frame()
    res.finished = datetime.now().isoformat(timespec="seconds")
    progress(96, "done")
    return res


def _dip_convention(ctx: Ctx) -> None:
    """Brief §4.1: detect positive-down dips. Converted for desurvey, raw kept, reported for confirmation."""
    if ctx.survey is None:
        return
    s = ctx.survey.df
    sent = set(ctx.p("SUR-020").get("sentinels", []))
    d = s["dip"][s["dip"].notna() & ~s["dip"].isin(sent) & (s["dip"].abs() > 5) & (s["dip"].abs() <= 90)]
    if len(d) >= 10 and (d > 0).mean() >= 0.95:
        s["dip_raw"] = s["dip"]
        s.loc[s["dip"].notna() & ~s["dip"].isin(sent), "dip"] = -s["dip"]
        ctx.dip_convention = "POSITIVE_DOWN_CONVERTED"
        if ctx.collar is not None and "dip" in ctx.collar.df:
            cd = ctx.collar.df["dip"].dropna()
            if len(cd) and (cd[cd.abs() > 5] > 0).mean() >= 0.95:
                ctx.collar.df["dip"] = -ctx.collar.df["dip"]
