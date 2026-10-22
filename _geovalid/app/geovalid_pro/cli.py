"""Command line (01 §11, v0.1 subset).

  GEOVALID.exe run --files collar.csv survey.csv assay.xlsx [--dem dem.asc] [--licence lic.csv] [--crm crm.csv]
                   [--profile my.yaml] [--out folder] [--lang fa|en|both] [--name "Project"]
  GEOVALID.exe run --sample [--out folder]          validate the bundled synthetic database
  GEOVALID.exe sample --out folder [--clean]        write the synthetic database (with or without injected errors)

Exit codes: 0 no ERROR/CRITICAL, 1 ERROR present, 2 CRITICAL present, 3 run failure.
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


def cmd_run(a) -> int:
    from .engine import ProjectSpec, load_inputs, run
    from .io.writers import write_outputs
    if a.sample:
        d = _sample_dir(None)
        files = [str(p) for p in sorted(d.glob("*.csv")) if p.stem in ("collar", "survey", "assay", "lithology", "geotech", "density")]
        a.dem, a.licence, a.crm = a.dem or str(d / "dem.asc"), a.licence or str(d / "licence.csv"), a.crm or str(d / "crm_standards.csv")
    else:
        files = a.files or []
    if not files:
        print("no input files (use --files or --sample)", file=sys.stderr)
        return 3
    inputs = load_inputs(files)
    for t in inputs:
        print(f"  {t.name:<28} {t.kind:<11} {len(t.raw.df):>8} rows")
    spec = ProjectSpec([t for t in inputs if t.kind != "ignore"], a.dem, a.licence, a.crm, a.profile, a.name)
    res = run(spec, lambda p, m: print(f"\r  [{p:3d}%] {m:<30}", end="", flush=True))
    out = write_outputs(res, a.out, a.lang)
    print()
    counts = res.issues["severity"].value_counts().to_dict() if not res.issues.empty else {}
    print(f"  issues: {counts}")
    print(f"  rules: {res.matrix['status'].value_counts().to_dict()}")
    for k, v in out.items():
        print(f"  {k}: {v}")
    if res.errors:
        print("  run messages:\n    " + "\n    ".join(e.splitlines()[0] for e in res.errors if e.strip()), file=sys.stderr)
    if (res.matrix["status"] == "FAILED").any():
        return 3
    return 2 if counts.get("CRITICAL") else 1 if counts.get("ERROR") else 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="geovalid", description=f"GEOVALID PRO {__version__} — drillhole database validation")
    ap.add_argument("--version", action="version", version=__version__)
    sub = ap.add_subparsers(dest="cmd")
    r = sub.add_parser("run", help="validate a database")
    r.add_argument("--files", nargs="*")
    r.add_argument("--sample", action="store_true")
    r.add_argument("--dem")
    r.add_argument("--licence")
    r.add_argument("--crm")
    r.add_argument("--profile")
    r.add_argument("--out", default=str(Path.home() / "GEOVALID_PRO" / "output"))
    r.add_argument("--lang", default="fa", choices=["fa", "en", "both"])
    r.add_argument("--name", default="GEOVALID project")
    s = sub.add_parser("sample", help="write the synthetic database")
    s.add_argument("--out")
    s.add_argument("--clean", action="store_true")
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
