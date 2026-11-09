"""Rule registry metadata (v2 brief §5.3): category A–J, brief aliases, standards clause tags, effective severity.

The catalogue (`03_rule_catalogue.md` → `rules_meta.json`) stays the specification of each rule. This module adds what
the v2 brief asks every rule to carry, and resolves the profile's per-rule settings (enabled flag, severity override,
parameters), so the GUI, the reports, the evidence pack and `RULE_CATALOGUE.md` all read one source.
"""
from __future__ import annotations

import hashlib
import json

from .issues import SEV_RANK, rules_meta

CATEGORIES = {
    "A": ("Schema and identifiers", "ساختار و شناسه‌ها"),
    "B": ("Collars", "دهانهٔ گمانه‌ها"),
    "C": ("Downhole survey", "انحراف‌سنجی درون‌چاهی"),
    "D": ("Intervals and samples", "بازه‌ها و نمونه‌ها"),
    "E": ("Values", "مقادیر"),
    "F": ("Cross-table consistency", "سازگاری میان جداول"),
    "G": ("Laboratory and QA/QC reconciliation", "تطبیق آزمایشگاه و کنترل کیفیت"),
    "H": ("Spatial, topography and boundary", "مکانی، توپوگرافی و محدوده"),
    "I": ("Versions", "نسخه‌ها"),
    "J": ("Profiles and process", "پروفایل و فرایند"),
}
_BY_FAMILY = {"IMP": "A", "COL": "B", "SUR": "C", "INT": "D", "SMP": "D", "ASY": "E", "LIT": "E", "ALT": "E", "STR": "E",
              "MAG": "E", "MIN": "E", "GEO": "F", "DEN": "F", "WTH": "F", "CRS": "F", "QAQ": "G", "SPA": "H", "VER": "I"}
_BY_RULE = {"COL-003": "A", "SMP-001": "A", "SUR-016": "H", "COL-005": "H", "COL-011": "H", "COL-012": "H",
            "CRS-002": "H", "CRS-006": "H", "ASY-009": "G", "ASY-020": "G", "SMP-004": "G", "ASY-008": "F", "INT-011": "F",
            "CRS-004": "F", "CRS-005": "F", "INT-015": "E", "IMP-021": "E", "ASY-031": "E"}

# v2 brief rule IDs (§7) carried by catalogue rules (decision D3).
ALIASES = {
    "SUR-007": ["SRV-01"], "SUR-003": ["SRV-02"], "SUR-004": ["SRV-02"], "SUR-005": ["SRV-03"], "SUR-002": ["SRV-04", "SCH-03"],
    "SUR-017": ["SRV-05"], "SUR-006": ["SRV-06"], "SUR-023": ["SRV-07"], "SUR-010": ["SRV-08"], "SUR-013": ["SRV-09"],
    "SUR-008": ["SRV-10"], "SUR-012": ["SRV-11"], "SUR-014": ["SRV-12"], "SUR-027": ["SRV-13"], "SUR-015": ["SRV-14"],
    "SUR-009": ["SRV-15"], "COL-003": ["SCH-05"], "SUR-001": ["SCH-04", "SCH-04b"], "INT-006": ["SCH-04", "SCH-04b"],
    "COL-008": ["SCH-04"], "COL-009": ["SCH-04"], "IMP-010": ["SCH-01"], "IMP-005": ["SCH-02"], "COL-001": ["SCH-03"],
    "INT-003": ["SCH-03"], "IMP-006": ["SCH-06"], "COL-002": ["COL-01"], "COL-004": ["COL-02"], "COL-006": ["COL-03"],
    "IMP-012": ["COL-04"], "COL-007": ["COL-07"], "COL-014": ["COL-08"], "INT-001": ["INT-01", "INT-02"], "INT-002": ["INT-03"],
    "INT-004": ["INT-04"], "INT-012": ["INT-03", "INT-04"], "INT-005": ["INT-05"], "INT-007": ["INT-06"], "SMP-001": ["INT-07"], "SMP-002": ["INT-07"],
    "ASY-002": ["VAL-01"], "ASY-005": ["VAL-02"], "ASY-001": ["VAL-03"], "ASY-004": ["VAL-03"], "ASY-010": ["VAL-04"],
    "ASY-019": ["VAL-04"], "ASY-003": ["VAL-05"], "ASY-028": ["VAL-06"], "ASY-015": ["VAL-07"], "INT-015": ["VAL-08"],
    "ASY-029": ["VAL-09"], "ASY-030": ["VAL-10"], "COL-011": ["COL-06"], "COL-012": ["COL-06b"], "COL-005": ["COL-05"],
    "SUR-016": ["SPA-01", "SPA-02"], "GEO-001": ["XTB-02"], "GEO-002": ["XTB-03"], "DEN-001": ["XTB-04"],
    "ASY-008": ["XTB-01"], "INT-011": ["XTB-05"], "WTH-001": ["XTB-06"], "CRS-001": ["XTB-07"], "CRS-006": ["SPA-03", "SPA-04"],
    "CRS-002": ["SPA-05"], "SMP-004": ["REC-01"], "ASY-020": ["REC-02", "REC-03", "REC-04"], "ASY-009": ["REC-05"],
    "CRS-008": ["REC-06"], "VER-009": ["VER-01"],
}

