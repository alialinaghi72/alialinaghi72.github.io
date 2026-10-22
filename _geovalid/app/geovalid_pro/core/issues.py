"""Issue model: one row per finding, with the fields of brief §1.3 plus fingerprint and run_id."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from importlib import resources

import pandas as pd

SEVERITIES = ["CRITICAL", "ERROR", "WARNING", "INFO"]
SEV_RANK = {s: i for i, s in enumerate(SEVERITIES)}
SEV_LETTER = {"CRITICAL": "C", "ERROR": "E", "WARNING": "W", "INFO": "I"}

ISSUE_COLUMNS = [
    "issue_id", "rule_id", "severity", "table", "hole_id", "from_m", "to_m", "field", "value",
    "expected", "message_en", "message_fa", "suggested_fix", "status", "reviewer", "reason",
    "timestamp", "src_row", "fingerprint", "run_id",
]

_META: dict | None = None


def rules_meta() -> dict:
    """Rule titles, default severities and references, generated from the rule catalogue."""
    global _META
    if _META is None:
        raw = resources.files("geovalid_pro.resources").joinpath("rules_meta.json").read_text(encoding="utf-8")
        _META = json.loads(raw)
    return _META


def _fmt(v) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ""
    if isinstance(v, float):
        return f"{v:.6g}"
    return str(v)


def fingerprint(rule_id: str, table: str, hole_id, from_m, to_m, field, value) -> str:
    key = "|".join(["gv1", rule_id, table or "", _fmt(hole_id), _fmt(from_m), _fmt(to_m), field or "", _fmt(value)])
    return hashlib.sha1(key.encode("utf-8")).hexdigest()[:16]


class IssueLog:
    """Collects issues from all rules; never modifies data."""

    def __init__(self, run_id: str, cap_per_rule_table: int = 500):
        self.run_id = run_id
        self.rows: list[dict] = []
        self.cap = cap_per_rule_table
        self._count: dict[tuple[str, str], int] = {}
        self._overflow: dict[tuple[str, str], list] = {}
        self.timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    def add(self, rule_id: str, severity: str, table: str, message_en: str, message_fa: str, *,
            hole_id=None, from_m=None, to_m=None, field=None, value=None, expected=None,
            suggested_fix=None, src_row=None) -> None:
        if severity not in SEV_RANK:
            raise ValueError(f"bad severity {severity} for {rule_id}")
        key = (rule_id, table or "")
        n = self._count.get(key, 0) + 1
        self._count[key] = n
        if n > self.cap:
            ov = self._overflow.setdefault(key, [0, severity])
            ov[0] += 1
            if SEV_RANK[severity] < SEV_RANK[ov[1]]:
                ov[1] = severity
            return
        self.rows.append({
            "rule_id": rule_id, "severity": severity, "table": table, "hole_id": hole_id,
            "from_m": from_m, "to_m": to_m, "field": field, "value": _fmt(value) if value is not None else None,
            "expected": expected, "message_en": message_en, "message_fa": message_fa,
            "suggested_fix": suggested_fix, "status": "open", "reviewer": None, "reason": None,
            "timestamp": self.timestamp, "src_row": src_row,
            "fingerprint": fingerprint(rule_id, table, hole_id, from_m, to_m, field, value),
            "run_id": self.run_id,
        })

    def count(self, rule_id: str) -> int:
        return sum(v for (r, _), v in self._count.items() if r == rule_id)

    def frame(self) -> pd.DataFrame:
        for (rule_id, table), (n, sev) in self._overflow.items():
            self.rows.append({c: None for c in ISSUE_COLUMNS if c != "issue_id"} | {
                "rule_id": rule_id, "severity": sev, "table": table, "value": str(n), "status": "open",
                "message_en": f"{n} further issues of this rule in this table are not listed individually (limit {self.cap}).",
                "message_fa": f"{n} مورد دیگر از این قاعده در این جدول به‌صورت جداگانه فهرست نشده‌اند (سقف {self.cap}).",
                "timestamp": self.timestamp, "run_id": self.run_id,
                "fingerprint": fingerprint(rule_id, table, "OVERFLOW", None, None, None, n)})
        self._overflow = {}
        df = pd.DataFrame(self.rows, columns=[c for c in ISSUE_COLUMNS if c != "issue_id"])
        if df.empty:
            return pd.DataFrame(columns=ISSUE_COLUMNS)
        df = df.drop_duplicates("fingerprint").copy()
        df["_rank"] = df["severity"].map(SEV_RANK)
        df = df.sort_values(["_rank", "rule_id", "table", "hole_id", "from_m"], na_position="last", kind="stable")
        df = df.drop(columns="_rank").reset_index(drop=True)
        df.insert(0, "issue_id", [f"GV-{i + 1:06d}" for i in range(len(df))])
        return df
