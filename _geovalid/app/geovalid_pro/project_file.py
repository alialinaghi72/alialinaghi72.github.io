"""Project files and profile-held mappings (v2 brief F10).

Project file (`geovalid-project/1`, JSON): the input tables with their table type, enabled flag and column mapping, the
optional inputs (topography, licence, CRM certificates, laboratory and umpire files, previous version, accepted
snapshot, audit results), the rule profile (embedded) or a profile path, and the output settings. Paths are stored
relative to the project file when they sit below its folder, so a project folder can be moved or shared.

The rule profile can also carry the column mappings (`column_mappings`, by table name) and the hole-ID merge table
(`id_merge`); mappings in a profile are applied to tables of the same name whenever files are loaded, so a profile can
be reused on the next delivery of the same database.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from . import __version__
from .io.mapping import AnalyteColumn, TableMapping

PROJECT_FORMAT = "geovalid-project/1"
OPTIONAL = ("dem", "licence", "crm", "lab", "umpire", "baseline", "snapshot", "audit_results")


def mapping_to_dict(inp) -> dict:
    m = inp.mapping
    return {"kind": inp.kind, "enabled": bool(inp.enabled), "fields": {k: v for k, v in m.fields.items() if v},
            "analytes": [{"column": a.column, "analyte": a.analyte, "unit": a.unit, "qualifier": a.qualifier, "partial": bool(a.partial)}
                         for a in m.analytes],
            "depth_unit": getattr(m, "depth_unit", "m")}


def apply_mapping(inp, d: dict) -> list[str]:
    """Apply a stored mapping to a loaded table. Columns that no longer exist are skipped and named (never guessed)."""
    cols = set(inp.raw.df.columns)
    missing = []
    kind = d.get("kind", inp.kind)
    m = TableMapping(kind)
    from .io.mapping import FIELDS
    req, opt = FIELDS.get(kind, ([], []))
    for f in req + opt:
        m.fields[f] = None
    for f, c in (d.get("fields") or {}).items():
        if c in cols:
            m.fields[f] = c
            m.confidence[f] = 1.0
        else:
            missing.append(f"{f}→{c}")
    for a in d.get("analytes") or []:
        if a.get("column") in cols:
            m.analytes.append(AnalyteColumn(a["column"], a["analyte"], a.get("unit"), a.get("qualifier") or "", bool(a.get("partial"))))
        else:
            missing.append(str(a.get("column")))
    m.depth_unit = d.get("depth_unit", "m")
    inp.kind, inp.mapping = kind, m
    if "enabled" in d:
        inp.enabled = bool(d["enabled"])
    return missing


def apply_profile_mappings(inputs, params: dict) -> list[str]:
    """Column mappings stored in the profile, applied to the tables with the same name. Returns messages."""
    stored = params.get("column_mappings") or {}
    msgs = []
    for inp in inputs:
        d = stored.get(inp.name)
        if d:
            miss = apply_mapping(inp, d)
            msgs.append(f"{inp.name}: mapping from the profile" + (f" (columns not found: {', '.join(miss)})" if miss else ""))
    return msgs


def store_mappings(inputs, params: dict) -> None:
    params["column_mappings"] = {i.name: mapping_to_dict(i) for i in inputs}


def _rel(p: str | None, base: Path) -> str | None:
    if not p:
        return None
    try:
        rp = Path(p).resolve()
        return rp.relative_to(base).as_posix() if rp.is_relative_to(base) else str(rp)
    except (OSError, ValueError):
        return str(p)


def _abs(p: str | None, base: Path) -> str | None:
    if not p:
        return None
    q = Path(p)
    return str(q if q.is_absolute() else (base / q).resolve())


def save_project(path: str, inputs, paths: dict, params: dict, name: str, out: str | None = None, lang: str = "both",
                 embed_profile: bool = True, profile_path: str | None = None) -> dict:
    base = Path(path).resolve().parent
    doc = {"format": PROJECT_FORMAT, "software": f"GEOVALID PRO {__version__}",
           "saved_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "name": name,
           "inputs": [{"path": _rel(i.raw.source, base), "sheet": i.raw.sheet, "name": i.name, **mapping_to_dict(i)} for i in inputs],
           "optional": {k: _rel(paths.get(k), base) for k in OPTIONAL if paths.get(k)},
           "output": {"folder": _rel(out, base) if out else None, "lang": lang}}
    if embed_profile:
        from .core.registry import profile_hash
        body = {k: v for k, v in params.items() if k not in ("profile_format", "saved_utc", "profile_hash", "software")}
        doc["profile"] = body
        doc["profile_hash"] = profile_hash(body)
    elif profile_path:
        doc["profile_path"] = _rel(profile_path, base)
    Path(path).write_text(json.dumps(doc, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    return doc


def load_project(path: str) -> dict:
    p = Path(path).resolve()
    doc = json.loads(p.read_text(encoding="utf-8"))
    if doc.get("format") != PROJECT_FORMAT:
        raise ValueError(f"{p.name} is not a GEOVALID project ({PROJECT_FORMAT})")
    base = p.parent
    doc["_base"] = str(base)
    for i in doc.get("inputs", []):
        i["path"] = _abs(i["path"], base)
    doc["optional"] = {k: _abs(v, base) for k, v in (doc.get("optional") or {}).items()}
    if doc.get("profile_path"):
        doc["profile_path"] = _abs(doc["profile_path"], base)
    out = (doc.get("output") or {}).get("folder")
    if out:
        doc["output"]["folder"] = _abs(out, base)
    return doc


def project_inputs(doc: dict) -> tuple[list, list[str]]:
    """Load the project's tables (same file and sheet) and re-apply their stored table types and mappings."""
    from .engine import load_inputs
    inputs, msgs = [], []
    by_file = {}
    for i in doc.get("inputs", []):
        by_file.setdefault(i["path"], []).append(i)
    for path, items in by_file.items():
        if not path or not os.path.exists(path):
            msgs.append(f"input not found: {path}")
            continue
        loaded = load_inputs([path])
        for it in items:
            t = next((x for x in loaded if (x.raw.sheet or None) == (it.get("sheet") or None)), None) if it.get("sheet") else (loaded[0] if loaded else None)
            if t is None:
                msgs.append(f"sheet {it.get('sheet')} not found in {Path(path).name}")
                continue
            if it.get("name"):
                t.name = it["name"]
            miss = apply_mapping(t, it)
            if miss:
                msgs.append(f"{t.name}: columns not found: {', '.join(miss)}")
            inputs.append(t)
    return inputs, msgs


