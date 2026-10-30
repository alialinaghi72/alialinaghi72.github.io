# -*- coding: utf-8 -*-
"""QA/QC analyses.

The 1.1 methods are carried over with their formulas unchanged; the only
differences are that every loop honours the cleaning (model.usable), CRMs are
keyed by their certificate label, blanks by (blank type, element), and every
threshold comes from S, C or RB. The methods added in 2.0 follow below them.
"""

from __future__ import annotations

import datetime as _dt
import math

from .cleaning import clean_pairs, clean_values, parse_value
from .core import (BLANK_TYPES, DUP_TYPES, R_NA, R_VBAD, SAMPLE_TYPES,
                   SEV_ERROR, SEV_WARN, T_BLANK, T_CBLANK, T_CDUP, T_CRM, T_FDUP,
                   T_NORMAL, T_PBLANK, T_PDUP, T_UMP, classify_type, cusum,
                   linreg, linreg_stats, mean, paired_t, pctile, rma, spearman,
                   stdev, t_two_tail_p, wilcoxon)
from .model import build_samples, detection_limit, usable
from .protocol import combine_ratings, rate

# ===========================================================================
#  CRM analysis
# ===========================================================================
def analyse_crm(project, F, C, S, RB, log=print):
    """Per (CRM label, element): control-chart series, statistics, rating."""
    out = {}
    all_crm = [s for s in project.samples if s.stype == T_CRM and not s.dropped]
    crm_samples = [s for s in all_crm if not s.excl_all]
    if not all_crm:
        return out

    codes = sorted({s.crm_key for s in all_crm if s.crm_key})
    if not codes:
        log("  ! CRM samples found but no CRM code column was mapped.")
        return out

    for code in codes:
        label = project.crm_labels.get(code, code)
        subset = [s for s in crm_samples if s.crm_key == code]
        subset.sort(key=lambda s: (s.order if s.order is not None else 0))
        for el in project.elements:
            cert = project.certs.get((code, el))
            series = [(s, s.vals.get(el)) for s in subset if usable(s, el)]
            excluded = [{"sample": s.sid, "reason": s.excl_all or s.excl.get(el, "")}
                        for s in all_crm if s.crm_key == code
                        and (s.excl_all or el in s.excl)]
            if not series:
                continue
            meas = [v for _, v in series]
            obs_mean = mean(meas)
            obs_sd = stdev(meas)
            key = (label, el)

            rec = {"crm": label, "key": code, "element": el, "n": len(series),
                   "excluded": excluded,
                   "obs_mean": obs_mean, "obs_sd": obs_sd,
                   "cert": None, "sd": None, "unit": "",
                   "points": [], "failures": [], "rules": [],
                   "bias": None, "fail_pct": None, "warn_pct": None,
                   "rsd_pct": None, "ratings": {}, "rating": R_NA, "score": None,
                   "drift": None, "cusum": None, "batch_bias": [],
                   "rsd_ratio": None}

            if cert is None:
                rec["note"] = ("No certificate found for this CRM/element pair. "
                               "Import a certificate table to enable accuracy "
                               "statistics; only repeatability is reported.")
                rec["rsd_pct"] = F.calc("crm_pooled_sd_pct",
                                        obs_sd=obs_sd or 0.0, obs_mean=obs_mean or 1.0)
                rec["ratings"]["crm_rsd"] = rate(rec["rsd_pct"], C["crm_rsd"])
                rec["rating"], rec["score"] = combine_ratings(
                    [rec["ratings"]["crm_rsd"]])
                out[key] = rec
                continue

            cv, sd = cert["cert"], cert["sd"]
            rec["cert"], rec["sd"], rec["unit"] = cv, sd, cert.get("unit", "")

            # if the certificate carries no SD, fall back on the observed spread
            eff_sd = sd if sd else obs_sd
            rec["eff_sd"] = eff_sd
            rec["sd_source"] = "certified" if sd else "observed"

            biases, zs = [], []
            for s, v in series:
                bias = F.calc("crm_bias", meas=v, cert=cv)
                z = F.calc("crm_z", meas=v, cert=cv, sd=eff_sd) if eff_sd else None
                biases.append(bias)
                zs.append(z)
                rec["points"].append({
                    "sample": s.sid, "order": s.order, "batch": s.batch,
                    "date": s.date, "value": v, "bias": bias, "z": z,
                    "row": s.row_n})

            rec["bias"] = mean([b for b in biases if b is not None])
            rec["abs_bias"] = abs(rec["bias"]) if rec["bias"] is not None else None
            rec["rsd_pct"] = F.calc("crm_pooled_sd_pct",
                                    obs_sd=obs_sd or 0.0, obs_mean=obs_mean or 1.0)
            zz = [z for z in zs if z is not None]
            if zz:
                rec["fail_pct"] = 100.0 * sum(1 for z in zz
                                              if abs(z) > S["k_fail"]) / len(zz)
                rec["warn_pct"] = 100.0 * sum(1 for z in zz
                                              if abs(z) > S["k_warn"]) / len(zz)

            # ---- Westgard-style rule violations ----
            rules = []
            for i, z in enumerate(zs):
                if z is None:
                    continue
                p = rec["points"][i]
                if abs(z) > S["k_fail"]:
                    rules.append({"rule": "1-3s", "sample": p["sample"],
                                  "z": z, "sev": SEV_ERROR,
                                  "desc": f"single result beyond {S['k_fail']:g} SD"})
                if i >= 1 and zs[i - 1] is not None:
                    if (z > S["k_warn"] and zs[i - 1] > S["k_warn"]) or \
                       (z < -S["k_warn"] and zs[i - 1] < -S["k_warn"]):
                        rules.append({"rule": "2-2s", "sample": p["sample"], "z": z,
                                      "sev": SEV_ERROR,
                                      "desc": "two consecutive results beyond "
                                              f"{S['k_warn']:g} SD on the same side"})
                if i >= 3 and all(zs[j] is not None for j in range(i - 3, i + 1)):
                    w = zs[i - 3:i + 1]
                    if all(x > 1 for x in w) or all(x < -1 for x in w):
                        rules.append({"rule": "4-1s", "sample": p["sample"], "z": z,
                                      "sev": SEV_WARN,
                                      "desc": "four consecutive results beyond "
                                              "1 SD on the same side"})
                if i >= 1 and zs[i - 1] is not None and abs(z - zs[i - 1]) > 4:
                    rules.append({"rule": "R-4s", "sample": p["sample"], "z": z,
                                  "sev": SEV_WARN,
                                  "desc": "range between two consecutive results "
                                          "exceeds 4 SD"})
            n_run = int(S["run_len"])
            side = 0
            run = 0
            for i, z in enumerate(zs):
                if z is None:
                    side, run = 0, 0
                    continue
                s_now = 1 if z > 0 else -1
                run = run + 1 if s_now == side else 1
                side = s_now
                if run == n_run:
                    rules.append({"rule": f"{n_run}x", "sample": rec["points"][i]["sample"],
                                  "z": z, "sev": SEV_WARN,
                                  "desc": f"{n_run} consecutive results on the same "
                                          "side of the certified value -- a bias, "
                                          "not random scatter"})
            rec["rules"] = rules
            rec["failures"] = [p for p, z in zip(rec["points"], zs)
                               if z is not None and abs(z) > S["k_fail"]]
            _crm_extras(rec, S, RB)

            if len(series) >= S["min_crm"]:
                rec["ratings"]["crm_bias"] = rate(rec["abs_bias"], C["crm_bias"])
                rec["ratings"]["crm_fail"] = rate(rec["fail_pct"], C["crm_fail"])
                rec["ratings"]["crm_warn"] = rate(rec["warn_pct"], C["crm_warn"])
                rec["ratings"]["crm_rsd"] = rate(rec["rsd_pct"], C["crm_rsd"])
                rec["rating"], rec["score"] = combine_ratings(
                    [rec["ratings"]["crm_bias"], rec["ratings"]["crm_fail"],
                     rec["ratings"]["crm_warn"], rec["ratings"]["crm_rsd"]],
                    [3.0, 3.0, 1.0, 1.5])
            else:
                rec["note"] = (f"Only {len(series)} results. Below the minimum of "
                               f"{S['min_crm']} the statistics are not stable "
                               f"enough to carry a rating.")
            out[key] = rec
    return out


