"""Validation engine: inputs → canonical tables → derived products → rules → results. Sources are read-only."""
from __future__ import annotations

import copy
import json
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
from .core.fingerprint import dataset_hash, hole_hashes
from .core.issues import SEV_RANK, IssueLog, rules_meta
from .core.registry import aliases, category, is_enabled, profile_hash, standards_refs
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


PROFILE_FORMAT = "geovalid-profile/1"


def load_params(profile_path: str | None) -> dict:
    """Default profile merged with a user profile: JSON (v2, preferred) or YAML (v0.1–0.2 profiles keep working)."""
    p = default_params()
    if profile_path:
        text = Path(profile_path).read_text(encoding="utf-8")
        user = json.loads(text) if str(profile_path).lower().endswith(".json") else yaml.safe_load(text)
        user = {k: v for k, v in (user or {}).items() if k not in ("profile_format", "saved_utc", "profile_hash", "software")}
        p = _merge(p, user)
    return p


def save_profile(params: dict, path: str) -> str:
    """Write a versioned JSON rule profile (v2 brief F10): enabled rules, thresholds, severities, dictionaries, ID map."""
    from datetime import timezone
    body = {k: v for k, v in params.items() if k not in ("profile_format", "saved_utc", "profile_hash", "software")}
    doc = {"profile_format": PROFILE_FORMAT, "software": f"GEOVALID PRO {__version__}",
           "saved_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "profile_hash": profile_hash(body), **body}
    Path(path).write_text(json.dumps(doc, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    return doc["profile_hash"]


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
    lab_path: str | None = None            # laboratory / QA-QC file, GEOQAQC format (R1)
    umpire_path: str | None = None         # check / umpire laboratory file
    audit_path: str | None = None          # filled random-audit checklist to import (REC-07)


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
    """CRM certificates: CRM_ID, ELEMENT (column name or symbol), CERTIFIED, SD[, UNIT] (QAQC_FORMAT.md §5)."""
    from .io.lab import read_crm_certificates
    return read_crm_certificates(path)


def run(spec: ProjectSpec, progress=None) -> Result:
    progress = progress or (lambda pct, msg: None)
    run_id = str(uuid.uuid4())
    started = datetime.now().isoformat(timespec="seconds")
    params = spec.params or load_params(spec.profile_path)
    log = IssueLog(run_id, severity_overrides=params.get("severity_overrides"))
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
    from .io.lab import read_lab_file, read_umpire_file
    for attr, path, fn in (("lab", spec.lab_path, read_lab_file), ("umpire", spec.umpire_path, read_umpire_file)):
        if path:
            try:
                setattr(ctx, attr, fn(path, params))
            except Exception as e:
                res.errors.append(f"{attr} file: {e}")
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
        if not is_enabled(params, r.id):
            rows.append({"rule_id": r.id, "status": "DISABLED", "n_issues": 0, "note": "disabled in the profile"})
            continue
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
    matrix["category"] = matrix["rule_id"].map(category)
    matrix["aliases"] = matrix["rule_id"].map(lambda x: ", ".join(aliases(x)))
    matrix["standards"] = matrix["rule_id"].map(lambda x: "; ".join(standards_refs(x)))
    res.issues = _decorate(log.frame(), ctx)
    worst = res.issues.groupby("rule_id")["severity"].agg(lambda s: min(s, key=lambda v: SEV_RANK[v])) if not res.issues.empty else pd.Series(dtype=object)
    matrix["worst"] = matrix["rule_id"].map(worst)
    matrix["result"] = [_result(st, w) for st, w in zip(matrix["status"], matrix["worst"])]
    res.matrix = matrix
    progress(95, "fingerprints")
    _fingerprints(ctx, spec, params)
    from . import audit
    try:
        ctx.stats["random_audit"] = audit.summarise(ctx, params, spec.audit_path) if spec.audit_path else audit.pending(ctx, params)
    except Exception as e:  # reported, never silent
        res.errors.append(f"random audit: {e}")
        ctx.stats["random_audit"] = {"status": f"audit file not read: {e}"}
    res.finished = datetime.now().isoformat(timespec="seconds")
    progress(96, "done")
    return res


def _result(status: str, worst) -> str:
    """Per-rule outcome for the reports: PASS (ran, nothing above INFO), FAIL, or why it did not run."""
    if status != "RUN":
        return status
    if not isinstance(worst, str) or worst == "INFO":
        return "PASS"
    return "FAIL"


def _source_files(ctx: Ctx) -> dict:
    out = {}
    for t in ([ctx.collar] if ctx.collar else []) + ([ctx.survey] if ctx.survey else []) + ctx.tables:
        for part in str(t.name).split("+"):
            out.setdefault(part, Path(str(t.source)).name)
        out.setdefault(t.name, Path(str(t.source)).name)
    return out


def _decorate(iss: pd.DataFrame, ctx: Ctx) -> pd.DataFrame:
    """Add the v2 issue fields that follow from the rule and the table (brief §5.1)."""
    if iss.empty:
        for c in ("category", "rule_alias", "source_file", "standards_refs"):
            iss[c] = pd.Series(dtype=object)
        return iss
    src = _source_files(ctx)
    iss["category"] = iss["rule_id"].map(category)
    iss["rule_alias"] = iss["rule_id"].map(lambda r: ", ".join(aliases(r)))
    if "alias_hint" in iss:                      # an issue that answers one specific brief check of a multi-check rule
        iss["rule_alias"] = iss["alias_hint"].where(iss["alias_hint"].notna(), iss["rule_alias"])
        iss = iss.drop(columns="alias_hint")
    iss["source_file"] = iss["table"].map(lambda t: "; ".join(dict.fromkeys(src.get(p, "") for p in str(t).split("+") if src.get(p))) if isinstance(t, str) else None)
    iss["standards_refs"] = iss["rule_id"].map(lambda r: "; ".join(standards_refs(r)))
    return iss


def _fingerprints(ctx: Ctx, spec: ProjectSpec, params: dict) -> None:
    """v2 brief §5.5: file SHA-256, per-hole canonical hashes, dataset hash and profile hash."""
    ctx.stats["file_hashes"] = [{"file": Path(i.raw.source).name, "sheet": i.raw.sheet or "", "sha256": i.raw.sha256,
                                 "table": i.name, "kind": i.kind} for i in spec.inputs]
    for k, path in (("dem", spec.dem_path), ("licence", spec.licence_path), ("crm", spec.crm_path), ("lab", spec.lab_path),
                    ("umpire", spec.umpire_path)):
        if path and Path(path).is_file():
            ctx.stats["file_hashes"].append({"file": Path(path).name, "sheet": "", "sha256": sha256_of(path), "table": k, "kind": k})
    try:
        hh = hole_hashes(ctx)
    except Exception as e:     # fingerprints must never stop a validation; reported in the run messages
        hh = pd.DataFrame(columns=["hole_key", "hole_id", "hash"])
        ctx.stats["fingerprint_error"] = str(e)
    ctx.stats["hole_hashes"] = hh
    ctx.stats["dataset_hash"] = dataset_hash(hh)
    ctx.stats["profile_hash"] = profile_hash(params)


def _dip_convention(ctx: Ctx) -> None:
    """Brief §4.1: detect positive-down dips. Converted for desurvey, raw kept, reported for confirmation."""
    if ctx.survey is None:
        return
    s = ctx.survey.df
    sent = set(ctx.p("SUR-020").get("sentinels", []))
    d = s["dip"][s["dip"].notna() & ~s["dip"].isin(sent) & (s["dip"].abs() > 5) & (s["dip"].abs() <= 90)]
    conv = str(ctx.params.get("dip_convention", "auto")).lower()      # v2 SRV-03: user-set convention
    if conv == "negative_down":
        ctx.dip_convention = "NEGATIVE_DOWN_DECLARED"
        return
    if conv == "positive_down" or (conv == "auto" and len(d) >= 10 and (d > 0).mean() >= 0.95):
        s["dip_raw"] = s["dip"]
        s.loc[s["dip"].notna() & ~s["dip"].isin(sent), "dip"] = -s["dip"]
        ctx.dip_convention = "POSITIVE_DOWN_CONVERTED"
        if ctx.collar is not None and "dip" in ctx.collar.df:
            cd = ctx.collar.df["dip"].dropna()
            if len(cd) and (cd[cd.abs() > 5] > 0).mean() >= 0.95:
                ctx.collar.df["dip"] = -ctx.collar.df["dip"]
