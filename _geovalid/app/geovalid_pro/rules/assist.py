"""Optional anomaly assist (v2 brief F12, category E): off by default, explainable, suggestion-only, INFO only.

  IMP-021  code-mapping suggestions: raw logged codes that are not in the project's code dictionary, with the closest
           dictionary code by three explainable measures (character similarity, token-set similarity, initials)
  ASY-031  multivariate anomaly score: robust Mahalanobis distance of each sample's composition (centred log-ratio,
           isometric coordinates, MCD covariance), with the elements that contribute most to its distance

Enable with the profile's `anomaly_assist: {enabled: true}`. Nothing is changed; every result is a suggestion.
"""
from __future__ import annotations

import difflib
import re

import numpy as np
import pandas as pd

from .base import rule

FIELDS = ("lith_code", "alt_type", "weathering", "drill_method", "sample_type")


def _tokens(s: str) -> set[str]:
    return {t for t in re.split(r"[^0-9a-zA-Z؀-ۿ]+", str(s).lower()) if t}


def code_suggestions(raw: str, dictionary: list[str], n: int = 3) -> list[tuple[str, float, str]]:
    """Ranked (code, score, reason): the best of character similarity (difflib ratio on case-folded text),
    token-set similarity (shared words / words of the shorter) and initials (first letters of the raw words = code)."""
    r = str(raw).strip()
    rl = r.lower()
    rt = _tokens(r)
    initials = "".join(t[0] for t in re.split(r"[^0-9a-zA-Z]+", r) if t).lower()
    out = []
    for c in dictionary:
        cl = str(c).strip().lower()
        ch = difflib.SequenceMatcher(None, rl, cl).ratio()
        ct = _tokens(c)
        tok = len(rt & ct) / min(len(rt), len(ct)) if rt and ct else 0.0
        ini = 1.0 if initials and len(initials) >= 2 and initials == cl else 0.0
        pre = 0.9 if len(cl) >= 2 and (rl.startswith(cl) or cl.startswith(rl)) and min(len(rl), len(cl)) >= 2 else 0.0
        best = max((ch, "characters"), (tok, "shared words"), (ini, "initials"), (pre, "prefix"))
        out.append((str(c), round(best[0], 3), best[1]))
    out.sort(key=lambda t: -t[1])
    return out[:n]


@rule("IMP-021", ("anomaly_assist", "code_dictionary"))
def imp_020(ctx):
    """Raw codes absent from the code dictionary of their field, with up to three suggested dictionary codes scoring at
    least `min_score`. INFO only; the mapping is the user's decision (INT-015 reports the code itself)."""
    p = {**{"min_score": 0.6}, **(ctx.params.get("anomaly_assist") or {})}
    dicts = {k: [str(x) for x in v] for k, v in (ctx.params.get("code_dictionaries") or {}).items() if v}
    seen = set()
    for t in ctx.tables:
        for f, dic in dicts.items():
            if f not in t.df:
                continue
            vals = t.df[f].dropna().astype(str).str.strip()
            known = {d.upper() for d in dic}
            for code, n in vals[~vals.str.upper().isin(known)].value_counts().items():
                if (f, code) in seen or not code:
                    continue
                seen.add((f, code))
                sug = [s for s in code_suggestions(code, dic) if s[1] >= float(p["min_score"])]
                if not sug:
                    continue
                txt = "; ".join(f"{c} ({s:.2f}, {why})" for c, s, why in sug)
                ctx.add("IMP-021", "INFO", t.name, f"Code '{code}' in {f} ({n} rows) is not in the dictionary; closest dictionary codes: {txt}.",
                        f"کد «{code}» در {f} ({n} ردیف) در فرهنگ‌نامه نیست؛ نزدیک‌ترین کدها: {txt}.", field=f, value=code,
                        expected=sug[0][0], suggested_fix=f"If '{code}' means {sug[0][0]}, add it as a synonym in the code dictionary.")


def _ilr_basis(D: int) -> np.ndarray:
    """Orthonormal basis (D × D−1) of the clr hyperplane (Helmert)."""
    V = np.zeros((D, D - 1))
    for j in range(1, D):
        V[:j, j - 1] = 1.0 / j
        V[j, j - 1] = -1.0
        V[:, j - 1] *= np.sqrt(j / (j + 1.0))
    return V


