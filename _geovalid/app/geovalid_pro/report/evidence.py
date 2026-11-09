"""Data Verification Evidence Pack (v2 brief §8.3): HTML + JSON, structured by the standards clauses of §8.2.

For each clause: the checks run, their results, open issues, and — where they apply — fixes applied, the version-diff
summary, the QA/QC reconciliation summary and the random-audit results. It ends with three empty sections that only the
Qualified / Competent Person writes: the tool never states an opinion. JSON schema: `docs/EVIDENCE_SCHEMA.md`.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from .. import APP_NAME, __version__
from ..core.issues import SEV_RANK, SEVERITIES
from ..core.registry import CATEGORIES, STANDARDS, aliases, category, standards_refs

SCHEMA = "geovalid-evidence/1.0"
QP_SECTIONS = [("procedures_applied", "Procedures applied", "روش‌های به‌کاررفته"),
               ("limitations", "Limitations", "محدودیت‌ها"),
               ("opinion_on_adequacy", "Opinion on adequacy", "نظر دربارهٔ کفایت داده‌ها")]


def _records(df: pd.DataFrame, cols: list[str], n: int | None = None) -> list[dict]:
    if df is None or df.empty:
        return []
    d = df[[c for c in cols if c in df.columns]]
    if n:
        d = d.head(n)
    return json.loads(d.to_json(orient="records", force_ascii=False, date_format="iso"))


def build(res) -> dict:
    ctx, iss, mx = res.ctx, res.issues, res.matrix
    open_iss = iss[iss["status"].fillna("open") == "open"] if not iss.empty else iss
    rules = []
    for r in mx.itertuples():
        rules.append({"id": r.rule_id, "aliases": aliases(r.rule_id), "name": r.title_en, "category": category(r.rule_id),
                      "status": r.status, "result": getattr(r, "result", r.status), "n_issues": int(r.n_issues),
                      "worst": r.worst if isinstance(getattr(r, "worst", None), str) else None,
                      "standards": standards_refs(r.rule_id)})
    clauses = []
    for tag, title in STANDARDS.items():
        rs = [x for x in rules if tag in x["standards"]]
        ids = {x["id"] for x in rs}
        sub = open_iss[open_iss["rule_id"].isin(ids)] if not open_iss.empty else open_iss
        clauses.append({
            "tag": tag, "title": title, "rules": rs,
            "results": {k: sum(1 for x in rs if x["result"] == k) for k in ("PASS", "FAIL", "NOT_APPLICABLE", "DISABLED", "FAILED")},
            "open_issues": {s: int((sub["severity"] == s).sum()) if not sub.empty else 0 for s in SEVERITIES},
            "top_issues": _records(sub.assign(_r=sub["severity"].map(SEV_RANK)).sort_values("_r") if not sub.empty else sub,
                                   ["issue_id", "rule_id", "severity", "table", "hole_id", "from_m", "to_m", "source_file", "src_row", "message_en"], 25),
        })
    fix_log = ctx.stats.get("fix_log")
    qaqc_rules = [x for x in rules if x["id"].startswith("QAQ")]
    rates = ctx.stats.get("qaqc_rates", {})
    by_sev = iss["severity"].value_counts().to_dict() if not iss.empty else {}
    by_cat = iss["category"].value_counts().to_dict() if not iss.empty and "category" in iss else {}
    hh = ctx.stats.get("hole_hashes")
    return {
        "schema": SCHEMA,
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "application": {"name": APP_NAME, "version": __version__},
        "run": {"run_id": res.run_id, "project": res.spec.project_name, "started": res.started, "finished": res.finished},
        "dataset": {"files": ctx.stats.get("file_hashes", []), "dataset_hash": ctx.stats.get("dataset_hash"),
                    "hole_count": int(len(hh)) if hh is not None else 0, "hole_hashes_file": "hole_hashes.csv"},
        "profile": {"hash": ctx.stats.get("profile_hash"), "depth_tolerance_m": ctx.params.get("depth_eps_m"),
                    "severity_overrides": ctx.params.get("severity_overrides") or {}, "disabled_rules": ctx.params.get("disabled_rules") or []},
        "summary": {"issues_by_severity": {s: int(by_sev.get(s, 0)) for s in SEVERITIES},
                    "issues_by_category": {k: int(by_cat.get(k, 0)) for k in CATEGORIES},
                    "rules": {k: int((mx["result"] == k).sum()) for k in ("PASS", "FAIL", "NOT_APPLICABLE", "DISABLED", "FAILED")}},
        "clauses": clauses,
        "fixes": {"applied": bool(fix_log is not None and len(fix_log)), "log_file": "fix_log.csv" if fix_log is not None else None,
                  "by_class": fix_log.groupby("fix_class").size().to_dict() if fix_log is not None and len(fix_log) else {},
                  "log": _records(fix_log, ["fix_class", "rule", "file", "row", "field", "old", "new", "timestamp", "user"], 500)},
        "version_comparison": _versions(ctx),
        "topography": {"surfaces": ctx.stats.get("topography") or [], "licence": ctx.stats.get("licence_info"),
                       "sanity": {k: v for k, v in (ctx.stats.get("topo_sanity") or {}).items()} or {"status": "not run"}},
        "qaqc_reconciliation": {"status": "QA/QC rules" if qaqc_rules else "not run", "rules": qaqc_rules,
                                "insertion_rates": {k: {"originals": n, **{kk: round(float(v), 3) for kk, v in r.items()}} for k, (n, r) in rates.items()},
                                "lab_file_reconciliation": ctx.stats.get("lab_reconciliation") or {"status": "not run"}},
        "random_audit": ctx.stats.get("random_audit") or {"status": "not run"},
        "qp_sections": {k: "" for k, _, _ in QP_SECTIONS},
    }


def _versions(ctx) -> dict:
    """v2 F6: comparison summary (holes, change classes, metal) and the accepted snapshot checked by VER-009."""
    out = dict(ctx.stats.get("version_summary") or {"status": "not run"})
    if "version" in ctx.stats:
        out["change_log_file"] = "change_log.csv"
    snap = ctx.stats.get("snapshot")
    if snap:
        iss = ctx.log.rows
        locked_changed = sorted({r["hole_id"] for r in iss if r["rule_id"] == "VER-009" and r["severity"] == "CRITICAL" and r["hole_id"]})
        out["accepted_snapshot"] = {"file": snap.get("_file"), "accepted_at": snap.get("accepted_at"), "reviewer": snap.get("reviewer"),
                                    "note": snap.get("note"), "app_version": snap.get("app_version"), "dataset_hash": snap.get("dataset_hash"),
                                    "locked_holes": len(snap.get("locked_holes", [])), "locked_holes_changed": locked_changed}
    return out


def _h(x) -> str:
    import html
    return html.escape("" if x is None else str(x))


def to_html(pack: dict, lang: str = "en") -> str:
    from .html import CSS, _font_b64, table
    fa = lang == "fa"
    T = (lambda e, f: f if fa else e)
    parts = []
    s = pack["summary"]
    kpi = "".join(f'<div class="kpi {k[0].lower()}"><span>{k.title()}</span><b>{s["issues_by_severity"][k]:,}</b></div>' for k in SEVERITIES)
    kpi += "".join(f'<div class="kpi g"><span>{lab}</span><b>{s["rules"][k]}</b></div>' for k, lab in
                   (("PASS", T("Rules passed", "قواعد بدون مسئله")), ("FAIL", T("Rules with findings", "قواعد دارای مسئله")),
                    ("NOT_APPLICABLE", T("Not applicable", "غیرقابل اجرا")), ("DISABLED", T("Disabled", "غیرفعال"))))
    hero = (f'<header class="hero"><div class="in"><div class="brand"><i></i>GEOVALID PRO</div>'
            f'<h1>{T("Data Verification Evidence Pack", "بستهٔ مستندات راستی‌آزمایی داده‌ها")}</h1><div class="chips">'
            f'<span class="chip">{T("Project", "پروژه")}: <b>{_h(pack["run"]["project"])}</b></span>'
            f'<span class="chip">{T("Run", "اجرا")}: <b class="ltr">{_h(pack["run"]["run_id"][:8])}</b> · <b class="ltr">{_h(pack["run"]["started"])}</b></span>'
            f'<span class="chip">{T("Software", "نرم‌افزار")}: <b class="ltr">{_h(pack["application"]["name"])} {_h(pack["application"]["version"])}</b></span>'
            f'<span class="chip">{T("Schema", "قالب")}: <b class="ltr">{_h(pack["schema"])}</b></span></div><div class="kpis">{kpi}</div></div></header>')
    nav = []

    def sec(i, title, body):
        nav.append(f"<a href='#e{i}'><span>{i}</span>{_h(title)}</a>")
        parts.append(f"<section id='e{i}'><h2><span class='n'>{i}</span>{_h(title)}</h2>{body}</section>")

    fp = pd.DataFrame(pack["dataset"]["files"])
    body = (f"<p class='lead'>{T('Every number in this pack refers to the inputs below. Re-running GEOVALID PRO on files with the same SHA-256 and the same profile hash reproduces it.', 'همهٔ اعداد این بسته به ورودی‌های زیر مربوط است. اجرای دوباره روی فایل‌هایی با همین SHA-256 و همین پروفایل همین نتایج را می‌دهد.')}</p>"
            + table(fp, None, None) +
            table(pd.DataFrame([{T("Dataset hash (per-hole canonical)", "اثرانگشت مجموعهٔ داده"): pack["dataset"]["dataset_hash"],
                                 T("Holes", "گمانه‌ها"): pack["dataset"]["hole_count"],
                                 T("Rule-profile hash", "اثرانگشت پروفایل قواعد"): pack["profile"]["hash"],
                                 T("Depth tolerance (m)", "رواداری عمق (متر)"): pack["profile"]["depth_tolerance_m"]}])))
    sec(1, T("Dataset and profile fingerprints", "اثرانگشت داده‌ها و پروفایل"), body)
    n = 2
    for c in pack["clauses"]:
        rs = pd.DataFrame(c["rules"])
        if rs.empty:
            continue
        rs["aliases"] = rs["aliases"].map(", ".join)
        res_ = c["results"]
        oi = c["open_issues"]
        body = (f"<p class='lead'>{_h(c['title'])}</p><div class='note'>{T('Checks run', 'کنترل‌های اجراشده')}: {len(rs)} · PASS {res_['PASS']} · FAIL {res_['FAIL']} · "
                f"{T('not applicable', 'غیرقابل اجرا')} {res_['NOT_APPLICABLE']} · {T('disabled', 'غیرفعال')} {res_['DISABLED']} — "
                f"{T('open issues', 'مسائل باز')}: " + ", ".join(f"{k} {v}" for k, v in oi.items()) + "</div>"
                f"<details><summary>{T('Checks and results', 'کنترل‌ها و نتایج')} ({len(rs)})</summary>"
                + table(rs, ["id", "aliases", "name", "category", "result", "n_issues", "worst"],
                        ["Rule", "v2 ID", T("Check", "کنترل"), "Cat.", T("Result", "نتیجه"), "n", T("Worst", "شدیدترین")]) + "</details>")
        ti = pd.DataFrame(c["top_issues"])
        if not ti.empty:
            body += f"<h3>{T('Most severe open issues', 'شدیدترین مسائل باز')}</h3>" + table(ti, ["issue_id", "severity", "rule_id", "hole_id", "source_file", "src_row", "message_en"],
                                                                                              ["#", T("Severity", "شدت"), T("Rule", "قاعده"), T("Hole", "گمانه"), T("File", "فایل"), T("Row", "ردیف"), T("Message", "شرح")])
        sec(n, c["tag"], body)
        n += 1
    fx = pack["fixes"]
    body = (f"<p>{T('No fix was applied: all findings are flags only.', 'هیچ اصلاحی اعمال نشده است: همهٔ یافته‌ها فقط علامت‌گذاری شده‌اند.')}</p>" if not fx["applied"] else
            table(pd.DataFrame([fx["by_class"]])) + table(pd.DataFrame(fx["log"]).head(200)))
    sec(n, T("Fixes applied (fix log)", "اصلاحات اعمال‌شده (گزارش اصلاح)"), body)
    n += 1
    vc = pack["version_comparison"]
    if vc.get("status") == "not run" and not vc.get("accepted_snapshot"):
        body = f"<p>{T('No previous version or accepted snapshot was supplied.', 'نسخهٔ قبلی یا تصویر پذیرفته‌شده‌ای داده نشده است.')}</p>"
    else:
        body = ""
        if vc.get("holes"):
            body += table(pd.DataFrame([vc["holes"]])) + f"<p class='note'>{T('Unchanged holes are identified by their canonical hash and skipped.', 'گمانه‌های بدون تغییر با اثرانگشت شناسایی و کنار گذاشته شدند.')}</p>"
        if vc.get("change_classes"):
            body += f"<h3>{T('Change classes', 'گونه‌های تغییر')}</h3>" + table(pd.DataFrame(sorted(vc["change_classes"].items(), key=lambda kv: -kv[1]), columns=["class", "n"]))
        if vc.get("metal"):
            m = pd.DataFrame(vc["metal"])
            for c in ("old_metres", "new_metres"):
                m[c] = m[c].map(lambda v: f"{v:,.1f}")
            for c in ("old_metal", "new_metal", "delta_metal", "old_grade", "new_grade"):
                m[c] = m[c].map(lambda v: "" if v is None or pd.isna(v) else f"{v:,.4g}")
            m["delta_pct"] = m["delta_pct"].map(lambda v: "" if v is None or pd.isna(v) else f"{v:+.2f} %")
            body += f"<h3>{T('Metal and grade reconciliation', 'تطبیق فلز و عیار')}</h3>" + table(m)
        if vc.get("deleted_holes"):
            body += f"<p>{T('Deleted holes', 'گمانه‌های حذف‌شده')}: {_h(', '.join(vc['deleted_holes'][:50]))}</p>"
        if vc.get("change_log_file"):
            body += f"<p class='note'>{T('Full change log', 'گزارش کامل تغییرات')}: change_log.csv</p>"
        snap = vc.get("accepted_snapshot")
        if snap:
            ch = snap.get("locked_holes_changed") or []
            body += (f"<h3>{T('Accepted snapshot', 'تصویر پذیرفته‌شده')}</h3>" + table(pd.DataFrame([{k: v for k, v in snap.items() if k != 'locked_holes_changed'}]))
                     + f"<p>{T('Locked holes changed since acceptance (VER-009)', 'گمانه‌های قفل‌شدهٔ تغییرکرده (VER-009)')}: "
                     + (f"<b>{_h(', '.join(ch[:50]))}</b>" if ch else T("none", "هیچ")) + "</p>")
    sec(n, T("Version comparison", "مقایسهٔ نسخه‌ها"), body)
    n += 1
    tp = pack.get("topography") or {}
    if tp.get("surfaces") or tp.get("licence"):
        rows = [{"file": t.get("file"), "label": t.get("label"), "date": t.get("date"), "format": t.get("format"),
                 "extent": ", ".join(f"{v:,.1f}" for v in (t.get("extent") or [])), "resolution": t.get("resolution"),
                 "points / cells": t.get("n_points") or t.get("n_cells") or t.get("n_triangles"),
                 "crs": ", ".join(f"{k}={v}" for k, v in (t.get("crs") or {}).items() if k != "wkt")} for t in tp.get("surfaces", [])]
        body = table(pd.DataFrame(rows)) if rows else ""
        notes = [n_ for t in tp.get("surfaces", []) for n_ in t.get("notes", [])]
        if tp.get("licence"):
            li = tp["licence"]
            body += f"<p>{T('Licence boundary', 'محدودهٔ پروانه')}: {_h(li['format'])}, {li['polygons']} polygon(s), {li['rings']} ring(s), {li['vertices']} vertices</p>"
            notes += li.get("notes", []) + li.get("alignment", [])
        san = tp.get("sanity") or {}
        if san.get("findings"):
            body += "<ul>" + "".join(f"<li><b>{_h(sv)}</b> {_h(m)}</li>" for sv, m in san["findings"]) + "</ul>"
        if notes:
            body += "<ul class='note'>" + "".join(f"<li>{_h(x)}</li>" for x in dict.fromkeys(notes)) + "</ul>"
        sec(n, T("Topography and licence boundary", "توپوگرافی و محدودهٔ پروانه"), body)
        n += 1
    q = pack["qaqc_reconciliation"]
    qr = pd.DataFrame(q["rules"])
    body = (table(qr, ["id", "name", "result", "n_issues", "worst"]) if not qr.empty else "") + \
        (table(pd.DataFrame([{"table": k, **v} for k, v in q["insertion_rates"].items()])) if q["insertion_rates"] else "")
    lr = q["lab_file_reconciliation"]
    if lr.get("status") == "not run":
        body += f"<p>{T('Laboratory-file reconciliation: no laboratory file supplied.', 'تطبیق با فایل آزمایشگاه: فایل آزمایشگاه داده نشده است.')}</p>"
    else:
        body += f"<h3>{T('Laboratory-file reconciliation', 'تطبیق با فایل آزمایشگاه')} — {_h(lr.get('lab_file'))}</h3>"
        if lr.get("samples"):
            body += table(pd.DataFrame([lr["samples"]]))
        if lr.get("values"):
            body += table(pd.DataFrame(lr["values"]))
        er = lr.get("error_rate")
        if er:
            body += (f"<p>{T('Project error rate', 'نرخ خطای پروژه')}: <b>{er['rate_pct']:.2f} %</b> ({er['mismatched']} / {er['compared']}); "
                     f"{T('95 % Clopper–Pearson upper bound', 'حد بالای ۹۵ درصد کلاپر–پیرسون')} {er['upper95_pct']:.2f} %</p>")
    sec(n, T("QA/QC and laboratory reconciliation", "کنترل کیفیت و تطبیق آزمایشگاه"), body)
    n += 1
    ra = pack["random_audit"]
    body = f"<p>{_h(ra.get('status'))}</p>"
    keys = ["seed", "pct", "population", "selected", "checked", "verified", "discrepancies", "unchecked", "rate_pct", "upper95_pct", "selection_matches"]
    if any(k in ra for k in keys):
        body += table(pd.DataFrame([{k: ra.get(k) for k in keys if k in ra}]))
    if ra.get("selection_hash"):
        body += f"<p class='note ltr'>selection SHA-256 {_h(ra['selection_hash'])}</p>"
    if ra.get("discrepancy_rows"):
        body += f"<h3>{T('Discrepancies found by the reviewer', 'مغایرت‌های یافته‌شده توسط بازبین')}</h3>" + table(pd.DataFrame(ra["discrepancy_rows"]))
    sec(n, T("Random verification audit", "ممیزی تصادفی راستی‌آزمایی"), body)
    n += 1
    qp = "".join(f"<h3>{_h(T(en, fa_))}</h3><div style='min-height:140px;border:1.5px dashed #B07D3A;border-radius:10px;padding:12px;color:#8A7A60'>"
                 f"{T('To be written by the Qualified / Competent Person. GEOVALID PRO does not express an opinion.', 'توسط شخص صلاحیت‌دار نوشته شود. این نرم‌افزار نظری ارائه نمی‌کند.')}</div>"
                 for _, en, fa_ in QP_SECTIONS)
    sec(n, T("Qualified Person sections", "بخش‌های شخص صلاحیت‌دار"), qp)
    css = CSS.replace("__FONT__", _font_b64())
    return (f"<!doctype html><html lang='{lang}' dir='{'rtl' if fa else 'ltr'}'><head><meta charset='utf-8'>"
            f"<meta name='viewport' content='width=device-width,initial-scale=1'><title>Evidence Pack – {_h(pack['run']['project'])}</title>"
            f"<style>{css}</style></head><body>{hero}<div class='layout'><nav class='toc'><h4>{T('Contents', 'فهرست')}</h4>{''.join(nav)}</nav>"
            f"<main>{''.join(parts)}</main></div></body></html>")


def write(res, out_dir, lang: str = "en") -> dict:
    out = Path(out_dir)
    pack = build(res)
    jp = out / "evidence_pack.json"
    jp.write_text(json.dumps(pack, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    files = {"evidence_json": jp}
    for lg in ([lang] if lang in ("fa", "en") else ["en", "fa"]):
        hp = out / f"evidence_pack_{lg}.html"
        hp.write_text(to_html(pack, lg), encoding="utf-8")
        files[f"evidence_{lg}"] = hp
    hh = res.ctx.stats.get("hole_hashes")
    if hh is not None:
        hh.to_csv(out / "hole_hashes.csv", index=False, encoding="utf-8-sig")
    return files
