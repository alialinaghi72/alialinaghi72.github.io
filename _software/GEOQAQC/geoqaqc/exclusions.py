# -*- coding: utf-8 -*-
"""Exclusion review of duplicate pairs (R5, R14, R24).

Two triggers, set per element and duplicate class in the element profiles:
  low-grade   the pair mean is below k x the QC reference DL (k = 10 by
              default): there the relative difference is instrument noise;
  outlier     HARD at or above a threshold, or a C16 mispair candidate.
Each trigger has an action: exclude automatically, keep, or ask. A pair the
user is asked about keeps its decision in the session (project.pair_decisions)
and the decision is re-applied on every run. Until it is decided, the
pre-selected action of the element applies, an exclusion then counting as a
suspected mix-up, not yet verified -- which makes the verdict provisional.

Exclusions only take a pair out of the statistics: no value is changed.
"""

from __future__ import annotations

from .core import DUP_TYPES, element_unit
from .model import detection_limit, pairable

REASONS = ["confirmed sample mix-up - dispatch sheet checked",
           "suspected mix-up - not yet verified",
           "laboratory transcription error",
           "other"]
SUSPECTED = REASONS[1]
REASONS_FA = {
    REASONS[0]: "جابه‌جایی نمونهٔ تأییدشده (برگهٔ ارسال بررسی شد)",
    REASONS[1]: "جابه‌جایی محتمل (هنوز تأیید نشده)",
    REASONS[2]: "خطای ثبت آزمایشگاه",
    REASONS[3]: "دلیل دیگر",
}
TRIGGERS = ("low-grade", "outlier", "mispair")


def pair_key(dtype, el, orig, dup):
    return f"{dtype}|{el}|{orig}|{dup}"


def _hard(a, b):
    return abs(a - b) / (a + b) * 100.0 if a + b > 0 else None


def review_rows(project, pairs, S, RB):
    """Every pair that meets a trigger, with its resolved decision:
    [{key, dtype, element, orig, dup, a, b, mean, hard, ratio, trigger,
      action, decision, reason, source, pending, order, batch, limit}]."""
    out = []
    mis = getattr(project, "mispair_candidates", {}) or {}
    decided = getattr(project, "pair_decisions", {}) or {}
    review_outliers = RB["clean_C16"]
    for dtype in DUP_TYPES:
        plist = pairs.get(dtype) or []
        if not plist:
            continue
        for el in project.elements:
            prof = RB.el.profile(el)
            dl = detection_limit(project, el, S)
            qdl = RB.el.qc_dl(el, element_unit(el)) or \
                detection_limit(project, el, S, known_only=True)
            k = prof["low_kdl"].get(dtype)
            k = RB["dup_min_kdl"] if k is None else k
            thr = prof["outlier_hard"].get(dtype)
            for so, sd_ in plist:
                if not pairable(so, el, RB) or not pairable(sd_, el, RB):
                    continue
                a, b = so.vals.get(el), sd_.vals.get(el)
                below = (so.flags.get(el) == "<" or sd_.flags.get(el) == "<"
                         or (dl and (a < dl or b < dl)))
                if below and S["drop_below_dl"]:
                    continue
                if a + b <= 0:
                    continue
                m = (a + b) / 2.0
                h = _hard(a, b)
                row = {"key": pair_key(dtype, el, so.sid, sd_.sid), "dtype": dtype,
                       "element": el, "orig": so.sid, "dup": sd_.sid, "a": a, "b": b,
                       "mean": m, "hard": h,
                       "ratio": (max(a, b) / min(a, b)) if min(a, b) > 0 else None,
                       "order": sd_.order, "batch": sd_.batch or so.batch}
                if k and qdl and m < k * qdl:
                    row.update(trigger="low-grade", action=prof["low_action"],
                               preselect="exclude", limit=k * qdl, kdl=k)
                elif review_outliers and ((so.sid, sd_.sid) in mis or
                                          (thr is not None and h is not None
                                           and h >= thr)):
                    is_out = thr is not None and h is not None and h >= thr
                    row.update(trigger="outlier" if is_out else "mispair",
                               action=prof["outlier_action"],
                               preselect=prof["outlier_preselect"], limit=thr,
                               detail=mis.get((so.sid, sd_.sid), ""))
                else:
                    continue
                _resolve(row, decided.get(row["key"]))
                out.append(row)
    return out


def _resolve(row, saved):
    low = row["trigger"] == "low-grade"
    auto_reason = (f"pair mean below {row.get('kdl', 0):g} x QC DL"
                   if low else f"excluded automatically (HARD >= {row['limit']:g} %)")
    row["pending"] = False
    if row["action"] == "exclude":
        row.update(decision="exclude", reason=auto_reason, source="rule")
    elif row["action"] == "keep":
        row.update(decision="keep", reason="", source="rule")
    elif saved and saved.get("decision") in ("exclude", "keep"):
        row.update(decision=saved["decision"], reason=saved.get("reason", ""),
                   note=saved.get("note", ""), source="user")
    else:
        row["pending"] = True
        row["source"] = "default"
        row["decision"] = row["preselect"]
        row["reason"] = (auto_reason if low else SUSPECTED) \
            if row["decision"] == "exclude" else ""


def excluded_sets(rows):
    """({(dtype, el): {(orig, dup)}} low-grade, ... outliers) of the excluded."""
    low, out = {}, {}
    for r in rows:
        if r["decision"] != "exclude":
            continue
        tgt = low if r["trigger"] == "low-grade" else out
        tgt.setdefault((r["dtype"], r["element"]), set()).add((r["orig"], r["dup"]))
    return low, out


def merge(a, b):
    out = {k: set(v) for k, v in a.items()}
    for k, v in b.items():
        out.setdefault(k, set()).update(v)
    return out


def summary(rows, dup_all):
    """Per (dtype, element): total pairs, excluded low-grade, excluded
    outliers, outliers kept."""
    out = {}
    for (dtype, el), rec in dup_all.items():
        out[(dtype, el)] = {"total": rec["n"] + rec.get("n_below_kdl", 0),
                            "low": 0, "out_excl": 0, "out_kept": 0}
    for r in rows:
        s = out.setdefault((r["dtype"], r["element"]),
                           {"total": 0, "low": 0, "out_excl": 0, "out_kept": 0})
        if r["trigger"] == "low-grade":
            s["low"] += r["decision"] == "exclude"
        elif r["decision"] == "exclude":
            s["out_excl"] += 1
        else:
            s["out_kept"] += 1
    return out


def provisional(rows):
    """Excluded outliers whose reason is a suspicion not yet verified."""
    return [r for r in rows if r["trigger"] != "low-grade"
            and r["decision"] == "exclude" and r.get("reason") == SUSPECTED]


def record(project, row, decision, reason="", note=""):
    """Store the user's decision on one pair."""
    if not hasattr(project, "pair_decisions") or project.pair_decisions is None:
        project.pair_decisions = {}
    project.pair_decisions[row["key"]] = {"decision": decision, "reason": reason,
                                         "note": note}