# ===========================================================================
#  Blank analysis
# ===========================================================================
def analyse_blank(project, F, C, S, RB, log=print):
    """Per (blank type, element). Each blank type present is analysed on its
    own: a coarse blank tests preparation and analysis, a pulp blank the
    analysis alone, so the two must not be pooled."""
    out = {}
    live = [s for s in project.samples if not s.dropped]
    order_index = {id(s): i for i, s in enumerate(live)}
    for btype in BLANK_TYPES:
        blanks = [s for s in live if s.stype == btype and not s.excl_all]
        if blanks:
            out.update(_analyse_blank_type(project, F, C, S, RB, btype, blanks,
                                           live, order_index))
    return out


def _analyse_blank_type(project, F, C, S, RB, btype, blanks, live, order_index):
    out = {}
    for el in project.elements:
        dl = detection_limit(project, el, S)
        if dl is None or dl <= 0:
            continue
        limit = F.calc("blank_limit", dl=dl, k_dl=S["k_dl"])
        pts, fails = [], 0
        for s in blanks:
            if not usable(s, el):
                continue
            v = s.vals.get(el)
            ratio = F.calc("blank_ratio", meas=v, dl=dl)
            i = order_index[id(s)]
            prev = live[i - 1] if i > 0 else None
            prev_v = prev.vals.get(el) if prev else None
            carry = (F.calc("blank_carry", meas=v, prev=prev_v)
                     if prev_v not in (None, 0) else None)
            bad = limit is not None and v > limit
            if bad:
                fails += 1
            pts.append({"sample": s.sid, "order": s.order, "batch": s.batch,
                        "value": v, "ratio": ratio, "limit": limit,
                        "prev_sample": prev.sid if prev else "",
                        "prev_value": prev_v, "carry_pct": carry,
                        "fail": bad, "row": s.row_n})
        if not pts:
            continue
        vals = [p["value"] for p in pts]
        rec = {"element": el, "btype": btype, "n": len(pts), "dl": dl,
               "limit": limit,
               "points": pts, "n_fail": fails,
               "fail_pct": 100.0 * fails / len(pts),
               "max": max(vals), "mean": mean(vals),
               "max_ratio": max(p["ratio"] for p in pts if p["ratio"] is not None),
               "ratings": {}, "rating": R_NA, "score": None}
        rec["ratings"]["blank_fail"] = rate(rec["fail_pct"], C["blank_fail"])
        rec["ratings"]["blank_max"] = rate(rec["max_ratio"], C["blank_max"])
        rec["rating"], rec["score"] = combine_ratings(
            [rec["ratings"]["blank_fail"], rec["ratings"]["blank_max"]], [3.0, 1.0])
        # carry-over evidence
        rec["carry"] = [p for p in pts
                        if p["fail"] and p["carry_pct"] is not None
                        and p["prev_value"] is not None
                        and p["prev_value"] > S["carry_kdl"] * dl]
        routine = sorted(s.vals[el] for s in live if s.stype == T_NORMAL
                         and usable(s, el) and s.flags.get(el) != "<")
        hi_cut = max(pctile(routine, RB["carry_pctile"]) or 0.0, S["carry_kdl"] * dl)
        _blank_extras(rec, hi_cut)
        out[(btype, el)] = rec
    return out


# ===========================================================================
#  Duplicate pairing and precision
# ===========================================================================
def build_pairs(project, S, log=print):
    """Return {dup_type: [(orig_sample, dup_sample), ...]}."""
    by_id = {}
    for s in project.samples:
        if not s.dropped:
            by_id.setdefault(s.sid.strip().upper(), s)
    pairs = {t: [] for t in DUP_TYPES}
    gone = project.excluded_pairs
    used = set()

    # 1) explicit pair table
    pt = project.pairs
    if pt is not None:
        for r in pt.rows:
            o = str(pt.get(r, "sampleid") or "").strip().upper()
            d = str(pt.get(r, "dupid") or "").strip().upper()
            if not o or not d:
                continue
            so, sd_ = by_id.get(o), by_id.get(d)
            if not so or not sd_ or so.excl_all or sd_.excl_all:
                continue
            if (so.sid, sd_.sid) in gone:
                continue
            raw = str(pt.get(r, "type") or "").strip()
            t = pt.type_map.get(raw) or classify_type(raw)
            if t not in DUP_TYPES:
                t = sd_.stype if sd_.stype in DUP_TYPES else T_FDUP
            pairs[t].append((so, sd_))
            used.add((o, d))

    # 2) parent-id column on the duplicate record
    for s in project.samples:
        if s.stype not in DUP_TYPES or not s.parent or s.dropped or s.excl_all:
            continue
        o = s.parent.strip().upper()
        key = (o, s.sid.strip().upper())
        if key in used:
            continue
        so = by_id.get(o)
        if so and not so.excl_all and (so.sid, s.sid) not in gone:
            pairs[s.stype].append((so, s))
            used.add(key)

    # Duplicates whose declared parent is not in the table are silently lost
    # otherwise, and a wrong PARENT_ID column is a common spreadsheet error.
    orphans = []
    for smp in project.samples:
        if smp.stype not in DUP_TYPES or smp.dropped:
            continue
        if not smp.parent:
            orphans.append((smp.sid, smp.stype, "no parent sample ID recorded"))
        elif smp.parent.strip().upper() not in by_id:
            orphans.append((smp.sid, smp.stype,
                            f"parent '{smp.parent}' is not in the table"))
    project.orphan_dups = orphans

    for t in DUP_TYPES:
        if pairs[t]:
            log(f"  {t}: {len(pairs[t])} pair(s)")
    if orphans:
        n_dup = sum(1 for x in project.samples
                    if x.stype in DUP_TYPES and not x.dropped)
        log(f"  ! {len(orphans)} of {n_dup} duplicate row(s) could NOT be paired "
            f"({100.0 * len(orphans) / max(1, n_dup):.0f} %). "
            f"Check the parent-sample column -- see the Log tab for the list.")
        for sid, t, why in orphans[:25]:
            log(f"      {t}  {sid}: {why}")
        if len(orphans) > 25:
            log(f"      ... and {len(orphans) - 25} more")
    return pairs