def build_spec(doc: dict, profile_override: str | None = None):
    """ProjectSpec, output folder and report language from a loaded project (headless runs)."""
    from .engine import ProjectSpec, _merge, default_params, load_folder, load_inputs, load_params
    if profile_override:
        params = load_params(profile_override)
    elif doc.get("profile"):
        params = _merge(default_params(), doc["profile"])
    else:
        params = load_params(doc.get("profile_path"))
    inputs, msgs = project_inputs(doc)
    o = doc.get("optional") or {}
    base = None
    if o.get("baseline"):
        if Path(o["baseline"]).is_dir():
            base, skipped = load_folder(o["baseline"])
            msgs += [f"baseline: skipped {m.splitlines()[0]}" for m in skipped]
        else:
            base = [t for t in load_inputs([o["baseline"]]) if t.kind != "ignore"]
    spec = ProjectSpec([i for i in inputs if i.enabled and i.kind != "ignore"], o.get("dem"), o.get("licence"), o.get("crm"),
                       profile_override or doc.get("profile_path"), doc.get("name") or "GEOVALID project", params,
                       lab_path=o.get("lab"), umpire_path=o.get("umpire"), audit_path=o.get("audit_results"),
                       baseline_inputs=base or None, snapshot_path=o.get("snapshot"))
    out = (doc.get("output") or {}).get("folder")
    return spec, out, (doc.get("output") or {}).get("lang") or "both", msgs
