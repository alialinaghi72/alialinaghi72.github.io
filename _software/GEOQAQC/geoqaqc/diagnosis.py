# -*- coding: utf-8 -*-
"""From statistics to findings: what is wrong, in which stage of the sample
chain, how serious, why, and what to do.

A finding's severity is never invented here: it comes from the rating of the
criterion that measures the problem (Criteria tab), mapped through the
editable severity table (Rules tab). Where a finding has no criterion of its
own (a significant drift, a swap) the size of the effect is rated on the
nearest criterion, with MINOR as the floor -- a significant problem is never
silently dropped.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .core import (BLANK_TYPES, DUP_TYPES, R_BAD, R_POOR, R_VBAD,
                   T_CBLANK, T_CDUP, T_CRM, T_FDUP, T_PBLANK, T_PDUP, mean)
from .protocol import rate
from .report import texts_fa as T

STAGES = ["SAMPLING", "PREPARATION", "ACCURACY", "PRECISION", "CONTAMINATION",
          "INTERLAB", "DATA", "PROGRAMME"]
SEVERITIES = ["CRITICAL", "MATERIAL", "MINOR"]
STAGE_EN = {"SAMPLING": "Sampling", "PREPARATION": "Preparation",
            "ACCURACY": "Analytical accuracy", "PRECISION": "Analytical precision",
            "CONTAMINATION": "Contamination", "INTERLAB": "Inter-laboratory",
            "DATA": "Data management", "PROGRAMME": "QC programme design"}
STAGE_FA = T.STAGE_FA
TIMINGS = ["IMMEDIATE", "BEFORE_ESTIMATE", "ONGOING"]

_DUP_STAGE = {T_FDUP: "SAMPLING", T_CDUP: "PREPARATION", T_PDUP: "PRECISION"}
_DUP_OWNER = {T_FDUP: "SITE", T_CDUP: "LAB", T_PDUP: "LAB"}
_DUP_CRIT = {T_FDUP: "fdup_hard90", T_CDUP: "cdup_hard90", T_PDUP: "pdup_hard90"}
_BUDGET_STAGE = {"sampling": "SAMPLING", "preparation": "PREPARATION",
                 "analytical": "PRECISION", "sampling+preparation": "SAMPLING",
                 "preparation+analytical": "PREPARATION"}

TITLE_EN = {
    "CRM_BIAS": "CRM bias", "CRM_SYSTEMATIC": "Systematic laboratory bias",
    "CRM_DRIFT": "Laboratory drift", "CRM_FAIL": "CRM failures",
    "CRM_CLUSTER": "CRM failures clustered in batches",
    "CRM_RSD": "Poor repeatability on CRM", "CRM_NOCERT": "CRM without certificate",
    "CRM_COVERAGE": "CRMs do not cover the grade range",
    "BLK_FAIL": "Blank failures", "BLK_CARRY": "Carry-over contamination",
    "BLK_MATERIAL": "Blank material not barren",
    "BLK_PREP": "Contamination in sample preparation",
    "DUP_PRECISION": "Poor duplicate precision", "DUP_SPLIT": "Splitting bias",
    "BUDGET_DOMINANT": "Dominant source of error",
    "TH_PRECISION": "Poor precision near detection limit",
    "UMP_BIAS": "Inter-laboratory bias", "UMP_GRADE": "Grade-dependent inter-lab bias",
    "INS_RATE": "Low insertion rate", "INS_MISSING": "Control class missing",
    "DATA_SWAP": "Mislabelled control samples", "DATA_UNIT": "Unit / decimal errors",
    "DATA_DUPID": "Duplicate sample IDs", "DATA_ORPHAN": "Duplicates without parent",
    "DATA_CODES": "Text codes and non-numeric values",
}


@dataclass
class Finding:
    code: str
    element: str            # "" for a project-wide finding
    stage: str
    severity: str
    title_en: str
    title_fa: str
    evidence_fa: str
    cause_fa: str
    actions_fa: list
    owner: str
    timing: str
    figures: list = field(default_factory=list)
    subject: str = ""       # CRM label, blank or duplicate class, ...


def severity_from_rating(rating, RB):
    key = {R_POOR: "sev_POOR", R_BAD: "sev_BAD", R_VBAD: "sev_VERY BAD"}.get(rating)
    if not key:
        return None
    s = RB[key]
    return None if s == "NONE" else s


def _worst(*sevs):
    sevs = [s for s in sevs if s]
    return min(sevs, key=SEVERITIES.index) if sevs else None


class Diagnosis:
    def __init__(self, elements, RB):
        self.elements = list(elements)
        self.RB = RB
        self.findings = []

    # -- building ----------------------------------------------------------
    def add(self, code, element, stage, severity, texts, owner, timing,
            figures=(), subject=""):
        title, evidence, cause, actions = texts
        if severity == "CRITICAL":
            timing = "IMMEDIATE"
        self.findings.append(Finding(code, element, stage, severity,
                                     TITLE_EN.get(code, code), title, evidence,
                                     cause, list(actions), owner, timing,
                                     list(figures), subject))

    # -- reading -----------------------------------------------------------
    def by_element(self, el):
        return [f for f in self.findings if f.element == el]

    def project_findings(self):
        return [f for f in self.findings if not f.element]

    def counts(self, el=None):
        lst = self.by_element(el) if el else self.findings
        return {s: sum(1 for f in lst if f.severity == s) for s in SEVERITIES}

    def verdict(self, el):
        """(code, Persian text) -- spec 6."""
        stages = set(self.RB["verdict_stages"])
        own = self.by_element(el)
        proj = [f for f in self.project_findings() if f.stage == "PROGRAMME"]
        block = [f for f in own if f.severity == "CRITICAL" and f.stage in stages]
        if block:
            return "REMEDIATE", T.verdict_text("REMEDIATE", el,
                                               [f.title_fa for f in block])
        limit = [f for f in own if f.severity == "CRITICAL"
                 or (f.severity == "MATERIAL" and f.stage in stages)]
        limit += [f for f in proj if f.severity in ("CRITICAL", "MATERIAL")]
        limit += [f for f in own if f.stage == "PROGRAMME"
                  and f.severity in ("CRITICAL", "MATERIAL") and f not in limit]
        if limit:
            return "RESTRICTED", T.verdict_text("RESTRICTED", el,
                                                [f.title_fa for f in limit])
        minor = [f.title_fa for f in own if f.severity == "MINOR"][:3]
        return "SUITABLE", T.verdict_text("SUITABLE", el, minor)

    def matrix(self):
        """{element: {stage: worst severity or None}}. Project-wide findings
        (programme design, data management) apply to every element."""
        out = {}
        proj = self.project_findings()
        for el in self.elements:
            row = {s: None for s in STAGES}
            for f in self.by_element(el) + proj:
                row[f.stage] = _worst(row[f.stage], f.severity)
            out[el] = row
        return out

    def actions(self):
        order = {el: i for i, el in enumerate(self.elements)}
        return sorted(self.findings, key=lambda f: (
            SEVERITIES.index(f.severity), TIMINGS.index(f.timing),
            order.get(f.element, -1), f.code))


# ===========================================================================
#  The rules
# ===========================================================================
def diagnose(project, results, C, S, RB):
    R = results
    d = Diagnosis(project.elements, RB)
    sev = lambda rating: severity_from_rating(rating, RB)     # noqa: E731
    for el in project.elements:
        _crm(d, el, R, C, S, RB, sev)
        _blanks(d, el, R, C, S, RB, sev)
        _dups(d, el, R, C, S, RB, sev)
        _umpire(d, el, R, C, S, RB, sev)
    _programme(d, project, R, C, S, RB, sev)
    _data(d, project, R, C, S, RB, sev)
    return d


# ---- accuracy ----------------------------------------------------------------
def _crm(d, el, R, C, S, RB, sev):
    recs = [r for (lab, e), r in sorted(R.get("crm", {}).items())
            if e == el and r.get("cert") is not None]
    rated = [r for r in recs if r["ratings"].get("crm_bias")]
    nocert = sorted({r["crm"] for (lab, e), r in R.get("crm", {}).items()
                     if e == el and r.get("cert") is None})
    if nocert:
        d.add("CRM_NOCERT", el, "DATA", "MATERIAL" if not recs else "MINOR",
              T.f_CRM_NOCERT(el, nocert, none_at_all=not recs), "DATABASE",
              "BEFORE_ESTIMATE")
    if not recs:
        return
    figs = [f"crm/{r['crm']}/{el}" for r in recs]

    # systematic bias: several CRMs, same sign, each beyond sys_bias
    systematic = False
    for sign in (1, -1):
        grp = [r for r in rated if r["bias"] is not None
               and r["bias"] * sign >= RB["sys_bias"]]
        if len(grp) >= RB["sys_min_crm"] and len(grp) * 2 > len(rated):
            systematic = True
            mb = mean([r["bias"] for r in grp])
            acc = R.get("accuracy", {}).get(el) or {}
            kind = "constant"
            if acc.get("prop_bias_pct") is not None:
                mc = mean([p["cert"] for p in acc["points"]]) or 1.0
                const_pct = abs(acc["const_bias"] or 0.0) / mc * 100.0
                if abs(acc["prop_bias_pct"]) >= const_pct:
                    kind = "proportional"
            s = _worst(sev(rate(abs(mb), C["crm_bias"])),
                       *[sev(r["ratings"].get("crm_bias")) for r in grp]) or "MINOR"
            d.add("CRM_SYSTEMATIC", el, "ACCURACY", s,
                  T.f_CRM_SYSTEMATIC(el, len(grp), len(rated),
                                     [r["crm"] for r in grp], mb, kind,
                                     acc.get("b") or 1.0, acc.get("a") or 0.0,
                                     acc.get("prop_bias_pct") or mb,
                                     1.0 / (1.0 + mb / 100.0)),
                  "LAB", "IMMEDIATE", figs + [f"accuracy/{el}"])
    if not systematic:
        bad = [r for r in rated if sev(r["ratings"].get("crm_bias"))]
        if bad:
            w = max(bad, key=lambda r: abs(r["bias"]))
            d.add("CRM_BIAS", el, "ACCURACY",
                  _worst(*[sev(r["ratings"]["crm_bias"]) for r in bad]),
                  T.f_CRM_BIAS(el, w["crm"], w["bias"], w["n"],
                               [r["crm"] for r in bad], len(rated)),
                  "LAB", "IMMEDIATE", figs)

    dr = R.get("drift", {}).get(el)
    if dr and dr["sig"]:
        d.add("CRM_DRIFT", el, "ACCURACY",
              sev(rate(abs(dr["total"]), C["crm_bias"])) or "MINOR",
              T.f_CRM_DRIFT(el, dr["total"], dr["n"], dr["p"], dr["n_crm"]),
              "LAB", "IMMEDIATE", [f"drift/{el}"])

    # failures beyond the action limit
    zrecs = [r for r in recs if r.get("fail_pct") is not None
             and r["n"] >= S["min_crm"]]
    n = sum(r["n"] for r in zrecs)
    fails = [p for r in zrecs for p in r["failures"]]
    if n:
        fp = 100.0 * len(fails) / n
        s_fail = sev(rate(fp, C["crm_fail"]))
        ra = R.get("batches", {}).get(el, {}).get("reassay", [])
        if s_fail:
            d.add("CRM_FAIL", el, "ACCURACY", s_fail,
                  T.f_CRM_FAIL(el, len(fails), n, fp, S["k_fail"], len(ra),
                               sum(x["n_samples"] for x in ra)),
                  "LAB", "IMMEDIATE", [f"batches/{el}"])
            _cluster(d, el, fails, R, RB, s_fail)

    # repeatability against the certificate
    rsd = [r for r in recs if r.get("rsd_ratio") is not None
           and r["n"] >= S["min_crm"] and r["rsd_ratio"] >= RB["rsd_ratio"]]
    if rsd:
        w = max(rsd, key=lambda r: r["rsd_ratio"])
        d.add("CRM_RSD", el, "PRECISION",
              sev(w["ratings"].get("crm_rsd")) or "MINOR",
              T.f_CRM_RSD(el, w["crm"], w["rsd_pct"], w["sd"] / w["cert"] * 100.0,
                          w["rsd_ratio"]),
              "LAB", "ONGOING", [f"crm/{w['crm']}/{el}"])

    cov = R.get("coverage", {}).get(el)
    if cov and cov["certs"] and (cov["none_above_p90"] or cov["none_below_p10"]):
        q = sorted(cov["pcts"])
        cv = [c for _, c in cov["certs"]]
        d.add("CRM_COVERAGE", el, "PROGRAMME", "MINOR",
              T.f_CRM_COVERAGE(el, cov["pcts"][q[-1]], max(cv), cov["pcts"][q[0]],
                               min(cv), cov["none_above_p90"], cov["none_below_p10"]),
              "GEOLOGY", "ONGOING", [f"coverage/{el}"])


def _cluster(d, el, fails, R, RB, s_fail):
    if len(fails) < 2:
        return
    rows = R.get("batches", {}).get(el, {}).get("rows", [])
    nb = sum(1 for r in rows if r["crm_status"] != "NONE") or 1
    cnt = {}
    for p in fails:
        b = p["batch"] or "(not recorded)"
        cnt[b] = cnt.get(b, 0) + 1
    top, acc = [], 0
    for b, c in sorted(cnt.items(), key=lambda x: -x[1]):
        top.append(b)
        acc += c
        if acc / len(fails) >= RB["cluster_frac"]:
            break
    if len(top) < nb and 100.0 * len(top) / nb <= RB["cluster_batches"]:
        d.add("CRM_CLUSTER", el, "ACCURACY", s_fail,
              T.f_CRM_CLUSTER(el, 100.0 * acc / len(fails), len(top), nb, top),
              "LAB", "IMMEDIATE", [f"batches/{el}"])


# ---- contamination -----------------------------------------------------------
def _blanks(d, el, R, C, S, RB, sev):
    blank = R.get("blank", {})
    sevs = {}
    for bt in BLANK_TYPES:
        rec = blank.get((bt, el))
        if not rec:
            continue
        s = sev(rec["rating"])
        sevs[bt] = s
        if not s:
            continue
        figs = [f"blank/{bt}/{el}"]
        d.add("BLK_FAIL", el, "CONTAMINATION", s,
              T.f_BLK_FAIL(el, bt, rec["n_fail"], rec["n"], rec["fail_pct"],
                           rec["limit"], S["k_dl"], rec["max_ratio"]),
              "LAB", "IMMEDIATE", figs, subject=bt)
        cut = rec.get("high_grade_cut")
        failed = [p for p in rec["points"] if p["fail"]]
        after = [p for p in failed if cut is not None and p["prev_value"] is not None
                 and p["prev_value"] >= cut]
        carry = (failed and len(after) / len(failed) >= RB["carry_frac"]
                 and (rec.get("fail_after_high_pct") or 0) > (rec.get("fail_other_pct") or 0))
        if carry:
            batches = sorted({p["batch"] for p in after if p["batch"]})
            d.add("BLK_CARRY", el, "CONTAMINATION", s,
                  T.f_BLK_CARRY(el, bt, rec["fail_after_high_pct"],
                                rec["fail_other_pct"] or 0.0, rec.get("rho"),
                                batches),
                  "LAB", "IMMEDIATE", figs + [f"blankprev/{bt}/{el}"], subject=bt)
        elif (rec.get("median_ratio") or 0) > RB["blank_median_kdl"]:
            d.add("BLK_MATERIAL", el, "CONTAMINATION", s,
                  T.f_BLK_MATERIAL(el, bt, rec["median_ratio"], RB["blank_median_kdl"]),
                  "GEOLOGY", "BEFORE_ESTIMATE", figs, subject=bt)
    cb, pb = blank.get((T_CBLANK, el)), blank.get((T_PBLANK, el))
    if cb and pb and sevs.get(T_CBLANK) and not sevs.get(T_PBLANK):
        d.add("BLK_PREP", el, "PREPARATION", sevs[T_CBLANK],
              T.f_BLK_PREP(el, cb["fail_pct"], pb["fail_pct"]),
              "LAB", "IMMEDIATE", [f"blank/{T_CBLANK}/{el}", f"blank/{T_PBLANK}/{el}"])



# ---- precision ---------------------------------------------------------------
def _dups(d, el, R, C, S, RB, sev):
    dup = R.get("dup", {})
    for dt in DUP_TYPES:
        rec = dup.get((dt, el))
        if not rec:
            continue
        crit = _DUP_CRIT[dt]
        figs = [f"dup/{dt}/{el}"]
        s = sev(rec["ratings"].get(crit))
        if s:
            good = C[crit]["cuts"][2]
            hards = [r["hard"] for r in rec["rows"] if r["hard"] is not None]
            within = 100.0 * sum(1 for h in hards if h <= good) / len(hards) if hards else 0
            d.add("DUP_PRECISION", el, _DUP_STAGE[dt], s,
                  T.f_DUP_PRECISION(el, dt, rec["hard_p90"], good, rec["n"], within,
                                    rec["maxmin"]["fail_pct"]),
                  _DUP_OWNER[dt], "ONGOING", figs, subject=dt)
        sp = rec.get("split") or {}
        if sp.get("sig") and rec["n"] >= S["min_pairs"]:
            d.add("DUP_SPLIT", el, _DUP_STAGE[dt],
                  sev(rec["ratings"].get("dup_bias")) or "MINOR",
                  T.f_DUP_SPLIT(el, dt, rec["rd_mean"], sp["t"]["p"]),
                  _DUP_OWNER[dt], "ONGOING", figs, subject=dt)

    b = R.get("budget", {}).get(el)
    if b and b.get("dominant") and (b["pct"].get(b["dominant"]) or 0) >= RB["budget_dominant"]:
        top = next((dup.get((dt, el)) for dt in DUP_TYPES if dup.get((dt, el))), None)
        crit = _DUP_CRIT[top["type"]] if top else None
        s = sev(top["ratings"].get(crit)) if top else None
        if s:
            shares = [(k, v) for k, v in b["pct"].items() if v is not None]
            d.add("BUDGET_DOMINANT", el, _BUDGET_STAGE.get(b["dominant"], "SAMPLING"), s,
                  T.f_BUDGET_DOMINANT(el, b["dominant"], b["pct"][b["dominant"]],
                                      b["total_cv_pct"], shares),
                  "GEOLOGY", "ONGOING", [f"budget/{el}"])

    th = R.get("th", {}).get((T_PDUP, el))
    if th:
        s = sev(th["ratings"].get("th_precision"))
        if s:
            d.add("TH_PRECISION", el, "PRECISION", s,
                  T.f_TH_PRECISION(el, th["c_ref"], th["precision_at_ref"], th.get("pdl")),
                  "LAB", "ONGOING", [f"th/{T_PDUP}/{el}"])


# ---- inter-laboratory --------------------------------------------------------
def _umpire(d, el, R, C, S, RB, sev):
    u = R.get("umpire", {}).get(el)
    if not u:
        return
    s_w = sev(u["ratings"].get("ump_wbias"))
    figs = [f"umpire/{el}"]
    if s_w:
        biases = [r["bias"] for (lab, e), r in R.get("crm", {}).items()
                  if e == el and r.get("bias") is not None]
        pb = mean(biases)
        verdict = "unclear"
        if pb is not None and u["wbias"] is not None:
            if abs(pb) >= RB["sys_bias"] and pb * u["wbias"] < 0:
                verdict = "primary"
            elif abs(pb) < RB["sys_bias"]:
                verdict = "umpire"
        tt = u.get("ttest") or {}
        d.add("UMP_BIAS", el, "INTERLAB", s_w,
              T.f_UMP_BIAS(el, u["wbias"], u["pbias"], u["n"], tt.get("p"),
                           u.get("lab", ""), pb, verdict),
              "QP", "BEFORE_ESTIMATE", figs)
    s_q = sev(u["ratings"].get("ump_grade_range"))
    if s_q and (not s_w or SEVERITIES.index(s_q) < SEVERITIES.index(s_w)):
        q = max((x for x in u["quartiles"] if x["bias"] is not None),
                key=lambda x: abs(x["bias"]))
        d.add("UMP_GRADE", el, "INTERLAB", s_q,
              T.f_UMP_GRADE(el, q["q"], q["bias"], u["wbias"], q["lo"], q["hi"]),
              "LAB", "BEFORE_ESTIMATE", figs)


# ---- project-wide --------------------------------------------------------------
def _programme(d, project, R, C, S, RB, sev):
    for r in R.get("insertion", {}).get("rows", []):
        if r.get("info_only"):
            continue
        s = sev(r["rating"])
        if not s:
            continue
        if r["n"] == 0:
            d.add("INS_MISSING", "", "PROGRAMME", s, T.f_INS_MISSING(r["type"]),
                  "GEOLOGY", "ONGOING", ["insertion"], subject=r["type"])
        else:
            d.add("INS_RATE", "", "PROGRAMME", s,
                  T.f_INS_RATE(r["type"], r["n"], r["pct"], r["every"]),
                  "GEOLOGY", "ONGOING", ["insertion"], subject=r["type"])
    if not R.get("umpire"):
        d.add("INS_MISSING", "", "PROGRAMME", "MINOR",
              T.f_INS_MISSING("CHECK / UMPIRE"), "GEOLOGY", "ONGOING", [],
              subject="CHECK / UMPIRE")


def _data(d, project, R, C, S, RB, sev):
    L = project.clean_log
    if L is None:
        return
    cnt = L.counts()
    n_ctrl = sum(1 for s in project.samples if not s.dropped
                 and (s.stype == T_CRM or s.stype in BLANK_TYPES))
    n_pairs = sum(len(v) for v in (R.get("pairs") or {}).values()) + len(
        project.excluded_pairs)
    swaps = [a for a in L.actions if a.rule in ("C13", "C14", "C15")
             or (a.rule == "C16" and a.action == "excluded")]
    if swaps:
        p = 100.0 * len(swaps) / max(1, n_ctrl + n_pairs)
        n16 = sum(1 for a in swaps if a.rule == "C16")
        d.add("DATA_SWAP", "", "DATA", sev(rate(p, C["crm_fail"])) or "MINOR",
              T.f_DATA_SWAP(cnt.get("C13", 0), cnt.get("C14", 0), cnt.get("C15", 0),
                            n16, [a.sample for a in swaps]),
              "DATABASE", "BEFORE_ESTIMATE")
    n11 = cnt.get("C11", 0)
    n12 = cnt.get("C12", 0)
    if n11 or n12:
        els = sorted({a.element for a in L.actions if a.rule == "C11"})
        d.add("DATA_UNIT", "", "DATA", "MATERIAL" if n11 else "MINOR",
              T.f_DATA_UNIT(n11, n12, els), "DATABASE", "BEFORE_ESTIMATE")
    if cnt.get("C03"):
        d.add("DATA_DUPID", "", "DATA", "MINOR",
              T.f_DATA_DUPID(cnt["C03"], [a.sample for a in L.actions if a.rule == "C03"]),
              "DATABASE", "BEFORE_ESTIMATE")
    if cnt.get("C17"):
        d.add("DATA_ORPHAN", "", "DATA", "MINOR",
              T.f_DATA_ORPHAN(cnt["C17"], [a.sample for a in L.actions if a.rule == "C17"]),
              "DATABASE", "BEFORE_ESTIMATE")
    codes = [cnt.get(k, 0) for k in ("C04", "C05", "C06", "C07")]
    if any(codes):
        d.add("DATA_CODES", "", "DATA", "MINOR", T.f_DATA_CODES(*codes),
              "DATABASE", "BEFORE_ESTIMATE")