def analyse_duplicates(project, F, C, S, RB, pairs, log=print):
    out = {}
    crit_key = {T_FDUP: "fdup_hard90", T_CDUP: "cdup_hard90", T_PDUP: "pdup_hard90"}

    for dtype in DUP_TYPES:
        plist = pairs.get(dtype) or []
        if not plist:
            continue
        for el in project.elements:
            dl = detection_limit(project, el, S)
            rows = []
            for so, sd_ in plist:
                if not usable(so, el) or not usable(sd_, el):
                    continue
                a, b = so.vals.get(el), sd_.vals.get(el)
                below = (so.flags.get(el) == "<" or sd_.flags.get(el) == "<"
                         or (dl and (a < dl or b < dl)))
                if below and S["drop_below_dl"]:
                    continue
                if below and dl:
                    a = dl * S["dl_substitute"] if a < dl else a
                    b = dl * S["dl_substitute"] if b < dl else b
                if a + b <= 0:
                    continue
                m = F.calc("dup_mean", a=a, b=b)
                rows.append({
                    "orig": so.sid, "dup": sd_.sid, "batch": sd_.batch,
                    "hole": so.hole or sd_.hole,
                    "drilltype": so.drilltype or sd_.drilltype,
                    "lab": so.lab or sd_.lab,
                    "a": a, "b": b, "mean": m,
                    "diff": F.calc("dup_diff", a=a, b=b),
                    "rd": F.calc("dup_rd", a=a, b=b),
                    "ard": F.calc("dup_ard", a=a, b=b),
                    "hard": F.calc("dup_hard", a=a, b=b),
                    "hrd": F.calc("dup_hrd", a=a, b=b),
                    "cv": F.calc("dup_cv", a=a, b=b),
                    "term": F.calc("dup_pooled_rel_var", a=a, b=b),
                })
            if not rows:
                continue
            for r in rows:
                r["prec95"] = F.calc("dup_precision95", cv=r["cv"] or 0.0)

            hards = sorted(r["hard"] for r in rows if r["hard"] is not None)
            terms = [r["term"] for r in rows if r["term"] is not None]
            a_int, b_slope, r_corr = linreg([r["a"] for r in rows],
                                            [r["b"] for r in rows])
            rma_a, rma_b = rma([r["a"] for r in rows], [r["b"] for r in rows])

            rec = {"type": dtype, "element": el, "n": len(rows), "rows": rows,
                   "dl": dl,
                   "hard_mean": mean(hards),
                   "hard_median": pctile(hards, 50),
                   "hard_p90": pctile(hards, S["hard_pct"]),
                   "hard_pct_used": S["hard_pct"],
                   "rd_mean": mean([r["rd"] for r in rows]),
                   "ard_mean": mean([r["ard"] for r in rows]),
                   "cv_mean": mean([r["cv"] for r in rows]),
                   "pooled_rp": (F.calc("dup_pooled_rp",
                                        s_terms=sum(terms), n=len(terms))
                                 if terms else None),
                   "r": r_corr, "ols_a": a_int, "ols_b": b_slope,
                   "rma_a": rma_a, "rma_b": rma_b,
                   "ratings": {}, "rating": R_NA, "score": None}

            rec["within"] = {}
            for lim in (5, 10, 15, 20, 30):
                rec["within"][lim] = 100.0 * sum(1 for h in hards if h <= lim) / len(hards)
            _dup_extras(rec, F, C, S, RB, crit_key[dtype])

            if len(rows) >= S["min_pairs"]:
                rec["ratings"][crit_key[dtype]] = rate(rec["hard_p90"],
                                                       C[crit_key[dtype]])
                rec["ratings"]["dup_bias"] = rate(
                    abs(rec["rd_mean"]) if rec["rd_mean"] is not None else None,
                    C["dup_bias"])
                rec["ratings"]["dup_r"] = rate(rec["r"], C["dup_r"])
                rec["ratings"]["dup_rma_slope"] = rate(
                    abs(rma_b - 1.0) if rma_b is not None else None,
                    C["dup_rma_slope"])
                rec["rating"], rec["score"] = combine_ratings(
                    [rec["ratings"][crit_key[dtype]], rec["ratings"]["dup_bias"],
                     rec["ratings"]["dup_r"], rec["ratings"]["dup_rma_slope"]],
                    [4.0, 2.0, 1.0, 1.5])
            else:
                rec["note"] = (f"Only {len(rows)} usable pairs. Below the minimum "
                               f"of {S['min_pairs']} a percentile is meaningless, "
                               f"so no rating is given.")
            out[(dtype, el)] = rec
    return out


# ===========================================================================
#  Grouping -- the same precision statistics computed per hole, batch,
#  drill type or laboratory. This is what turns "the duplicates are poor"
#  into "the duplicates are poor in BH103 and nowhere else".
# ===========================================================================
def dup_stats(rows, F, C, S, crit_key):
    """Recompute the duplicate summary for an arbitrary subset of pairs."""
    rows = [r for r in rows if r.get("hard") is not None]
    if not rows:
        return None
    hards = sorted(r["hard"] for r in rows)
    terms = [r["term"] for r in rows if r.get("term") is not None]
    a_int, b_slope, r_corr = linreg([r["a"] for r in rows], [r["b"] for r in rows])
    rma_a, rma_b = rma([r["a"] for r in rows], [r["b"] for r in rows])
    st = {"n": len(rows),
          "hard_mean": mean(hards),
          "hard_median": pctile(hards, 50),
          "hard_p90": pctile(hards, S["hard_pct"]),
          "hard_pct_used": S["hard_pct"],
          "rd_mean": mean([r["rd"] for r in rows]),
          "ard_mean": mean([r["ard"] for r in rows]),
          "cv_mean": mean([r["cv"] for r in rows]),
          "pooled_rp": (F.calc("dup_pooled_rp", s_terms=sum(terms), n=len(terms))
                        if terms else None),
          "r": r_corr, "rma_a": rma_a, "rma_b": rma_b,
          "within": {}}
    for lim in (5, 10, 15, 20, 30):
        st["within"][lim] = 100.0 * sum(1 for h in hards if h <= lim) / len(hards)
    if len(rows) >= S["min_pairs"]:
        st["rating"] = rate(st["hard_p90"], C[crit_key])
    else:
        st["rating"] = R_NA
        st["note"] = (f"only {len(rows)} pairs -- below the minimum of "
                      f"{S['min_pairs']}, so no rating")
    return st


