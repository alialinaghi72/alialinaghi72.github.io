"""Version rules (v2 brief F6, category I), on the comparison computed by versions.compare():

  VER-001  holes added (INFO summary) or deleted (WARNING each)
  VER-002  collar coordinates or EOH changed (INFO); a common shift of most moved collars → WARNING (datum change)
  VER-003  survey changed; EOH position moves more than `pos_tol_m` → WARNING
  VER-004  intervals added, removed or re-segmented (INFO per table); assayed metres inside mineralised zones fewer
           than before → WARNING
  VER-005  values or codes changed (INFO per field); assay changes mostly upward (sign test) → WARNING; a one-to-one
           code substitution → INFO "renamed code"
  VER-009  (brief VER-01) any change to a hole locked in the last accepted snapshot → CRITICAL
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .base import rule


def _cmp(ctx):
    return ctx.stats["version"]


def _ch(ctx) -> pd.DataFrame:
    return _cmp(ctx)["changes"]


@rule("VER-001", ("baseline",))
def ver_001(ctx):
    c = _cmp(ctx)
    s = c["summary"]["holes"]
    if c["added"]:
        names = [c["names_new"][k] for k in c["added"]]
        ctx.add("VER-001", "INFO", "versions", f"{len(names)} holes added since the baseline: {', '.join(names[:20])}{' …' if len(names) > 20 else ''}.",
                f"{len(names)} گمانه نسبت به نسخهٔ پایه افزوده شده است.", field="hole_id", value=len(names))
    for k in c["removed"]:
        h = c["names_old"][k]
        ctx.add("VER-001", "WARNING", "versions", f"Hole {h} is in the baseline but not in the current version.",
                f"گمانهٔ {h} در نسخهٔ پایه هست ولی در نسخهٔ فعلی نیست.", hole_id=h, field="hole_id", value=h,
                suggested_fix="Confirm the deletion was intended and documented.")
    ctx.add("VER-001", "INFO", "versions", f"Version comparison: {s['current']} holes now, {s['baseline']} in the baseline; {s['unchanged']} unchanged (skipped by hash), {s['changed']} changed, {s['added']} added, {s['deleted']} deleted.",
            f"مقایسهٔ نسخه‌ها: {s['current']} گمانه در نسخهٔ فعلی و {s['baseline']} در نسخهٔ پایه؛ {s['unchanged']} بدون تغییر، {s['changed']} تغییرکرده.",
            field="holes", value=f"{s['changed']} changed")


@rule("VER-002", ("baseline",))
def ver_002(ctx):
    p = ctx.p("VER-002")
    ch = _ch(ctx)
    mv = ch[ch["change_class"] == "collar moved"]
    for r in mv.itertuples():
        ctx.add("VER-002", "INFO", "versions", f"Collar {r.field} changed: {r.old} → {r.new}" + (f" ({r.detail})" if isinstance(r.detail, str) else "") + ".",
                f"دهانهٔ {r.hole_id} تغییر کرده است ({r.field}): {r.old} → {r.new}.", hole_id=r.hole_id, field=r.field, value=r.delta)
    moves = _cmp(ctx)["collar_moves"]
    if len(moves) >= 3:
        d = np.array([m[1:] for m in moves], float)
        med = np.median(d, axis=0)
        mad = np.median(np.abs(d - med), axis=0) * 1.4826
        share = np.mean(np.all(np.abs(d - med) <= np.maximum(3 * mad, 0.05), axis=1))
        n_all = _cmp(ctx)["summary"]["holes"]["common"]
        if share >= float(p.get("shift_min_frac", 0.5)) and np.linalg.norm(med) > 0.05:
            ctx.add("VER-002", "WARNING", "versions", f"{len(moves)} collars moved, {100 * share:.0f} % of them by the same vector (dx {med[0]:+.2f}, dy {med[1]:+.2f}, dz {med[2]:+.2f} m; {len(moves)} of {n_all} common holes): a datum or projection change, not individual corrections.",
                    f"{len(moves)} دهانه با یک بردار مشترک جابه‌جا شده‌اند: احتمال تغییر مبنا یا سیستم تصویر.", field="x,y,z",
                    value=f"{med[0]:+.2f},{med[1]:+.2f},{med[2]:+.2f}", suggested_fix="Document the transformation applied to the collars.")


@rule("VER-003", ("baseline",))
def ver_003(ctx):
    tol = float(ctx.p("VER-003").get("pos_tol_m", 1.0))
    ch = _ch(ctx)
    for r in ch[ch["change_class"] == "survey changed"].itertuples():
        d = r.delta if r.delta is not None and not pd.isna(r.delta) else 0.0
        sev = "WARNING" if d > tol else "INFO"
        ctx.add("VER-003", sev, "versions", f"Survey changed ({r.detail}).", f"داده‌های انحراف‌سنجی تغییر کرده است ({r.detail}).",
                hole_id=r.hole_id, field="survey", value=round(float(d), 3))


@rule("VER-004", ("baseline",))
def ver_004(ctx):
    ch = _ch(ctx)
    geo = ch[ch["change_class"].isin(["interval added", "interval removed", "re-segmented"])]
    for t, g in geo.groupby("table"):
        n = g["change_class"].value_counts()
        holes = g["hole_id"].nunique()
        txt = ", ".join(f"{v} {k}" for k, v in n.items())
        ctx.add("VER-004", "INFO", t, f"{t}: {txt} in {holes} holes.", f"{t}: {txt} در {holes} گمانه.", field="intervals", value=int(len(g)))
    if any((ctx.params.get("mineralised_codes") or {}).values()):
        from .xtable import _codes, _zones
        z = _zones(ctx, _codes(ctx.params, "mineralised_codes"))
        if z.empty:
            return
        rem = ch[(ch["change_class"] == "interval removed") & (ch["table"].isin([t.name for t in ctx.by_kind("assay")]))]
        lost = 0.0
        for r in rem.itertuples():
            zz = z[z["hole_id"] == r.hole_id]
            ov = (np.minimum(zz["to_m"], r.to_m) - np.maximum(zz["from_m"], r.from_m)).clip(lower=0).sum()
            lost += float(ov)
        if lost > ctx.eps:
            ctx.add("VER-004", "WARNING", "versions", f"{lost:.1f} m of assayed intervals inside zones logged as mineralised were removed since the baseline.",
                    f"{lost:.1f} متر از بازه‌های آنالیزشده درون زون‌های کانه‌دار نسبت به نسخهٔ پایه حذف شده است.", field="assay", value=round(lost, 2))


@rule("VER-005", ("baseline",))
def ver_005(ctx):
    from scipy.stats import binomtest
    p = ctx.p("VER-005")
    ch = _ch(ctx)
    vals = ch[ch["change_class"].isin(["re-assayed", "code changed", "metadata changed"])]
    for (cls, t, f), g in vals.groupby(["change_class", "table", "field"]):
        if cls == "code changed":
            pairs = g[["old", "new"]].drop_duplicates()
            bij = pairs["old"].is_unique and pairs["new"].is_unique
            ctx.add("VER-005", "INFO", t, f"{t}.{f}: {len(g)} codes changed" + (f" (a one-to-one renaming: {', '.join(f'{a}→{b}' for a, b in pairs.head(6).itertuples(index=False))})" if bij else "") + ".",
                    f"{t}.{f}: {len(g)} کد تغییر کرده است.", field=f, value=int(len(g)))
            continue
        d = pd.to_numeric(g["delta"], errors="coerce").dropna()
        txt = f"{t}.{f}: {len(g)} values changed ({cls})"
        if len(d):
            txt += f", median change {d.median():+.4g}"
        ctx.add("VER-005", "INFO", t, txt + ".", f"{t}.{f}: {len(g)} مقدار تغییر کرده است.", field=f, value=int(len(g)))
        if cls == "re-assayed" and len(d[d != 0]) >= int(p.get("min_n", 20)):
            up = int((d > 0).sum())
            n = int((d != 0).sum())
            pv = binomtest(up, n, 0.5, alternative="greater").pvalue
            if up / n >= float(p.get("upward_share", 0.75)) and pv < 0.05:
                ctx.add("VER-005", "WARNING", t, f"{t}.{f}: {up} of {n} changed values went up (sign test p = {pv:.1e}): a systematic upgrade needs its source documents.",
                        f"{t}.{f}: {up} از {n} مقدار تغییرکرده افزایش یافته‌اند: افزایش سیستماتیک نیازمند سند منبع است.", field=f, value=f"{up}/{n}")


@rule("VER-009", ("snapshot",))
def ver_009(ctx):
    """Brief VER-01: per-hole hashes against the last accepted snapshot. A locked hole changed or deleted → CRITICAL;
    other differences → INFO summary; a different rule profile or program version → INFO."""
    m = ctx.stats["snapshot"]
    hh = ctx.stats.get("hole_hashes")
    cur = dict(zip(hh["hole_key"], hh["hash"])) if hh is not None else {}
    names = dict(zip(hh["hole_key"], hh["hole_id"])) if hh is not None else {}
    snap = m.get("hole_hashes", {})
    locked = set(m.get("locked_holes", []))
    tag = f"snapshot {m.get('_file', '')} accepted {m.get('accepted_at', '')} by {m.get('reviewer', '')}"
    other = 0
    for k, rec in snap.items():
        h = rec.get("hole_id", k)
        if k not in cur:
            if k in locked:
                ctx.add("VER-009", "CRITICAL", "versions", f"Locked hole {h} ({tag}) is missing from the current data.",
                        f"گمانهٔ قفل‌شدهٔ {h} در داده‌های فعلی وجود ندارد.", hole_id=h, field="hole", value="deleted", alias="VER-01",
                        suggested_fix="Restore the hole, or accept a new snapshot with the reason recorded.")
            continue
        if cur[k] != rec.get("hash"):
            if k in locked:
                ctx.add("VER-009", "CRITICAL", "versions", f"Locked hole {names.get(k, h)} changed since the accepted {tag}.",
                        f"گمانهٔ قفل‌شدهٔ {names.get(k, h)} پس از پذیرش تصویر داده تغییر کرده است.", hole_id=names.get(k, h), field="hash",
                        value=cur[k][:12], expected=rec.get("hash", "")[:12], alias="VER-01",
                        suggested_fix="Find the change (compare with the accepted version) and either revert it or accept a new snapshot with the reason.")
            else:
                other += 1
    new = [names[k] for k in cur if k not in snap]
    if other or new:
        ctx.add("VER-009", "INFO", "versions", f"Since the accepted {tag}: {other} unlocked holes changed, {len(new)} holes added.",
                f"پس از تصویر پذیرفته‌شده: {other} گمانهٔ قفل‌نشده تغییر کرده و {len(new)} گمانه افزوده شده است.", field="holes", value=other + len(new), alias="VER-01")
    if m.get("profile_hash") and m.get("profile_hash") != ctx.stats.get("profile_hash"):
        ctx.add("VER-009", "INFO", "versions", "The rule profile differs from the one used for the accepted snapshot.",
                "پروفایل قواعد با پروفایل تصویر پذیرفته‌شده متفاوت است.", field="profile_hash", value=str(ctx.stats.get("profile_hash"))[:12], alias="VER-01")
    from .. import __version__
    if m.get("app_version") and m.get("app_version") != __version__:
        ctx.add("VER-009", "INFO", "versions", f"The accepted snapshot was made with GEOVALID PRO {m['app_version']} (now {__version__}).",
                f"تصویر پذیرفته‌شده با نسخهٔ {m['app_version']} ساخته شده است.", field="app_version", value=m["app_version"], alias="VER-01")