def mcd(X: np.ndarray, h_frac: float = 0.75, n_start: int = 20, seed: int = 0) -> tuple[np.ndarray, np.ndarray]:
    """Minimum covariance determinant (FastMCD C-steps from random starts) with one reweighting step at χ²(0.975)."""
    from scipy.stats import chi2
    n, p = X.shape
    h = max(int(h_frac * n), p + 1)
    rng = np.random.default_rng(seed)
    best = (np.inf, None, None)
    for _ in range(n_start):
        idx = rng.choice(n, size=p + 1, replace=False)
        mu, S = X[idx].mean(axis=0), np.cov(X[idx].T) + 1e-9 * np.eye(p)
        for _ in range(20):
            Si = np.linalg.pinv(S)
            d = np.einsum("ij,jk,ik->i", X - mu, Si, X - mu)
            sel = np.argsort(d)[:h]
            mu_new, S_new = X[sel].mean(axis=0), np.cov(X[sel].T) + 1e-12 * np.eye(p)
            if np.allclose(mu_new, mu) and np.allclose(S_new, S):
                break
            mu, S = mu_new, S_new
        det = np.linalg.det(S)
        if det < best[0]:
            best = (det, mu, S)
    _, mu, S = best
    d = np.einsum("ij,jk,ik->i", X - mu, np.linalg.pinv(S), X - mu)
    S = S * np.median(d) / chi2.ppf(0.5, p)                      # consistency correction
    d = np.einsum("ij,jk,ik->i", X - mu, np.linalg.pinv(S), X - mu)
    keep = d <= chi2.ppf(0.975, p)
    if keep.sum() > p + 1:
        mu, S = X[keep].mean(axis=0), np.cov(X[keep].T)
    return mu, S


@rule("ASY-031", ("anomaly_assist", "assay"))
def asy_031(ctx):
    """Robust Mahalanobis distance of each routine sample's composition. Analytes with ≥ `min_valid_frac` measured
    values are used (≥ `min_elements`); below-detection values at ½ DL. Centred log-ratio, isometric coordinates, MCD
    covariance; samples with D² above χ²(`chi2_q`) are listed (at most `max_listed`, largest first) with the elements
    whose robust clr z-scores contribute most. INFO only: an anomaly can be mineralisation, contamination or a swap."""
    from scipy.stats import chi2
    from ..rules.interval import QC_TYPES
    p = {**{"min_elements": 4, "min_valid_frac": 0.7, "chi2_q": 0.999, "max_listed": 100, "top_elements": 3},
         **(ctx.params.get("anomaly_assist") or {})}
    for t in ctx.by_kind("assay"):
        df = t.df
        ok = ~df["qc_class"].isin(QC_TYPES) if "qc_class" in df else pd.Series(True, index=df.index)
        cols = {}
        for a in t.analytes:
            if a.partial or a.analyte in cols:
                continue
            v = a.parsed["value_policy"].astype(float)
            from ..analysis.assay import TO_PPM
            f = TO_PPM.get(a.unit, 1.0) if a.unit else 1.0               # one scale for all parts (ppm)
            if (v[ok] > 0).mean() >= float(p["min_valid_frac"]):
                cols[a.analyte] = v * f
        if len(cols) < int(p["min_elements"]):
            continue
        X = pd.DataFrame(cols)[ok]
        X = X[(X > 0).all(axis=1)]
        if len(X) < 10 * len(cols):
            continue
        L = np.log(X.to_numpy(float))
        clr = L - L.mean(axis=1, keepdims=True)
        V = _ilr_basis(clr.shape[1])
        Z = clr @ V
        mu, S = mcd(Z, seed=int(p.get("seed", 0)))
        d2 = np.einsum("ij,jk,ik->i", Z - mu, np.linalg.pinv(S), Z - mu)
        lim = chi2.ppf(float(p["chi2_q"]), Z.shape[1])
        med = np.median(clr, axis=0)
        mad = 1.4826 * np.median(np.abs(clr - med), axis=0)
        zc = (clr - med) / np.where(mad > 0, mad, 1)
        names = list(cols)
        flag = np.where(d2 > lim)[0]
        ctx.stats.setdefault("anomaly", {})[t.name] = pd.DataFrame({"idx": X.index, "d2": d2})
        order = flag[np.argsort(-d2[flag])][: int(p["max_listed"])]
        for k in order:
            i = X.index[k]
            top = np.argsort(-np.abs(zc[k]))[: int(p["top_elements"])]
            why = ", ".join(f"{names[j]} {'high' if zc[k, j] > 0 else 'low'} (z {zc[k, j]:+.1f})" for j in top)
            r = df.loc[i]
            ctx.add("ASY-031", "INFO", t.name, f"Unusual composition (robust distance² {d2[k]:.0f} > {lim:.0f}): {why}. Mineralisation, contamination or a sample swap — check.",
                    f"ترکیب نامعمول (فاصلهٔ مقاوم² {d2[k]:.0f}): {why}.", hole_id=r.get("hole_id"), from_m=r.get("from_m"), to_m=r.get("to_m"),
                    field="composition", value=round(float(d2[k]), 1), src_row=int(r["src_row"]))
        if len(flag) > len(order):
            ctx.add("ASY-031", "INFO", t.name, f"{len(flag)} samples exceed the anomaly threshold; the {len(order)} largest are listed.",
                    f"{len(flag)} نمونه از آستانهٔ ناهنجاری فراتر رفته‌اند؛ {len(order)} مورد بزرگ‌تر فهرست شده است.", field="composition", value=len(flag))