def group_values(rows, key):
    """Distinct values of a grouping dimension, blanks folded into one bucket."""
    seen = []
    for r in rows:
        v = (r.get(key) or "").strip() or "(not recorded)"
        if v not in seen:
            seen.append(v)
    return sorted(seen)


def group_rows(rows, key, value):
    if not key or value is None:
        return list(rows)
    out = []
    for r in rows:
        v = (r.get(key) or "").strip() or "(not recorded)"
        if v == value:
            out.append(r)
    return out


def group_breakdown(rec, key, F, C, S, crit_key):
    """[{group, n, hard_p90, rd_mean, r, rating}] for every value of a
    grouping dimension, worst first so the problem group is at the top."""
    rows = rec["rows"]
    out = []
    for g in group_values(rows, key):
        st = dup_stats(group_rows(rows, key, g), F, C, S, crit_key)
        if st:
            st["group"] = g
            out.append(st)
    out.sort(key=lambda d: (-(d["hard_p90"] or 0)))
    return out


# ===========================================================================
#  Thompson & Howarth precision regression
# ===========================================================================
MIN_TH_BINS = 3
MIN_TH_GROUP = 5


def _th_bins(rows, g):
    out = []
    for i in range(0, len(rows) - g + 1, g):
        chunk = rows[i:i + g]
        if len(chunk) < g:
            break
        out.append({"n": len(chunk),
                    "conc": mean([c["mean"] for c in chunk]),
                    "dbar": mean([c["diff"] for c in chunk])})
    return out


