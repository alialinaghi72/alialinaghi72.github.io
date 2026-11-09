"""Performance benchmark (v2 brief §10.7): validation time for N holes × M samples per hole.

    python tools/perf_bench.py 10000 100        # 10 000 holes, 1 000 000 assay rows

Writes a synthetic database (collar, survey, assay, lithology) to a temporary folder, runs the full validation and
prints the time of each stage and of the slowest rules.
"""
import sys
import tempfile
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from geovalid_pro.engine import ProjectSpec, load_inputs, run  # noqa: E402


def make(folder: Path, n_holes: int, per_hole: int, seed: int = 5) -> list[str]:
    rng = np.random.default_rng(seed)
    side = int(np.ceil(np.sqrt(n_holes)))
    ids = np.array([f"BH{i:06d}" for i in range(n_holes)])
    gx, gy = np.arange(n_holes) % side, np.arange(n_holes) // side
    eoh = float(per_hole)
    collar = pd.DataFrame({"HoleID": ids, "East": 400000 + 25.0 * gx + rng.normal(0, 0.5, n_holes),
                           "North": 3500000 + 25.0 * gy + rng.normal(0, 0.5, n_holes), "RL": 1200 + rng.normal(0, 5, n_holes).round(2),
                           "MaxDepth": eoh, "Azimuth": 90.0, "Dip": -60.0})
    st = np.array([0.0, 30.0, 60.0, 90.0])
    st = st[st < eoh]
    survey = pd.DataFrame({"HoleID": np.repeat(ids, len(st)), "Depth": np.tile(st, n_holes),
                           "Azimuth": (90 + rng.normal(0, 0.3, n_holes * len(st))).round(2),
                           "Dip": (-60 + rng.normal(0, 0.2, n_holes * len(st))).round(2)})
    frm = np.tile(np.arange(per_hole, dtype=float), n_holes)
    assay = pd.DataFrame({"HoleID": np.repeat(ids, per_hole), "From": frm, "To": frm + 1,
                          "SampleID": [f"S{i:08d}" for i in range(n_holes * per_hole)],
                          "Cu_pct": np.round(rng.lognormal(-2, 1, n_holes * per_hole), 4),
                          "Au_ppm": np.round(rng.lognormal(-2.5, 1, n_holes * per_hole), 3)})
    cuts = np.array([0.0, 0.2, 0.45, 0.7, 1.0]) * eoh
    lith = pd.DataFrame({"HoleID": np.repeat(ids, 4), "From": np.tile(cuts[:-1], n_holes), "To": np.tile(cuts[1:], n_holes),
                         "Lith": np.tile(["AND", "DIO", "QMP", "DIO"], n_holes)})
    paths = []
    for name, df in (("collar", collar), ("survey", survey), ("assay", assay), ("lithology", lith)):
        p = folder / f"{name}.csv"
        df.to_csv(p, index=False)
        paths.append(str(p))
    return paths


def main(n_holes: int, per_hole: int) -> None:
    d = Path(tempfile.mkdtemp())
    t0 = time.time()
    paths = make(d, n_holes, per_hole)
    t1 = time.time()
    ins = [i for i in load_inputs(paths) if i.kind != "ignore"]
    t2 = time.time()
    marks = []
    last = [time.time(), "start"]

    def progress(p, msg):
        now = time.time()
        marks.append((last[1], now - last[0]))
        last[0], last[1] = now, msg
    res = run(ProjectSpec(ins), progress)
    t3 = time.time()
    rows = sum(len(i.raw.df) for i in ins)
    print(f"holes {n_holes:,}, rows {rows:,}: generate {t1 - t0:.1f} s, read+map {t2 - t1:.1f} s, validate {t3 - t2:.1f} s, "
          f"total {t3 - t1:.1f} s; issues {len(res.issues):,}; failed rules {int((res.matrix['status'] == 'FAILED').sum())}")
    slow = sorted(marks, key=lambda m: -m[1])[:12]
    print("slowest steps: " + ", ".join(f"{k} {v:.1f}s" for k, v in slow))


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 10000, int(sys.argv[2]) if len(sys.argv) > 2 else 100)
