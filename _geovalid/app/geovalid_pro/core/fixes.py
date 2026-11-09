"""Fix classes (v2 brief §5.6, constraint 7): flag-only by default; a fix is applied only after explicit approval of its
class. Applying writes a corrected COPY of each affected input file plus `fix_log.csv` (rule, row, old value, new value,
timestamp, user). Source files are never modified.

Every fix class is listed here with its description; the GUI and the evidence pack read this list.
"""
from __future__ import annotations

import getpass
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from .normalise import hole_key


@dataclass(frozen=True)
class FixClass:
    id: str
    rules: tuple[str, ...]
    title_en: str
    title_fa: str
    description: str


FIX_CLASSES = {
    "ID_MAP": FixClass("ID_MAP", ("COL-003", "SUR-001", "INT-006"), "Apply the approved hole-ID mapping table",
                       "اعمال جدول تأییدشدهٔ نگاشت شناسهٔ گمانه",
                       "Replaces each raw hole ID listed in the mapping table by its approved target ID, in every table. "
                       "Nothing is merged unless the user approved that row of the table (SCH-05)."),
    "AZ_360": FixClass("AZ_360", ("SUR-004",), "Write azimuth 360° as 0°", "نوشتن آزیموت ۳۶۰ به صورت صفر",
                       "Survey and collar azimuths exactly equal to 360 become 0 (same direction)."),
    "AZ_WRAP": FixClass("AZ_WRAP", ("SUR-004",), "Bring azimuths into 0–360°", "انتقال آزیموت‌ها به بازهٔ ۰ تا ۳۶۰",
                        "Azimuths in (360, 720] lose 360 (declination added without modulo); azimuths in [−360, 0) gain 360."),
    "SURVEY_DUP_IDENTICAL": FixClass("SURVEY_DUP_IDENTICAL", ("SUR-002",), "Remove identical duplicate survey stations",
                                     "حذف ایستگاه‌های تکراری یکسان", "Of two survey rows with the same hole, depth, azimuth and dip, "
                                     "the later row is removed. Conflicting duplicates are never touched."),
    "INTERVAL_DUP_IDENTICAL": FixClass("INTERVAL_DUP_IDENTICAL", ("INT-003",), "Remove identical duplicate interval rows",
                                       "حذف ردیف‌های بازه‌ای تکراری یکسان", "Rows identical in every column (hole, from, to and all "
                                       "values) are reduced to one. Conflicting duplicates are never touched."),
}


def candidates(res) -> pd.DataFrame:
    """Fix classes with at least one issue they can act on (issues carry `fix_class`), for the approval dialog."""
    iss = res.issues
    if iss.empty or "fix_class" not in iss:
        return pd.DataFrame(columns=["fix_class", "n_issues"])
    return iss[iss["fix_class"].notna()].groupby("fix_class").size().rename("n_issues").reset_index()


def suggested_id_map(res) -> pd.DataFrame:
    """Rows for the ID-mapping table: raw ID → suggested target, from SCH-05 groups (all unapproved)."""
    g = res.ctx.stats.get("id_groups")
    if g is None or g.empty:
        return pd.DataFrame(columns=["raw_id", "target_id", "approved", "tables", "rows"])
    out = (g[g["raw_id"] != g["suggested_target"]].groupby(["raw_id", "suggested_target"])
           .agg(tables=("table", lambda s: ", ".join(sorted(set(s)))), rows=("rows", "sum")).reset_index())
    out = out.rename(columns={"suggested_target": "target_id"})
    out.insert(2, "approved", False)
    return out


def _num(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s.astype("string").str.strip().str.replace(",", ".", regex=False), errors="coerce")