def analyse_th(project, F, C, S, dups, log=print):
    """Thompson & Howarth binned precision regression.

    The 1978 paper bins 11 pairs at a time, but that is a convention, not a
    requirement: the regression needs at least three bins to mean anything.
    When the requested bin size cannot deliver three bins, the bin size is
    reduced (never below MIN_TH_GROUP) and the size actually used is reported
    on the chart. If even that fails, the reason is recorded instead of the
    method silently producing nothing."""
    out = {}
    skipped = []
    g_req = max(MIN_TH_GROUP, int(S["th_group"]))
    for (dtype, el), rec in dups.items():
        rows = [r for r in rec["rows"] if r["mean"] is not None and r["mean"] > 0]
        g = g_req
        bins = _th_bins(rows, g)
        while len(bins) < MIN_TH_BINS and g > MIN_TH_GROUP:
            g -= 1
            bins = _th_bins(rows, g)
        if len(bins) < MIN_TH_BINS:
            need = MIN_TH_BINS * MIN_TH_GROUP
            skipped.append((dtype, el,
                            f"{len(rows)} usable pairs. The regression needs at "
                            f"least {MIN_TH_BINS} bins, so at least {need} pairs "
                            f"even at the smallest bin size of {MIN_TH_GROUP}. "
                            f"Insert more duplicates of this class, or lower the "
                            f"bin size in Settings if you accept coarser bins."))
            continue
        rows.sort(key=lambda r: r["mean"])
        bins = _th_bins(rows, g)
        cs = [bb["conc"] for bb in bins]
        ds = [bb["dbar"] for bb in bins]
        a_int, b_slope, r_corr = linreg(cs, ds)
        if a_int is None:
            skipped.append((dtype, el, "the binned points are collinear in x; "
                                       "no regression can be fitted."))
            continue

        # The intercept is the mean absolute difference at zero concentration,
        # so it cannot be negative. An unconstrained fit on few bins spanning a
        # wide grade range routinely returns a negative one, which then yields a
        # negative precision and a negative detection limit. When that happens
        # the model is refitted through the origin, which is the constrained
        # form of the same model rather than a cosmetic clamp.
        constrained = False
        if a_int < 0:
            sxx = sum(c * c for c in cs)
            if sxx <= 0:
                skipped.append((dtype, el, "all binned concentrations are zero."))
                continue
            b_slope = sum(c * d for c, d in zip(cs, ds)) / sxx
            a_int = 0.0
            constrained = True

        if b_slope <= 0:
            skipped.append((dtype, el,
                            "the fitted slope is not positive, so absolute "
                            "difference does not grow with grade. With this few "
                            "bins that is noise rather than a real result; treat "
                            "the rank-HARD statistics as the precision measure "
                            "for this set."))
            continue

        dl = rec.get("dl")
        # never read the curve below the lowest bin -- that is extrapolation
        # into the region the regression knows nothing about
        c_lo, c_hi = min(cs), max(cs)
        c_req = (dl * S["th_at_dl"]) if dl else bins[len(bins) // 2]["conc"]
        c_ref = min(max(c_req, c_lo), c_hi)
        clamped = abs(c_ref - c_req) > 1e-12
        prec = F.calc("th_precision", a_int=a_int, b_slope=b_slope, c=c_ref)
        rr = {"type": dtype, "element": el, "bins": bins, "group": g,
              "a_int": a_int, "b_slope": b_slope, "r": r_corr,
              "c_ref": c_ref, "c_requested": c_req, "clamped": clamped,
              "constrained": constrained, "dl": dl,
              "c_lo": c_lo, "c_hi": c_hi,
              "precision_at_ref": prec,
              "sigma_at_ref": F.calc("th_sigma",
                                     dbar=a_int + b_slope * c_ref),
              "pdl": (F.calc("th_pdl", a_int=a_int) if a_int > 0 else None),
              "curve": [], "ratings": {}, "rating": R_NA, "score": None}
        lo, hi = c_lo, c_hi
        for i in range(60):
            c = lo + (hi - lo) * i / 59.0
            if c <= 0:
                continue
            p = F.calc("th_precision", a_int=a_int, b_slope=b_slope, c=c)
            if p is not None:
                rr["curve"].append((c, p))
        rr["ratings"]["th_precision"] = rate(
            abs(prec) if prec is not None else None, C["th_precision"])
        rr["rating"], rr["score"] = combine_ratings([rr["ratings"]["th_precision"]])
        rr["group_requested"] = g_req
        out[(dtype, el)] = rr
    out["_skipped"] = skipped
    return out


# ===========================================================================
#  Check / umpire assays
# ===========================================================================
#  A duplicate measures PRECISION: the same laboratory, the same method, twice.
#  A check (umpire) assay measures ACCURACY BETWEEN LABORATORIES: the same
#  pulp, two different laboratories. The statistics are therefore different.
#  HARD is not the headline number here -- the grade-weighted bias is, because
#  that is the figure that moves contained metal.
# ===========================================================================
def _match_element(name, elements):
    """Match an umpire column to a primary element, allowing lab suffixes."""
    n = name.strip().lower()
    for e in elements:
        if n == e.strip().lower():
            return e
    for e in elements:
        el = e.strip().lower()
        if n.startswith(el) or el.startswith(n):
            return e
    for e in elements:
        el = e.strip().lower()
        base = el.split("_")[0]
        if base and n.startswith(base):
            return e
    return None


def build_umpire(project, S, RB, log=print):
    """Return {element: [(sample_id, primary, umpire)]} plus the umpire lab name."""
    by_id = {}
    for smp in project.samples:
        if not smp.dropped:
            by_id.setdefault(smp.sid.strip().upper(), smp)
    pairs = {}
    lab = ""

    # (a) a separate results file from the second laboratory
    ut = project.umpire
    if ut is not None:
        cols = [c for c, k in ut.value_cols if k == "numeric"] or [
            c for c in ut.header if c not in ut.mapping.values()]
        colmap = {}
        for c in cols:
            e = _match_element(c, project.elements)
            if e:
                colmap[c] = e
        if not colmap:
            log("  ! no umpire column could be matched to a primary element.")
        udc = getattr(ut, "decimal_comma", False)
        for r in ut.rows:
            sid = str(ut.get(r, "sampleid") or "").strip()
            if not sid:
                continue
            prim = by_id.get(sid.upper())
            if prim is None or prim.excl_all:
                continue
            if not lab:
                lab = str(ut.get(r, "lab") or "").strip()
            for c, e in colmap.items():
                if not usable(prim, e):
                    continue
                a = prim.vals.get(e)
                b, flag, _ = parse_value(ut.col(r, c), RB, decimal_comma=udc)
                if b is None or (flag == ">" and RB["clean_C08"]):
                    continue
                pairs.setdefault(e, []).append(
                    (sid, a, b, prim.hole, prim.batch, prim.drilltype, prim.lab))

    # (b) umpire rows inside the main table, keyed by parent sample
    for smp in project.samples:
        if smp.stype != T_UMP or not smp.parent or smp.dropped or smp.excl_all:
            continue
        prim = by_id.get(smp.parent.strip().upper())
        if prim is None or prim.excl_all:
            continue
        if not lab:
            lab = smp.lab
        for e in project.elements:
            if not usable(prim, e) or not usable(smp, e):
                continue
            a, b = prim.vals.get(e), smp.vals.get(e)
            pairs.setdefault(e, []).append(
                (smp.sid, a, b, prim.hole, prim.batch, prim.drilltype, prim.lab))

    for e, lst in pairs.items():
        log(f"  CHECK / UMPIRE {e}: {len(lst)} pair(s)")
    return pairs, lab


def analyse_umpire(project, F, C, S, RB, log=print):
    out = {}
    pairs, lab = build_umpire(project, S, RB, log=log)
    for el, lst in pairs.items():
        dl = detection_limit(project, el, S)
        rows = []
        for item in lst:
            sid, a, b = item[0], item[1], item[2]
            hole, batch, drilltype, plab = (list(item[3:]) + ["", "", "", ""])[:4]
            if a is None or b is None or a + b <= 0:
                continue
            if dl and S["drop_below_dl"] and (a < dl or b < dl):
                continue
            rows.append({
                "sample": sid, "primary": a, "umpire": b,
                "hole": hole, "batch": batch, "drilltype": drilltype, "lab": plab,
                "a": a, "b": b,
                "mean": (a + b) / 2.0, "diff": b - a,
                "bias": F.calc("ump_bias", pr=a, u=b),
                "ratio": F.calc("ump_ratio", pr=a, u=b),
                "hard": F.calc("ump_hard", pr=a, u=b)})
        if len(rows) < 3:
            continue

        sp = sum(r["primary"] for r in rows)
        su = sum(r["umpire"] for r in rows)
        wbias = F.calc("ump_weighted_bias", sum_pr=sp, sum_u=su)
        biases = [r["bias"] for r in rows if r["bias"] is not None]
        ratios = sorted(r["ratio"] for r in rows if r["ratio"] is not None)
        hards = sorted(r["hard"] for r in rows if r["hard"] is not None)
        diffs = [r["diff"] for r in rows]

        _, ols_b, r_corr = linreg([r["primary"] for r in rows],
                                  [r["umpire"] for r in rows])
        rma_a, rma_b = rma([r["primary"] for r in rows],
                           [r["umpire"] for r in rows])

        # bias by grade quartile -- an average hides a high-grade-only bias
        srt = sorted(rows, key=lambda r: r["primary"])
        q = max(1, len(srt) // 4)
        quart = []
        for i in range(4):
            chunk = srt[i * q:(i + 1) * q] if i < 3 else srt[3 * q:]
            if not chunk:
                continue
            cp = sum(c["primary"] for c in chunk)
            cu = sum(c["umpire"] for c in chunk)
            quart.append({
                "q": i + 1, "n": len(chunk),
                "lo": chunk[0]["primary"], "hi": chunk[-1]["primary"],
                "bias": F.calc("ump_weighted_bias", sum_pr=cp, sum_u=cu)})
        worst_q = max((abs(x["bias"]) for x in quart if x["bias"] is not None),
                      default=None)

        rec = {"element": el, "n": len(rows), "rows": rows, "lab": lab, "dl": dl,
               "sum_primary": sp, "sum_umpire": su,
               "mean_primary": sp / len(rows), "mean_umpire": su / len(rows),
               "wbias": wbias, "pbias": mean(biases),
               "median_ratio": pctile(ratios, 50),
               "hard_p90": pctile(hards, S["hard_pct"]),
               "hard_median": pctile(hards, 50),
               "hard_pct_used": S["hard_pct"],
               "r": r_corr, "ols_b": ols_b, "rma_a": rma_a, "rma_b": rma_b,
               "quartiles": quart, "worst_quartile": worst_q,
               "ttest": paired_t(diffs), "wilcoxon": wilcoxon(diffs),
               "ratings": {}, "rating": R_NA, "score": None}

        if len(rows) >= S["min_pairs"]:
            rec["ratings"]["ump_wbias"] = rate(
                abs(wbias) if wbias is not None else None, C["ump_wbias"])
            rec["ratings"]["ump_pbias"] = rate(
                abs(rec["pbias"]) if rec["pbias"] is not None else None,
                C["ump_pbias"])
            rec["ratings"]["ump_hard90"] = rate(rec["hard_p90"], C["ump_hard90"])
            rec["ratings"]["ump_grade_range"] = rate(worst_q, C["ump_grade_range"])
            rec["rating"], rec["score"] = combine_ratings(
                [rec["ratings"]["ump_wbias"], rec["ratings"]["ump_pbias"],
                 rec["ratings"]["ump_hard90"], rec["ratings"]["ump_grade_range"]],
                [4.0, 2.0, 1.5, 3.0])
        else:
            rec["note"] = (f"Only {len(rows)} usable pairs. Below the minimum of "
                           f"{S['min_pairs']} an inter-laboratory bias cannot be "
                           f"separated from chance, so no rating is given.")
        out[el] = rec
    return out


# ===========================================================================
#  Insertion rates
# ===========================================================================
def analyse_insertion(project, F, C, S, pairs, log=print):
    """Insertion rates. A mislabelled control (C13-C15) was still inserted and
    still counts; only rows that are not samples at all (C02, C03) do not."""
    live = [s for s in project.samples if not s.dropped]
    n_total = len(live)
    counts = {t: 0 for t in SAMPLE_TYPES}
    for s in live:
        counts[s.stype] = counts.get(s.stype, 0) + 1
    out = {"n_total": n_total, "rows": [], "rating": R_NA, "score": None}
    ratings = []
    n_blank_all = sum(counts.get(t, 0) for t in BLANK_TYPES)
    for t in (T_CRM, T_BLANK, T_FDUP, T_CDUP, T_PDUP):
        n = n_blank_all if t == T_BLANK else counts.get(t, 0)
        pct = F.calc("insert_rate", n_control=n, n_total=n_total) if n_total else None
        every = (F.calc("insert_interval", n_control=n, n_total=n_total)
                 if n else None)
        r = rate(pct, C["insert_rate"]) if n_total else R_NA
        # a control class that is simply absent is a finding in itself
        if n == 0:
            r = R_VBAD
        out["rows"].append({"type": t, "n": n, "pct": pct, "every": every,
                            "rating": r})
        ratings.append(r)
    # coarse and pulp blanks are listed for information; the 5 % convention
    # applies to blanks as a class
    for t in (T_CBLANK, T_PBLANK):
        n = counts.get(t, 0)
        if n:
            out["rows"].append({
                "type": t, "n": n, "info_only": True, "rating": R_NA,
                "pct": F.calc("insert_rate", n_control=n, n_total=n_total),
                "every": F.calc("insert_interval", n_control=n, n_total=n_total)})
    out["counts"] = counts
    out["rating"], out["score"] = combine_ratings(ratings)
    return out


# ===========================================================================
#  Driver
# ===========================================================================
def run_analysis(project, F, C, S, RB, log=print):
    log("Building the sample population ...")
    build_samples(project, S, log=log)
    log("Cleaning the data ...")
    project.excluded_pairs = set()
    clean_values(project, S, RB, log=log)
    log("Pairing duplicates ...")
    pairs = build_pairs(project, S, log=lambda m: None)
    clean_pairs(project, pairs, S, RB, log=log)
    pairs = build_pairs(project, S, log=log)
    log("Analysing CRMs ...")
    crm = analyse_crm(project, F, C, S, RB, log=log)
    log("Analysing blanks ...")
    blank = analyse_blank(project, F, C, S, RB, log=log)
    log("Analysing duplicates ...")
    dup = analyse_duplicates(project, F, C, S, RB, pairs, log=log)
    log("Fitting Thompson-Howarth precision ...")
    th = analyse_th(project, F, C, S, dup, log=log)
    th_skipped = th.pop("_skipped", [])
    for dt, el, why in th_skipped:
        log(f"  Thompson-Howarth not fitted for {dt} / {el}: {why}")
    log("Analysing check / umpire assays ...")
    ump = analyse_umpire(project, F, C, S, RB, log=log)
    log("Checking insertion rates ...")
    ins = analyse_insertion(project, F, C, S, pairs, log=log)
    log("Accuracy curve, grade coverage, error budget, batch acceptance ...")
    accuracy = analyse_accuracy_curve(crm)
    drift = analyse_drift(crm, RB)
    coverage = analyse_coverage(project, RB)
    budget = analyse_error_budget(dup, S)
    batches = analyse_batches(project, crm, blank, S, RB)

    ratings, weights = [], []
    for rec in crm.values():
        if rec["rating"] != R_NA:
            ratings.append(rec["rating"])
            weights.append(3.0)
    for rec in blank.values():
        if rec["rating"] != R_NA:
            ratings.append(rec["rating"])
            weights.append(1.5)
    for rec in dup.values():
        if rec["rating"] != R_NA:
            ratings.append(rec["rating"])
            weights.append(2.5)
    for rec in ump.values():
        if rec["rating"] != R_NA:
            ratings.append(rec["rating"])
            weights.append(3.0)
    if ins["rating"] != R_NA:
        ratings.append(ins["rating"])
        weights.append(1.0)
    overall, score = combine_ratings(ratings, weights)

    project.results = {"crm": crm, "blank": blank, "dup": dup, "th": th,
                       "umpire": ump, "th_skipped": th_skipped,
                       "insertion": ins, "pairs": pairs,
                       "clean_log": project.clean_log,
                       "accuracy": accuracy, "coverage": coverage,
                       "drift": drift,
                       "budget": budget, "batches": batches,
                       "overall": overall, "score": score}
    project.analysed_at = _dt.datetime.now()
    log(f"Analysis complete. Overall QA/QC rating: {overall}"
        + (f"  (score {score:.1f}/100)" if score is not None else ""))
    return project.results


# ===========================================================================
#  2.0 -- CRM: drift, CUSUM, batch bias, repeatability against certificate
# ===========================================================================
def _crm_extras(rec, S, RB):
    pts = rec["points"]
    idx = [i for i, p in enumerate(pts) if p["bias"] is not None]
    st = linreg_stats(idx, [pts[i]["bias"] for i in idx])
    if st is not None:
        total = st["b"] * (len(pts) - 1)
        rec["drift"] = {"slope": st["b"], "total": total, "p": st["p"],
                        "a": st["a"],
                        "sig": bool(st["p"] < RB["drift_p"]
                                    and abs(total) >= RB["drift_total"])}
    zs = [p["z"] for p in pts]
    if any(z is not None for z in zs):
        rec["cusum"] = cusum(zs, RB["cusum_k"], RB["cusum_h"])
    order, groups = [], {}
    for p in pts:
        b = p["batch"] or "(not recorded)"
        if b not in groups:
            order.append(b)
            groups[b] = []
        groups[b].append(p)
    for b in order:
        g = groups[b]
        zz = [abs(p["z"]) for p in g if p["z"] is not None]
        rec["batch_bias"].append({
            "batch": b, "n": len(g),
            "bias": mean([p["bias"] for p in g if p["bias"] is not None]),
            "zmax": max(zz) if zz else None})
    if rec.get("sd") and rec.get("cert") and rec.get("rsd_pct") is not None:
        cert_rsd = rec["sd"] / rec["cert"] * 100.0
        rec["rsd_ratio"] = rec["rsd_pct"] / cert_rsd if cert_rsd else None


def analyse_drift(crm, RB):
    """Laboratory drift per element: the bias of EVERY CRM of the element in
    analytical sequence, regressed on rank. A laboratory drift moves all CRMs
    together, so pooling them is both the right question and a far stronger
    test than one CRM at a time, which also multiplies false alarms."""
    out = {}
    by_el = {}
    for (label, el), rec in crm.items():
        for p in rec["points"]:
            if p["bias"] is not None:
                by_el.setdefault(el, []).append(
                    (p["order"] if p["order"] is not None else 0, p["bias"], label))
    for el, pts in by_el.items():
        pts.sort(key=lambda x: x[0])
        st = linreg_stats(list(range(len(pts))), [b for _, b, _ in pts])
        if st is None:
            continue
        total = st["b"] * (len(pts) - 1)
        out[el] = {"n": len(pts), "slope": st["b"], "a": st["a"], "total": total,
                   "p": st["p"], "n_crm": len({x[2] for x in pts}),
                   "series": [(o, b, lab) for o, b, lab in pts],
                   "sig": bool(st["p"] < RB["drift_p"]
                               and abs(total) >= RB["drift_total"])}
    return out


def analyse_accuracy_curve(crm):
    """Mean measured against certified value over every CRM of an element.
    slope - 1 is a proportional bias (calibration), the intercept a constant
    one (baseline / blank correction)."""
    by_el = {}
    for (label, el), rec in crm.items():
        if rec.get("cert") is None or rec.get("obs_mean") is None:
            continue
        by_el.setdefault(el, []).append({
            "crm": label, "cert": rec["cert"], "mean": rec["obs_mean"],
            "n": rec["n"], "bias": rec.get("bias")})
    out = {}
    for el, pts in by_el.items():
        pts.sort(key=lambda p: p["cert"])
        rec = {"points": pts, "n_crm": len(pts), "a": None, "b": None,
               "prop_bias_pct": None, "const_bias": None, "p_slope": None}
        if len(pts) >= 2:
            xs, ys = [p["cert"] for p in pts], [p["mean"] for p in pts]
            a, b, _ = linreg(xs, ys)
            if b is not None:
                rec.update(a=a, b=b, prop_bias_pct=(b - 1.0) * 100.0,
                           const_bias=a)
            st = linreg_stats(xs, ys) if len(pts) >= 3 else None
            if st is not None:
                if st["se_b"] > 0:
                    t = (st["b"] - 1.0) / st["se_b"]
                    rec["p_slope"] = t_two_tail_p(t, st["n"] - 2)
                else:
                    rec["p_slope"] = 0.0 if st["b"] != 1.0 else 1.0
        out[el] = rec
    return out


def analyse_coverage(project, RB):
    """Do the CRMs bracket the grades that matter? Percentiles of the routine
    samples against the certified values of the CRMs actually inserted."""
    out = {}
    inserted = {s.crm_key for s in project.samples
                if s.stype == T_CRM and not s.dropped and s.crm_key}
    for el in project.elements:
        vals = sorted(s.vals[el] for s in project.samples
                      if s.stype == T_NORMAL and usable(s, el)
                      and s.flags.get(el) != "<")
        certs = [(project.crm_labels.get(k, k), c["cert"])
                 for (k, e), c in project.certs.items()
                 if e == el and k in inserted]
        if not vals:
            continue
        pcts = {float(q): pctile(vals, float(q)) for q in RB["coverage_pcts"]}
        lo_q, hi_q = min(pcts), max(pcts)
        mid_q = sorted(pcts)[len(pcts) // 2]
        cv = [c for _, c in certs]
        out[el] = {"pcts": pcts, "certs": certs, "n": len(vals),
                   "quantiles": [(q, pctile(vals, float(q))) for q in range(101)],
                   "below_p50_only": bool(cv) and max(cv) < pcts[mid_q],
                   "none_above_p90": bool(cv) and max(cv) < pcts[hi_q],
                   "none_below_p10": bool(cv) and min(cv) > pcts[lo_q]}
    return out


# ===========================================================================
#  2.0 -- blanks: carry-over evidence
# ===========================================================================
def _blank_extras(rec, hi_cut):
    pts = rec["points"]
    rec["high_grade_cut"] = hi_cut
    pairs = [(p["prev_value"], p["value"]) for p in pts
             if p["prev_value"] is not None]
    sp = spearman([a for a, _ in pairs], [b for _, b in pairs])
    rec["rho"] = sp["rho"] if sp else None
    rec["rho_p"] = sp["p"] if sp else None
    ratios = sorted(p["ratio"] for p in pts if p["ratio"] is not None)
    rec["median_ratio"] = pctile(ratios, 50)
    high = [p for p in pts if p["prev_value"] is not None
            and p["prev_value"] >= hi_cut]
    other = [p for p in pts if p not in high]
    rec["n_after_high"] = len(high)
    rec["fail_after_high_pct"] = (100.0 * sum(p["fail"] for p in high) / len(high)
                                  if high else None)
    rec["fail_other_pct"] = (100.0 * sum(p["fail"] for p in other) / len(other)
                             if other else None)


# ===========================================================================
#  2.0 -- duplicates: max-min, grade quartiles, splitting bias, CV^2
# ===========================================================================
def _dup_extras(rec, F, C, S, RB, crit_key):
    rows = rec["rows"]
    for r in rows:
        r["cv2"] = F.calc("dup_cv2", a=r["a"], b=r["b"])
    cv2 = [r["cv2"] for r in rows if r["cv2"] is not None]
    rec["cv2_mean"] = mean(cv2)
    h = C[crit_key]["cuts"][2]                    # the GOOD boundary
    fails = sum(1 for r in rows if r["hard"] is not None and r["hard"] > h)
    fail_pct = 100.0 * fails / len(rows)
    rec["maxmin"] = {"limit_hard": h,
                     "ratio_line": (1 + h / 100.0) / (1 - h / 100.0) if h < 100 else None,
                     "fail_pct": fail_pct,
                     "rating": rate(fail_pct, C["maxmin_fail"])}
    srt = sorted(rows, key=lambda r: r["mean"])
    q = max(1, len(srt) // 4)
    quart = []
    for i in range(4):
        chunk = srt[i * q:(i + 1) * q] if i < 3 else srt[3 * q:]
        if not chunk:
            continue
        hh = sorted(c["hard"] for c in chunk if c["hard"] is not None)
        quart.append({"q": i + 1, "n": len(chunk), "lo": chunk[0]["mean"],
                      "hi": chunk[-1]["mean"],
                      "hard_p90": pctile(hh, S["hard_pct"]),
                      "hard_median": pctile(hh, 50)})
    rec["quartiles"] = quart
    lr = [math.log(r["a"] / r["b"]) for r in rows if r["a"] > 0 and r["b"] > 0]
    t = paired_t(lr)
    w = wilcoxon(lr)
    good_bias = C["dup_bias"]["cuts"][2]
    rec["split"] = {"t": t, "wilcoxon": w,
                    "sig": bool(t is not None and t["p"] is not None
                                and t["p"] < RB["split_p"]
                                and rec["rd_mean"] is not None
                                and abs(rec["rd_mean"]) > good_bias)}


# ===========================================================================
#  2.0 -- error budget: which stage of the sample chain makes the error
# ===========================================================================
_STAGE_OF = {T_FDUP: "field", T_CDUP: "coarse", T_PDUP: "pulp"}


def analyse_error_budget(dup, S):
    """Relative variance of each stage from the mean pair CV^2 of each class:
    pulp duplicates carry the analytical variance, coarse duplicates add the
    preparation (sub-sampling) variance, field duplicates add the sampling
    variance. Stage variance = difference of consecutive classes; a negative
    difference is sampling noise and is set to zero with a note. A missing
    class merges the two stages it would have separated."""
    out = {}
    els = sorted({el for (_, el) in dup})
    for el in els:
        cv2 = {}
        for dtype, name in _STAGE_OF.items():
            rec = dup.get((dtype, el))
            if rec and rec["n"] >= S["min_pairs"] and rec.get("cv2_mean") is not None:
                cv2[name] = rec["cv2_mean"]
        if len(cv2) < 2:
            if cv2:
                out[el] = {"cv2": cv2, "stages": {}, "pct": {}, "merged": None,
                           "dominant": None, "total_cv_pct": None,
                           "notes": ["only one duplicate class has enough pairs; "
                                     "the error cannot be split by stage"]}
            continue
        notes = []
        f, c, p = cv2.get("field"), cv2.get("coarse"), cv2.get("pulp")
        stages, merged = {}, None

        def diff(hi, lo, name):
            d = hi - lo
            if d < 0:
                notes.append(f"{name}: the finer class is noisier than the coarser "
                             f"one; variance set to zero")
                d = 0.0
            return d

        if f is not None and c is not None and p is not None:
            stages = {"sampling": diff(f, c, "sampling"),
                      "preparation": diff(c, p, "preparation"),
                      "analytical": p}
        elif f is not None and p is not None:
            merged = "sampling+preparation"
            stages = {merged: diff(f, p, merged), "analytical": p}
        elif f is not None and c is not None:
            merged = "preparation+analytical"
            stages = {"sampling": diff(f, c, "sampling"), merged: c}
        else:
            merged = "sampling"
            stages = {"preparation": diff(c, p, "preparation"), "analytical": p}
            notes.append("no field duplicates: the sampling variance is not "
                         "measured")
        total = sum(stages.values())
        pct = {k: (100.0 * v / total if total > 0 else None) for k, v in stages.items()}
        dom = max(pct, key=lambda k: pct[k] or 0) if total > 0 else None
        top = f if f is not None else (c if c is not None else p)
        out[el] = {"cv2": cv2, "stages": stages, "pct": pct,
                   "merged": None if merged == "sampling" else merged,
                   "unmeasured": "sampling" if merged == "sampling" else None,
                   "dominant": dom, "total_cv_pct": math.sqrt(top) * 100.0,
                   "notes": notes}
    return out


# ===========================================================================
#  2.0 -- batch acceptance and re-assay ranges
# ===========================================================================
def _rule_family(name):
    return "10x" if name.endswith("x") else name


def _crm_point_rules(rec, S):
    """{sample id: set of rule names} for every CRM point of a record."""
    out = {}
    for p in rec["points"]:
        z = p["z"]
        rules = set()
        if z is not None and abs(z) > S["k_fail"]:
            rules.add("1-3s")
        if z is not None and abs(z) > S["k_warn"]:
            rules.add("2s")
        out[p["sample"]] = rules
    for r in rec["rules"]:
        out.setdefault(r["sample"], set()).add(_rule_family(r["rule"]))
    return out


def analyse_batches(project, crm, blank, S, RB):
    fail_rules = set(RB["batch_fail_rules"])
    warn_rules = set(RB["batch_warn_rules"])
    live = sorted([s for s in project.samples if not s.dropped],
                  key=lambda s: (s.order if s.order is not None else 0))
    batch_order, n_by_batch = [], {}
    for s in live:
        b = s.batch or "(not recorded)"
        if b not in n_by_batch:
            batch_order.append(b)
            n_by_batch[b] = 0
        n_by_batch[b] += 1
    out = {}
    for el in project.elements:
        crm_pts = []                      # (order, sample, label, rules, batch)
        for (label, e), rec in crm.items():
            if e != el or rec.get("cert") is None:
                continue
            pr = _crm_point_rules(rec, S)
            for p in rec["points"]:
                crm_pts.append((p["order"] if p["order"] is not None else 0,
                                p["sample"], label, pr.get(p["sample"], set()),
                                p["batch"] or "(not recorded)"))
        crm_pts.sort(key=lambda x: x[0])
        blank_pts = []
        for (bt, e), rec in blank.items():
            if e == el:
                blank_pts += [(p["batch"] or "(not recorded)", p["sample"], p["fail"],
                               bt) for p in rec["points"]]
        rows = []
        for b in batch_order:
            cp = [x for x in crm_pts if x[4] == b]
            bp = [x for x in blank_pts if x[0] == b]
            reasons = []
            if not cp:
                crm_status = "NONE"
            else:
                crm_status = "PASS"
                for _, sid, label, rules, _ in cp:
                    hit_f = rules & fail_rules
                    hit_w = rules & warn_rules
                    if hit_f:
                        crm_status = "FAIL"
                        reasons.append(f"{label} {'/'.join(sorted(hit_f))} at {sid}")
                    elif hit_w:
                        if crm_status != "FAIL":
                            crm_status = "WARN"
                        reasons.append(f"{label} {'/'.join(sorted(hit_w))} at {sid}")
            if not bp:
                blank_status = "NONE"
            else:
                bad = [x for x in bp if x[2]]
                blank_status = ("PASS" if not bad else
                                "FAIL" if RB["batch_blank_fail"] else "WARN")
                reasons += [f"{x[3].lower()} failed at {x[1]}" for x in bad]
            rank = {"NONE": 0, "PASS": 1, "WARN": 2, "FAIL": 3}
            worst = max((crm_status, blank_status), key=lambda x: rank[x])
            rows.append({"batch": b, "n": n_by_batch[b], "crm_status": crm_status,
                         "blank_status": blank_status, "status": worst,
                         "reasons": reasons})
        # re-assay ranges: samples between the passing CRMs bracketing a failure
        reassay, seen = [], set()
        passing = [x for x in crm_pts if not (x[3] & fail_rules)]
        for x in crm_pts:
            hit = x[3] & fail_rules
            if not hit:
                continue
            before = [y for y in passing if y[0] < x[0]]
            after = [y for y in passing if y[0] > x[0]]
            lo = before[-1][0] if before else None
            hi = after[0][0] if after else None
            span = [s for s in live if s.stype == T_NORMAL
                    and (lo is None or (s.order or 0) > lo)
                    and (hi is None or (s.order or 0) < hi)]
            if not span:
                continue
            key = (span[0].sid, span[-1].sid)
            if key in seen:
                for r in reassay:
                    if (r["from_sample"], r["to_sample"]) == key:
                        r["failed_sample"] += f", {x[1]}"
                        r["rule"] = "/".join(sorted(set(r["rule"].split("/")) | hit))
                continue
            seen.add(key)
            reassay.append({"crm": x[2], "failed_sample": x[1],
                            "from_sample": span[0].sid, "to_sample": span[-1].sid,
                            "n_samples": len(span), "batch": x[4],
                            "rule": "/".join(sorted(hit))})
        out[el] = {"rows": rows, "reassay": reassay,
                   "n_fail": sum(1 for r in rows if r["status"] == "FAIL"),
                   "n_warn": sum(1 for r in rows if r["status"] == "WARN")}
    return out