# v2 brief §8.2 clause tags.
STANDARDS = {
    "JORC-T1-S1-Verification": "JORC Table 1 §1 Verification of sampling and assaying",
    "JORC-T1-S1-Location": "JORC Table 1 §1 Location of data points",
    "JORC-T1-S3-DBIntegrity": "JORC Table 1 §3 Database integrity",
    "NI43101-F1-Item12": "NI 43-101 Form 43-101F1 Item 12 Data verification",
    "SK1300-601b96-iii-B-9": "S-K 1300 Item 601(b)(96)(iii)(B)(9) Data verification",
    "CIM2019-4.2": "CIM MRMR Best Practice 2019 §4.2 Database: unintended changes, edits, archiving, units as received",
    "CIM2019-4.5": "CIM MRMR Best Practice 2019 §4.5 Data verification: collars, deviation, log consistency, certificates",
    "CIM2019-6.2": "CIM MRMR Best Practice 2019 §6.2 Unsampled intervals, below-detection and over-limit values, mixed methods",
}
_JORC_MAP = {"T1.07": "JORC-T1-S1-Verification", "T1.06": "JORC-T1-S1-Verification", "T1.08": "JORC-T1-S1-Location",
             "S3.DI": "JORC-T1-S3-DBIntegrity", "NI-12": "NI43101-F1-Item12"}
_CIM_62 = {"ASY", "IMP"} | {"INT-004", "ASY-008", "INT-011"}
_CIM_42 = {"VER", "ASY-001", "ASY-004", "IMP-003", "IMP-011"}


def category(rule_id: str) -> str:
    return _BY_RULE.get(rule_id, _BY_FAMILY.get(rule_id[:3], "J"))


def aliases(rule_id: str) -> list[str]:
    return ALIASES.get(rule_id, [])


def standards_refs(rule_id: str) -> list[str]:
    meta = rules_meta().get(rule_id, {})
    tags = []
    for tok in str(meta.get("jorc", "")).replace(",", ";").split(";"):
        t = _JORC_MAP.get(tok.strip())
        if t and t not in tags:
            tags.append(t)
    if not any(t.startswith("JORC") for t in tags):
        tags.append("JORC-T1-S3-DBIntegrity")
    fam = rule_id[:3]
    if fam in ("COL", "SUR", "LIT", "ALT", "WTH", "GEO", "DEN", "STR", "INT", "CRS", "SMP", "QAQ", "SPA") and rule_id not in ("INT-004",):
        tags.append("CIM2019-4.5")
    if fam in _CIM_62 or rule_id in _CIM_62:
        tags.append("CIM2019-6.2")
    if fam in _CIM_42 or rule_id in _CIM_42:
        tags.append("CIM2019-4.2")
    tags += ["NI43101-F1-Item12", "SK1300-601b96-iii-B-9"]
    return list(dict.fromkeys(tags))


def default_severity(rule_id: str) -> str:
    """Catalogue default as written (may be banded, e.g. 'WARNING/ERROR (banded)')."""
    return rules_meta().get(rule_id, {}).get("severity", "")


def resolve_severity(overrides: dict, rule_id: str, severity: str) -> str:
    """Profile override: a single severity for the whole rule, or a mapping {emitted: wanted}."""
    o = (overrides or {}).get(rule_id)
    if o is None:
        return severity
    if isinstance(o, str):
        return o if o in SEV_RANK else severity
    if isinstance(o, dict):
        v = o.get(severity, severity)
        return v if v in SEV_RANK else severity
    return severity


def is_enabled(params: dict, rule_id: str) -> bool:
    return rule_id not in set(params.get("disabled_rules") or [])


def profile_hash(params: dict) -> str:
    """SHA-256 of the canonical JSON of every setting that changes results (shown in reports, evidence pack, snapshots)."""
    blob = json.dumps(params, sort_keys=True, ensure_ascii=False, default=str, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def describe(rule_id: str, params: dict | None = None) -> dict:
    """Everything known about one rule, for the GUI, reports and RULE_CATALOGUE.md."""
    meta = rules_meta().get(rule_id, {})
    params = params or {}
    return {
        "id": rule_id, "aliases": aliases(rule_id), "category": category(rule_id),
        "category_name_en": CATEGORIES[category(rule_id)][0], "category_name_fa": CATEGORIES[category(rule_id)][1],
        "name_en": meta.get("title_en", ""), "name_fa": meta.get("title_fa", ""), "logic": meta.get("logic", ""),
        "default_severity": meta.get("severity", ""), "severity_override": (params.get("severity_overrides") or {}).get(rule_id),
        "parameters": dict((params.get("rules") or {}).get(rule_id, {})), "enabled": is_enabled(params, rule_id),
        "standards": standards_refs(rule_id), "reference": meta.get("reference", ""), "jorc": meta.get("jorc", ""),
    }
