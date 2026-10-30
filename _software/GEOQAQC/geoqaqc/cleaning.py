# -*- coding: utf-8 -*-
"""Automatic validation and cleaning of raw assay data.

Policy (spec 4): a DATA ERROR is excluded or corrected; a QC FAILURE is never
removed. A CRM that is merely beyond 3 SD, a blank that is merely dirty and a
pair that is merely scattered stay in the statistics -- they are the findings.
Nothing in the input tables is modified: "excluded" always means "left out of
the calculations", and every action is written to the cleaning log with the
rule, the sample, the original text and the reason.

Every rule can be switched off (RuleBook 'clean_Cxx') and every threshold is a
RuleBook entry. With every switch off the values are exactly those of 1.1.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

from .core import (BLANK_TYPES, T_CRM, canonical_unit, dl_flag, element_symbol,
                   element_unit, fnum, to_latin_digits, unit_factor)
from .model import detection_limit, usable

# ---------------------------------------------------------------------------
RULE_TITLES = {
    "C01": ("Row without sample ID", "سطر بدون شمارهٔ نمونه"),
    "C02": ("Exact duplicate row", "سطر تکراری"),
    "C03": ("Duplicate sample ID (re-assay)", "شمارهٔ نمونهٔ تکراری (آنالیز مجدد)"),
    "C04": ("Laboratory text code", "کد متنی آزمایشگاه"),
    "C05": ("Sentinel value", "عدد نگهبان"),
    "C06": ("Negative value read as below DL", "عدد منفی به معنای زیر حد تشخیص"),
    "C07": ("Zero read as below DL", "صفر به معنای زیر حد تشخیص"),
    "C08": ("Over-range value", "مقدار بالای دامنهٔ روش"),
    "C09": ("CRM code matched loosely", "تطبیق کد شاهد"),
    "C10": ("Certificate element / unit matched", "تطبیق عنصر و واحد گواهی"),
    "C11": ("Unit mismatch of a whole column", "ناهمخوانی واحد کل ستون"),
    "C12": ("Decimal or unit slip in one CRM result", "خطای ممیز یا واحد در یک نتیجهٔ شاهد"),
    "C13": ("Swapped CRM", "جابه‌جایی شاهد"),
    "C14": ("Blank inserted as CRM", "خالی به‌جای شاهد"),
    "C15": ("CRM inserted as blank", "شاهد به‌جای خالی"),
    "C16": ("Mispaired duplicate", "جفت تکراری جابه‌جا"),
    "C17": ("Duplicate without parent", "تکراری بی‌والد"),
    "C18": ("Sequence problem", "اشکال ترتیب"),
}

_SEVERITY = {"C01": "warning", "C02": "warning", "C03": "warning",
             "C04": "info", "C05": "info", "C06": "info", "C07": "info",
             "C08": "warning", "C09": "info", "C10": "info", "C11": "error",
             "C12": "error", "C13": "error", "C14": "error", "C15": "error",
             "C16": "error", "C17": "warning", "C18": "warning"}


@dataclass
class CleanAction:
    rule: str
    sample: str
    element: str
    original: str
    action: str          # dropped | excluded | corrected | converted | flagged
    reason: str
    severity: str        # info | warning | error


class CleanLog:
    def __init__(self):
        self.actions = []

    def add(self, rule, sample, element, original, action, reason,
            severity=None):
        self.actions.append(CleanAction(rule, str(sample), element or "",
                                        "" if original is None else str(original),
                                        action, reason,
                                        severity or _SEVERITY.get(rule, "info")))

    def rows(self):
        return [{"Rule": a.rule, "Sample": a.sample, "Element": a.element,
                 "Original": a.original, "Action": a.action, "Reason": a.reason,
                 "Severity": a.severity} for a in self.actions]

    def counts(self):
        out = {}
        for a in self.actions:
            out[a.rule] = out.get(a.rule, 0) + 1
        return dict(sorted(out.items()))

    def excluded_samples(self):
        return {a.sample for a in self.actions
                if a.action in ("dropped", "excluded")}

    def for_element(self, el):
        return [a for a in self.actions if a.element == el]

    def to_state(self):
        return [asdict(a) for a in self.actions]


def _on(RB, code):
    return bool(RB[f"clean_{code}"])


def norm_code(s):
    """CRM code for matching: upper case, without spaces, - _ . /"""
    s = str(s or "").upper()
    for ch in " -_./\t":
        s = s.replace(ch, "")
    return s


# ===========================================================================
#  Value parsing (C04-C07)
# ===========================================================================
def parse_value(raw, RB, decimal_comma=False):
    """One cell -> (value, flag, rule_code or None). With C04-C07 switched off
    the result is the 1.1 parse: fnum() and dl_flag()."""
    if raw is None:
        return None, "", None
    s = to_latin_digits(raw).strip()
    if not s:
        return None, "", None
    codes = {str(c).strip().upper() for c in RB["lab_codes"]}
    if _on(RB, "C04") and s.upper() in codes:
        return None, "", "C04"
    v = fnum(s, decimal_comma=decimal_comma)
    flag = dl_flag(s)
    if v is None:
        # text that is neither a number nor a known code is still "no result",
        # but it is reported, so an unknown code can be added to the list
        return None, "", ("C04" if _on(RB, "C04") else None)
    if flag == "":
        if _on(RB, "C05") and any(abs(v - x) < 1e-9 for x in RB["sentinels"]):
            return None, "", "C05"
        if _on(RB, "C06") and v < 0:
            return -v, "<", "C06"
        if _on(RB, "C07") and v == 0:
            return 0.0, "<", "C07"
    return v, flag, None


_PARSE_REASON = {
    "C04": "laboratory code or text, not a result -> missing",
    "C05": "sentinel number, not a concentration -> missing",
    "C06": "negative value -> below detection limit",
    "C07": "zero -> below detection limit",
}


# ===========================================================================
#  Driver
# ===========================================================================
def clean_values(project, S, RB, log=print):
    """Apply C01-C15 and C18 to project.samples and rebuild project.certs.
    Returns the CleanLog (also stored on project.clean_log)."""
    L = CleanLog()
    project.clean_log = L
    samples = project.samples
    t = project.assay
    elements = list(project.elements)

    # ---- C01 rows without an ID ----
    if _on(RB, "C01"):
        for n, why in project.dropped_rows:
            L.add("C01", f"row {n}", "", "", "dropped", why)

    # ---- C02 exact duplicate rows ----
    if _on(RB, "C02") and t is not None:
        seen = {}
        for s in samples:
            key = tuple(t.rows[s.row_n - 2]) if 0 <= s.row_n - 2 < len(t.rows) else None
            if key is None:
                continue
            if key in seen:
                s.dropped = True
                L.add("C02", s.sid, "", f"file row {s.row_n}", "dropped",
                      f"identical to file row {seen[key]}")
            else:
                seen[key] = s.row_n

    # ---- C03 duplicate IDs ----
    if _on(RB, "C03"):
        groups = {}
        for s in samples:
            if not s.dropped:
                groups.setdefault(s.sid.strip().upper(), []).append(s)
        policy = RB["dup_id_policy"]
        for sid, lst in groups.items():
            if len(lst) < 2:
                continue
            if policy == "keep first":
                gone = lst[1:]
            elif policy == "keep last":
                gone = lst[:-1]
            else:
                gone = lst
            for s in gone:
                s.dropped = True
                L.add("C03", s.sid, "", f"file row {s.row_n}", "dropped",
                      f"sample ID appears {len(lst)} times; policy '{policy}'")

    # ---- C04-C07 re-parse every value ----
    dc = getattr(t, "decimal_comma", False) if t is not None else False
    for s in samples:
        if s.dropped:
            continue
        for el in elements:
            raw = s.raw.get(el)
            v, flag, rule = parse_value(raw, RB, decimal_comma=dc)
            s.vals[el], s.flags[el] = v, flag
            if rule:
                L.add(rule, s.sid, el, raw, "converted" if v is not None
                      else "excluded", _PARSE_REASON[rule])

    # ---- C08 over-range ----
    if _on(RB, "C08"):
        for s in samples:
            if s.dropped:
                continue
            for el in elements:
                if s.flags.get(el) == ">" and s.vals.get(el) is not None:
                    s.excl[el] = "C08 over-range value (censored)"
                    L.add("C08", s.sid, el, s.raw.get(el), "excluded",
                          "over the upper limit of the method; the true value "
                          "is unknown")

    # ---- C09 / C10 certificates ----
    _build_certs(project, RB, L)

    # ---- C11 / C12 units ----
    if _on(RB, "C11"):
        _column_units(project, S, RB, L)
    if _on(RB, "C12"):
        _single_slips(project, S, RB, L)

    # ---- C13 / C14 / C15 swaps ----
    if _on(RB, "C13"):
        _crm_swaps(project, S, RB, L)
    if _on(RB, "C14"):
        _crm_is_blank(project, S, RB, L)
    if _on(RB, "C15"):
        _blank_is_crm(project, S, RB, L)

    # ---- C18 sequence ----
    if _on(RB, "C18"):
        _sequence(project, L)

    n = len(L.actions)
    log(f"Cleaning: {n} action(s)" + (": " + ", ".join(
        f"{k} {v}" for k, v in L.counts().items()) if n else ""))
    return L


# ===========================================================================
#  Certificates (C09, C10)
# ===========================================================================
def _match_cert_element(cert_el, elements, fuzzy):
    """Assay column for a certificate element name, or None."""
    ce = str(cert_el).strip()
    for e in elements:
        if e.strip().upper() == ce.upper():
            return e
    if not fuzzy:
        return None
    sym = element_symbol(ce)
    cands = [e for e in elements if element_symbol(e) == sym]
    if not cands:
        return None
    cu = element_unit(ce)
    same = [e for e in cands if cu and element_unit(e) == cu]
    return (same or cands)[0]


def _build_certs(project, RB, L):
    ct = project.crm
    fuzzy_code, fuzzy_el = _on(RB, "C09"), _on(RB, "C10")
    for s in project.samples:
        s.crm_key = norm_code(s.crmid) if fuzzy_code else s.crmid.strip().upper()
    certs, labels = {}, {}
    if ct is not None:
        cdc = getattr(ct, "decimal_comma", False)
        for r in ct.rows:
            label = str(ct.get(r, "crmid") or "").strip()
            el = str(ct.get(r, "element") or "").strip()
            cv = fnum(ct.get(r, "certified"), decimal_comma=cdc)
            sd = fnum(ct.get(r, "sd"), decimal_comma=cdc)
            unit = str(ct.get(r, "unit") or "").strip()
            if not label or not el or cv is None:
                continue
            key = norm_code(label) if fuzzy_code else label.upper()
            labels.setdefault(key, label)
            col = _match_cert_element(el, project.elements, fuzzy_el)
            if col is None:
                continue
            factor = 1.0
            if fuzzy_el:
                cu = canonical_unit(unit) or element_unit(el)
                au = element_unit(col)
                f = unit_factor(cu, au) if cu and au else None
                if f is not None and f != 1:
                    factor = float(f)
                    L.add("C10", label, col, f"{cv:g} {cu}", "converted",
                          f"certificate in {cu}, assay column in {au}: "
                          f"x {factor:g}")
                elif col.strip().upper() != el.upper():
                    L.add("C10", label, col, el, "corrected",
                          f"certificate element '{el}' matched to column '{col}'")
            certs[(key, col)] = {
                "cert": cv * factor, "sd": sd * factor if sd is not None else None,
                "unit": unit, "method": str(ct.get(r, "method") or "").strip(),
                "label": label, "factor": factor}
    # labels for codes that only occur in the assay table
    for s in project.samples:
        if s.stype == T_CRM and s.crm_key:
            labels.setdefault(s.crm_key, s.crmid.strip().upper())
    if fuzzy_code:
        seen = set()
        for s in project.samples:
            if s.stype != T_CRM or not s.crm_key or s.crm_key not in labels:
                continue
            lab = labels[s.crm_key]
            pair = (s.crmid.strip(), lab)
            if s.crmid.strip().upper() != lab.upper() and pair not in seen:
                seen.add(pair)
                L.add("C09", s.crmid.strip(), "", s.crmid, "corrected",
                      f"CRM code '{s.crmid.strip()}' matched to certificate "
                      f"'{lab}'")
    project.certs = certs
    project.crm_labels = labels


# ===========================================================================
#  Helpers for z-scores against a certificate
# ===========================================================================
def _crm_results(project, key, el):
    return [s for s in project.samples
            if s.stype == T_CRM and s.crm_key == key and usable(s, el)]


def _robust_sd(vals):
    if len(vals) < 3:
        return None
    srt = sorted(vals)
    med = srt[len(srt) // 2]
    mad = sorted(abs(v - med) for v in vals)[len(vals) // 2]
    return 1.4826 * mad or None


def _eff_sd(project, key, el):
    c = project.certs.get((key, el))
    if not c:
        return None
    if c["sd"]:
        return c["sd"]
    vals = [s.vals[el] for s in _crm_results(project, key, el)
            if c["cert"] and 0.5 <= s.vals[el] / c["cert"] <= 2.0]
    return _robust_sd(vals)


def _z(project, key, el, v):
    c = project.certs.get((key, el))
    sd = _eff_sd(project, key, el)
    if not c or not sd:
        return None
    return (v - c["cert"]) / sd


def _crm_keys(project):
    return sorted({k for k, _ in project.certs})


# ===========================================================================
#  Units (C11, C12)
# ===========================================================================
def _column_units(project, S, RB, L):
    tol = RB["unit_col_tol"] / 100.0
    for el in project.elements:
        ratios = []
        for (key, e), c in project.certs.items():
            if e != el or not c["cert"]:
                continue
            ratios += [s.vals[el] / c["cert"] for s in _crm_results(project, key, el)
                       if s.vals[el] > 0]
        if len(ratios) < 3:
            continue
        med = sorted(ratios)[len(ratios) // 2]
        for k in (3, 4, -3, -4):
            target = 10.0 ** k
            if abs(med / target - 1.0) <= tol:
                for (key, e), c in project.certs.items():
                    if e == el:
                        c["cert"] *= target
                        if c["sd"] is not None:
                            c["sd"] *= target
                        c["factor"] *= target
                L.add("C11", "(all CRMs)", el, f"median ratio {med:.4g}",
                      "converted", f"every CRM reads about {target:g} x its "
                      f"certificate: the certificate and the assay column use "
                      f"different units; certificates rescaled x {target:g}")
                break


def _single_slips(project, S, RB, L):
    tol = RB["unit_single_tol"] / 100.0
    for (key, el), c in project.certs.items():
        if not c["cert"]:
            continue
        for s in _crm_results(project, key, el):
            r = s.vals[el] / c["cert"]
            z = _z(project, key, el, s.vals[el])
            if z is not None and abs(z) <= S["k_fail"]:
                continue
            for k in (1, 2, 3, -1, -2, -3):
                if r > 0 and abs(r / 10.0 ** k - 1.0) <= tol:
                    s.excl[el] = f"C12 reads {r:.4g} x certificate (decimal/unit slip)"
                    L.add("C12", s.sid, el, s.raw.get(el), "excluded",
                          f"{r:.4g} x the certificate of {c['label']} while the "
                          f"other results agree: transcription slip, not an "
                          f"analytical failure")
                    break


# ===========================================================================
#  Swaps (C13, C14, C15)
# ===========================================================================
def _match_other(project, s, own_key, RB, S, require_own_fail=True):
    """Best other CRM a result agrees with, or None.
    Returns (key, n_elements, n_agree, mean |z_alt|)."""
    best = None
    for k2 in _crm_keys(project):
        if k2 == own_key:
            continue
        els = [el for el in project.elements
               if usable(s, el) and (k2, el) in project.certs
               and (own_key is None or (own_key, el) in project.certs)]
        if not els:
            continue
        z_alt = [_z(project, k2, el, s.vals[el]) for el in els]
        z_own = ([_z(project, own_key, el, s.vals[el]) for el in els]
                 if own_key is not None else [None] * len(els))
        if any(z is None for z in z_alt):
            continue
        agree = sum(1 for z in z_alt if abs(z) <= RB["swap_alt_z"])
        n = len(els)
        if require_own_fail:
            if any(z is None for z in z_own):
                continue
            fail = sum(1 for z in z_own if abs(z) > S["k_fail"])
            if n >= 2:
                ok = fail / n >= RB["swap_frac"] and agree / n >= RB["swap_frac"]
            else:
                ok = abs(z_own[0]) > RB["swap_single_z"] and agree == 1
        else:
            ok = (agree / n >= RB["swap_frac"]) if n >= 2 else agree == 1
        if not ok:
            continue
        score = (agree, -sum(abs(z) for z in z_alt) / n)
        if best is None or score > best[0]:
            best = (score, (k2, n, agree, -score[1]))
    return best[1] if best else None


def _crm_swaps(project, S, RB, L):
    for s in project.samples:
        if s.stype != T_CRM or s.dropped or s.excl_all or not s.crm_key:
            continue
        m = _match_other(project, s, s.crm_key, RB, S)
        if not m:
            continue
        k2, n, agree, zbar = m
        own = project.crm_labels.get(s.crm_key, s.crm_key)
        other = project.crm_labels.get(k2, k2)
        s.excl_all = f"C13 probably {other}, labelled {own}"
        s.swap_to = k2
        basis = (f"{agree} of {n} certified elements" if n >= 2
                 else "single-element evidence")
        L.add("C13", s.sid, "", own, "excluded",
              f"fails {own} but agrees with {other} ({basis}, mean |z| "
              f"{zbar:.2f}): labelling error, not a laboratory failure")


def _crm_is_blank(project, S, RB, L):
    kdl = RB["crm_blank_kdl"]
    dls = {el: detection_limit(project, el, S) for el in project.elements}
    for s in project.samples:
        if s.stype != T_CRM or s.dropped or s.excl_all or not s.crm_key:
            continue
        els = [el for el in project.elements
               if usable(s, el) and (s.crm_key, el) in project.certs and dls[el]]
        if not els:
            continue
        low = all(s.vals[el] <= kdl * dls[el] for el in els)
        # the material itself must not be blank-level, or a low reading of a
        # genuinely low-grade CRM would be called a swap
        cert_high = all(project.certs[(s.crm_key, el)]["cert"] > kdl * dls[el]
                        for el in els)
        if low and cert_high:
            own = project.crm_labels.get(s.crm_key, s.crm_key)
            s.excl_all = f"C14 blank-level result labelled {own}"
            L.add("C14", s.sid, "", own, "excluded",
                  f"every certified element is below {kdl:g} x DL: a blank or "
                  f"an empty slot was inserted instead of {own}")


def _blank_is_crm(project, S, RB, L):
    dls = {el: detection_limit(project, el, S) for el in project.elements}
    for s in project.samples:
        if s.stype not in BLANK_TYPES or s.dropped or s.excl_all:
            continue
        # a candidate swap must at least fail as a blank in the voting elements
        m = _match_other(project, s, None, RB, S, require_own_fail=False)
        if not m:
            continue
        k2, n, agree, zbar = m
        els = [el for el in project.elements
               if usable(s, el) and (k2, el) in project.certs]
        if not all(dls[el] and s.vals[el] > S["k_dl"] * dls[el] for el in els):
            continue
        other = project.crm_labels.get(k2, k2)
        s.excl_all = f"C15 probably {other}, labelled blank"
        s.swap_to = k2
        basis = (f"{agree} of {n} certified elements" if n >= 2
                 else "single-element evidence")
        L.add("C15", s.sid, "", s.stype, "excluded",
              f"matches the certificate of {other} ({basis}, mean |z| "
              f"{zbar:.2f}): a CRM was inserted as a blank, not contamination")


# ===========================================================================
#  Sequence (C18)
# ===========================================================================
def _sequence(project, L):
    t = project.assay
    if t is None or not t.mapping.get("order"):
        L.add("C18", "(all)", "", "", "flagged",
              "no sequence column mapped: the file order is used as the "
              "analytical sequence")
        return
    live = [s for s in project.samples if not s.dropped]
    missing = [s for s in live if s.order is None]
    if missing:
        L.add("C18", ", ".join(s.sid for s in missing[:10])
              + (" ..." if len(missing) > 10 else ""), "", "", "flagged",
              f"{len(missing)} sample(s) without a sequence number; they sort "
              f"first in the control charts")
    seen = {}
    for s in live:
        if s.order is not None:
            seen.setdefault(s.order, []).append(s.sid)
    rep = {k: v for k, v in seen.items() if len(v) > 1}
    if rep:
        ex = "; ".join(f"{k:g}: {', '.join(v[:3])}" for k, v in list(rep.items())[:5])
        L.add("C18", "(several)", "", "", "flagged",
              f"{len(rep)} sequence number(s) used more than once ({ex}); "
              f"file order breaks the tie")


# ===========================================================================
#  Pairs (C16, C17) -- run after the duplicates are paired
# ===========================================================================
def _hard(a, b):
    return abs(a - b) / (a + b) * 100.0 if a + b > 0 else None


def clean_pairs(project, pairs, S, RB, log=print):
    """C17: list duplicates that could not be paired. C16: a pair that
    disagrees grossly in most elements comes from two different samples and
    is excluded (project.excluded_pairs); with too few voting elements it is
    only flagged, because one element cannot tell a mispair from a nugget."""
    L = project.clean_log or CleanLog()
    project.clean_log = L
    if _on(RB, "C17"):
        for sid, dtype, why in project.orphan_dups:
            L.add("C17", sid, "", dtype, "flagged",
                  f"{why}; this duplicate is not in the precision statistics")
    if not _on(RB, "C16"):
        return
    dls = {el: detection_limit(project, el, S) for el in project.elements}
    multi = len(project.elements) >= RB["mispair_min_el"]
    for dtype, plist in pairs.items():
        for so, sd_ in plist:
            voting, bad = [], []
            for el in project.elements:
                if not usable(so, el) or not usable(sd_, el) or not dls[el]:
                    continue
                a, b = so.vals[el], sd_.vals[el]
                if min(a, b) <= RB["mispair_kdl"] * dls[el]:
                    continue
                h = _hard(a, b)
                voting.append(el)
                if h is not None and h > RB["mispair_hard"]:
                    bad.append((el, h))
            if not bad:
                continue
            detail = ", ".join(f"{el} HARD {h:.0f}%" for el, h in bad)
            if (multi and len(voting) >= RB["mispair_min_el"]
                    and len(bad) / len(voting) >= RB["mispair_frac"]):
                project.excluded_pairs.add((so.sid, sd_.sid))
                L.add("C16", sd_.sid, "", f"{dtype} of {so.sid}", "excluded",
                      f"disagrees with its parent in {len(bad)} of "
                      f"{len(voting)} elements ({detail}): the two results "
                      f"come from different samples")
            elif len(voting) < RB["mispair_min_el"]:
                L.add("C16", sd_.sid, "", f"{dtype} of {so.sid}", "flagged",
                      f"{detail}; too few elements to tell a mispair from a "
                      f"nugget effect, so the pair is kept")
