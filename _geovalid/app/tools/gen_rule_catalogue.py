"""Generate docs/RULE_CATALOGUE.md from the rule registry (v2 brief §5.3, deliverable 3).

Run from the app folder:  python tools/gen_rule_catalogue.py [../docs/RULE_CATALOGUE.md]
Lists every rule the software runs, with its v2 alias, category, description, logic, catalogue and effective default
severity, thresholds and standards tags. It reads the registry and the default profile, never a hand-kept list.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from geovalid_pro import __version__  # noqa: E402
from geovalid_pro.core.registry import CATEGORIES, STANDARDS, describe  # noqa: E402
from geovalid_pro.engine import IMPORT_RULES, default_params  # noqa: E402
from geovalid_pro.rules import REGISTRY  # noqa: E402


def _cell(x) -> str:
    return str(x).replace("|", "\\|").replace("\n", " ")


def main(out: str) -> None:
    params = default_params()
    ids = list(dict.fromkeys(IMPORT_RULES + [r.id for r in REGISTRY]))
    docs = {r.id: (r.fn.__doc__ or "").strip() for r in REGISTRY}
    lines = [f"# GEOVALID PRO {__version__} — rule catalogue (generated)", "",
             "Generated from the rule registry by `tools/gen_rule_catalogue.py`; do not edit by hand. The design specification of every",
             "rule, including those not yet implemented, is `03_rule_catalogue.md`.", "",
             f"{len(ids)} rules run in this version. Severities: Critical = CRITICAL, Major = ERROR, Minor = WARNING, Info = INFO.", "",
             "## Categories", "", "| Cat. | Name | فارسی |", "|---|---|---|"]
    lines += [f"| {k} | {en} | {fa} |" for k, (en, fa) in CATEGORIES.items()]
    lines += ["", "## Standards tags", "", "| Tag | Clause |", "|---|---|"] + [f"| `{k}` | {v} |" for k, v in STANDARDS.items()]
    lines += ["", "## Rules", "", "| ID | v2 ID | Cat. | Name | Default severity (catalogue) | Profile override | Thresholds | Standards |",
              "|---|---|---|---|---|---|---|---|"]
    for rid in sorted(ids, key=lambda r: (describe(r)["category"], r)):
        d = describe(rid, params)
        ov = d["severity_override"]
        ov = ov if isinstance(ov, str) else (", ".join(f"{a}→{b}" for a, b in ov.items()) if ov else "")
        prm = ", ".join(f"`{k}` {v}" for k, v in d["parameters"].items())
        lines.append(f"| {rid} | {', '.join(d['aliases'])} | {d['category']} | {_cell(d['name_en'])} / {_cell(d['name_fa'])} | "
                     f"{_cell(d['default_severity'])} | {_cell(ov)} | {_cell(prm)} | {', '.join(d['standards'])} |")
    lines += ["", "## Logic", ""]
    for rid in sorted(ids):
        d = describe(rid, params)
        lines += [f"### {rid} — {d['name_en']}", "", f"*{d['name_fa']}* · category {d['category']} ({d['category_name_en']})"
                  + (f" · v2 {', '.join(d['aliases'])}" if d["aliases"] else ""), ""]
        if docs.get(rid):
            lines += [docs[rid], ""]
        lines += [f"Catalogue logic: {d['logic']}", ""]
    Path(out).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{len(ids)} rules -> {out}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else str(Path(__file__).resolve().parents[2] / "docs" / "RULE_CATALOGUE.md"))
