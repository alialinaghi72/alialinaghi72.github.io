"""Command line and headless mode (01 §11; v2 brief F10).

  GEOVALID.exe --cli --project project.json [--profile my.json] [--out folder]     headless batch run of a saved project
  GEOVALID.exe run --project project.json [--profile my.json] [--out folder] [--lang fa|en|both]
  GEOVALID.exe run --files collar.csv survey.csv assay.xlsx [--dem dem.asc] [--licence lic.csv] [--crm crm.csv]
                   [--lab lab.csv] [--umpire umpire.csv] [--audit-export checklist.xlsx] [--audit-results filled.xlsx]
                   [--baseline old/*.csv] [--snapshot accepted.json] [--accept-snapshot out.json --reviewer NAME --note TEXT --lock all]
                   [--profile my.json|my.yaml] [--codes codes.csv] [--out folder] [--lang fa|en|both] [--name "Project"]
  GEOVALID.exe run --sample [--out folder]          validate the bundled synthetic database
  GEOVALID.exe sample --out folder [--clean]        write the synthetic database (with or without injected errors)

Exit codes: 0 no Major/Critical (ERROR/CRITICAL), 1 Major present, 2 Critical present, 3 run failure.
Every run writes a log file: GEOVALID_PRO/logs/geovalid_<time>.log in the user folder, copied into the run's output
folder (a windowed exe has no console, so the log is the record of a headless run).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__


def _sample_dir(base: str | None, clean: bool = False) -> Path:
    from . import synth
    d = Path(base or Path.home() / "GEOVALID_PRO") / ("sample_clean" if clean else "sample_data")
    synth.generate(str(d), inject=not clean)
    return d


class _Log:
    """Messages to the console (when there is one) and always to a log file."""

    def __init__(self):
        from datetime import datetime
        d = Path.home() / "GEOVALID_PRO" / "logs"
        d.mkdir(parents=True, exist_ok=True)
        self.path = d / f"geovalid_{datetime.now():%Y%m%dT%H%M%S}.log"
        self.f = open(self.path, "w", encoding="utf-8")
        self.write(f"GEOVALID PRO {__version__} — {datetime.now().isoformat(timespec='seconds')}")
        self.write("command: " + " ".join(sys.argv))

    def write(self, msg: str, err: bool = False) -> None:
        self.f.write(msg.rstrip("\n") + "\n")
        self.f.flush()
        stream = sys.stderr if err else sys.stdout
        if stream is not None:
            try:
                print(msg, file=stream, flush=True)
            except (OSError, ValueError):
                pass

    def progress(self, p: int, m: str) -> None:
        self.f.write(f"[{p:3d}%] {m}\n")
        if sys.stdout is not None:
            try:
                print(f"\r  [{p:3d}%] {m:<30}", end="", flush=True)
            except (OSError, ValueError):
                pass

    def close(self, run_dir=None) -> None:
        self.f.close()
        if run_dir:
            import shutil
            try:
                shutil.copy(self.path, Path(run_dir) / "geovalid_run.log")
            except OSError:
                pass


def _spec_from_args(a, log: _Log):
    from .engine import ProjectSpec, load_folder, load_inputs, load_params
    from .project_file import apply_profile_mappings
    from .synth import SAMPLE_TABLES
    if a.sample:
        d = _sample_dir(None)
        files = [str(d / f"{n}.csv") for n in SAMPLE_TABLES]
        a.dem, a.licence, a.crm = a.dem or str(d / "dem.asc"), a.licence or str(d / "licence.csv"), a.crm or str(d / "crm_standards.csv")
        from . import synth_lab
        lab = synth_lab.from_database(str(d))          # GEOQAQC laboratory and umpire files for the sample
        a.lab, a.umpire = a.lab or lab["lab"], a.umpire or lab["umpire"]
        if not a.baseline:
            a.baseline = [str(_sample_dir(None, clean=True))]   # the clean twin stands in for the previous version
    else:
        files = a.files or []
    if not files:
        raise SystemExit("no input files (use --project, --files or --sample)")
    inputs = load_inputs(files)
    params = load_params(a.profile)
    for m in apply_profile_mappings(inputs, params):
        log.write(f"  {m}")
    base = None
    if a.baseline:
        if len(a.baseline) == 1 and Path(a.baseline[0]).is_dir():
            base, skipped = load_folder(a.baseline[0])
            for m in skipped:
                log.write(f"  baseline: skipped {m.splitlines()[0]}", err=True)
        else:
            base = [t for t in load_inputs(a.baseline) if t.kind != "ignore"]
    spec = ProjectSpec([t for t in inputs if t.kind != "ignore"], a.dem, a.licence, a.crm, a.profile, a.name, params,
                       lab_path=a.lab, umpire_path=a.umpire, audit_path=a.audit_results, baseline_inputs=base, snapshot_path=a.snapshot)
    return spec, inputs


def cmd_run(a) -> int:
    from .engine import run
    from .io.writers import write_outputs
    log = _Log()
    run_dir = None
    try:
        if a.project:
            from .project_file import build_spec, load_project
            doc = load_project(a.project)
            spec, out_p, lang_p, msgs = build_spec(doc, a.profile)
            for m in msgs:
                log.write(f"  project: {m}", err=True)
            inputs = spec.inputs
            out_dir = a.out or out_p or str(Path.home() / "GEOVALID_PRO" / "output")
            lang = a.lang or lang_p
            log.write(f"  project: {a.project} ({doc.get('name')})")
        else:
            spec, inputs = _spec_from_args(a, log)
            out_dir = a.out or str(Path.home() / "GEOVALID_PRO" / "output")
            lang = a.lang or "fa"
        params = spec.params
        if getattr(a, "codes", None):
            from .io.codes import read_code_dictionary
            for k, v in read_code_dictionary(a.codes).items():
                params.setdefault("code_dictionaries", {})[k] = sorted(set(params.get("code_dictionaries", {}).get(k, [])) | set(v))
        if a.topo_format:
            params.setdefault("topography", {})["format"] = a.topo_format
        for t in inputs:
            log.write(f"  {t.name:<28} {t.kind:<11} {len(t.raw.df):>8} rows")
        if a.save_project:
            from .project_file import save_project
            paths = {"dem": spec.dem_path, "licence": spec.licence_path, "crm": spec.crm_path, "lab": spec.lab_path,
                     "umpire": spec.umpire_path, "snapshot": spec.snapshot_path, "audit_results": spec.audit_path,
                     "baseline": a.baseline[0] if getattr(a, "baseline", None) and len(a.baseline) == 1 else None}
            save_project(a.save_project, inputs, paths, params, spec.project_name, out_dir, lang)
            log.write(f"  project saved: {a.save_project}")
        res = run(spec, log.progress)
        out = write_outputs(res, out_dir, lang)
        run_dir = out.get("folder")
        if a.apply_fixes:
            from .core import fixes
            import pandas as pd
            classes = [c.strip().upper() for c in a.apply_fixes.split(",") if c.strip()]
            idm = pd.DataFrame(params.get("id_merge") or [], columns=["raw_id", "target_id", "approved"])
            r = fixes.apply_fixes(res, classes, str(Path(run_dir) / "corrected"), idm, a.reviewer)
            out["fixes"] = f"{Path(run_dir) / 'corrected'} ({r['n']} changes, fix log {r['fix_log']})"
        if a.accept_snapshot:
            from .versions import accept
            lock = "all" if a.lock in (None, "all") else ("none" if a.lock == "none" else [h.strip() for h in a.lock.split(",") if h.strip()])
            m = accept(res, a.accept_snapshot, a.reviewer or "", a.note or "", lock)
            out["snapshot"] = f"{a.accept_snapshot} ({len(m['locked_holes'])} holes locked)"
        if a.audit_export:
            from .audit import export
            m = export(res.ctx, params, a.audit_export)
            out["audit_checklist"] = f"{m['path']} ({m['selected']} of {m['population']} samples, seed {m['seed']})"
        log.write("")
        counts = res.issues["severity"].value_counts().to_dict() if not res.issues.empty else {}
        log.write(f"  issues: {counts}")
        log.write(f"  rules: {res.matrix['status'].value_counts().to_dict()}")
        for k, v in out.items():
            log.write(f"  {k}: {v}")
        if res.errors:
            log.write("  run messages:\n    " + "\n    ".join(e.splitlines()[0] for e in res.errors if e.strip()), err=True)
        code = 3 if (res.matrix["status"] == "FAILED").any() else 2 if counts.get("CRITICAL") else 1 if counts.get("ERROR") else 0
        log.write(f"  exit code {code} (0 no Major/Critical, 1 Major, 2 Critical, 3 run failure)")
        return code
    except SystemExit as e:
        log.write(str(e), err=True)
        return 3
    except Exception:
        import traceback
        log.write(traceback.format_exc(), err=True)
        return 3
    finally:
        log.close(run_dir)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="geovalid", description=f"GEOVALID PRO {__version__} — drillhole database validation")
    ap.add_argument("--version", action="version", version=__version__)
    sub = ap.add_subparsers(dest="cmd")
    r = sub.add_parser("run", help="validate a database")
    r.add_argument("--project", help="saved project file (.json): inputs, mappings, optional inputs and profile")
    r.add_argument("--save-project", help="write a project file for this run (.json)")
    r.add_argument("--apply-fixes", help="apply approved fix classes to corrected copies, e.g. ID_MAP,AZ_360 (ID map from the profile)")
    r.add_argument("--files", nargs="*")
    r.add_argument("--sample", action="store_true")
    r.add_argument("--dem")
    r.add_argument("--licence")
    r.add_argument("--crm", help="CRM certificates: CRM_ID, ELEMENT, CERTIFIED, SD[, UNIT]")
    r.add_argument("--lab", help="laboratory / QA-QC file in the GEOQAQC format (reconciliation REC-01…06)")
    r.add_argument("--umpire", help="check / umpire laboratory file (SAMPLE_ID, elements)")
    r.add_argument("--topo-format", help="override topography format detection (asc, grd, bil, flt, tif, hgt, xyz, dxf, shp, kml, str, obj, stl, ply)")
    r.add_argument("--baseline", nargs="*", help="files of the previous dataset version (VER-001…005, change log)")
    r.add_argument("--snapshot", help="accepted-snapshot manifest, or a folder of them (VER-009)")
    r.add_argument("--accept-snapshot", help="write an accepted-snapshot manifest for this dataset (.json)")
    r.add_argument("--reviewer", help="reviewer name for --accept-snapshot and --apply-fixes")
    r.add_argument("--note", help="note for --accept-snapshot")
    r.add_argument("--lock", help="holes locked by --accept-snapshot: all (default), none, or a comma-separated list")
    r.add_argument("--audit-export", help="write the seeded random-audit checklist (.xlsx or .csv) (REC-07)")
    r.add_argument("--audit-results", help="import a filled random-audit checklist into the evidence pack")
    r.add_argument("--profile")
    r.add_argument("--codes", help="code dictionary file (field, code[, description])")
    r.add_argument("--out", help="output folder (default: the project's, else GEOVALID_PRO/output)")
    r.add_argument("--lang", choices=["fa", "en", "both"], help="report language (default: the project's, else fa)")
    r.add_argument("--name", default="GEOVALID project")
    s = sub.add_parser("sample", help="write the synthetic database")
    s.add_argument("--out")
    s.add_argument("--clean", action="store_true")
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] == ["--cli"]:                 # brief F10: GEOVALID.exe --cli --project ... --profile ... --out ...
        argv = ["run"] + argv[1:]
    a = ap.parse_args(argv)
    if a.cmd == "run":
        return cmd_run(a)
    if a.cmd == "sample":
        print(_sample_dir(a.out, a.clean))
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