def apply_fixes(res, approved: list[str], out_dir: str, id_map: pd.DataFrame | None = None, user: str | None = None) -> dict:
    """Apply the approved fix classes to copies of the inputs. Returns {"files": [...], "fix_log": path, "n": count}."""
    user = user or getpass.getuser()
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    log, written = [], []
    mapping = {}
    if "ID_MAP" in approved and id_map is not None and not id_map.empty:
        ok = id_map[id_map["approved"].astype(bool)]
        mapping = {str(a).strip(): str(b).strip() for a, b in zip(ok["raw_id"], ok["target_id"]) if str(a).strip() and str(b).strip()}
    for inp in res.spec.inputs:
        df = inp.raw.df.copy()
        f = inp.mapping.fields
        changed = False
        drop = []
        hid = f.get("hole_id")
        if mapping and hid in df:
            for i, v in df[hid].items():
                k = str(v).strip() if pd.notna(v) else None
                if k in mapping:
                    log.append({"fix_class": "ID_MAP", "rule": "COL-003", "file": Path(inp.raw.source).name, "table": inp.name,
                                "row": int(i) + 2, "field": hid, "old": v, "new": mapping[k], "timestamp": stamp, "user": user})
                    df.at[i, hid] = mapping[k]
                    changed = True
        az = f.get("azimuth")
        if az in df and ({"AZ_360", "AZ_WRAP"} & set(approved)):
            num = _num(df[az])
            for i, v in num.items():
                new = None
                if "AZ_360" in approved and v == 360:
                    new = 0
                elif "AZ_WRAP" in approved and np.isfinite(v) and (360 < v <= 720 or -360 <= v < 0):
                    new = v - 360 if v > 360 else v + 360
                if new is not None:
                    log.append({"fix_class": "AZ_360" if v == 360 else "AZ_WRAP", "rule": "SUR-004", "file": Path(inp.raw.source).name,
                                "table": inp.name, "row": int(i) + 2, "field": az, "old": df.at[i, az], "new": f"{new:g}",
                                "timestamp": stamp, "user": user})
                    df.at[i, az] = f"{new:g}"
                    changed = True
        if inp.kind == "survey" and "SURVEY_DUP_IDENTICAL" in approved and hid in df and f.get("depth_m") in df:
            key = [hid, f["depth_m"]] + [c for c in (az, f.get("dip")) if c in df]
            norm = df[key].astype("string").apply(lambda s: s.str.strip())
            for i in df.index[norm.duplicated(keep="first")]:
                drop.append((i, "SURVEY_DUP_IDENTICAL", "SUR-002"))
        if inp.kind not in ("collar", "survey") and "INTERVAL_DUP_IDENTICAL" in approved and hid in df:
            norm = df.astype("string").apply(lambda s: s.str.strip())
            for i in df.index[norm.duplicated(keep="first")]:
                drop.append((i, "INTERVAL_DUP_IDENTICAL", "INT-003"))
        for i, fc, rule in drop:
            log.append({"fix_class": fc, "rule": rule, "file": Path(inp.raw.source).name, "table": inp.name, "row": int(i) + 2,
                        "field": "(row)", "old": "; ".join(f"{c}={df.at[i, c]}" for c in df.columns[:6]), "new": "(removed)",
                        "timestamp": stamp, "user": user})
        if drop:
            df = df.drop(index=[i for i, _, _ in drop])
            changed = True
        if changed:
            safe = "".join(ch if ch.isalnum() or ch in "-_." else "_" for ch in inp.name)
            path = out / f"{safe}_corrected.csv"
            df.to_csv(path, index=False, encoding="utf-8-sig")
            written.append(path)
    log_df = pd.DataFrame(log, columns=["fix_class", "rule", "file", "table", "row", "field", "old", "new", "timestamp", "user"])
    log_path = out / "fix_log.csv"
    log_df.to_csv(log_path, index=False, encoding="utf-8-sig")
    if mapping:
        pd.DataFrame({"raw_id": list(mapping), "target_id": list(mapping.values()), "approved_by": user, "timestamp": stamp}) \
            .to_csv(out / "id_mapping_approved.csv", index=False, encoding="utf-8-sig")
    res.outputs["fix_log"] = log_path
    res.ctx.stats["fix_log"] = log_df
    return {"files": written, "fix_log": log_path, "n": len(log_df)}


def unused_mapping_rows(id_map: pd.DataFrame, res) -> list[str]:
    """Raw IDs in an approved mapping that no longer occur in the data (stale table)."""
    present = set()
    for inp in res.spec.inputs:
        c = inp.mapping.fields.get("hole_id")
        if c in inp.raw.df:
            present |= set(inp.raw.df[c].dropna().astype(str).str.strip())
    return [r for r in id_map.get("raw_id", []) if str(r) not in present and hole_key(r)]
