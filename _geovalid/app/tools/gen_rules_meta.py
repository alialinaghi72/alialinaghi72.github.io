"""Regenerate geovalid_pro/resources/rules_meta.json from the approved rule catalogue.

Run from the app folder:  python tools/gen_rules_meta.py ../docs/03_rule_catalogue.md
The catalogue is the specification; titles, default severities, references and JORC
tags shown by the software come from it, so code and catalogue cannot drift apart.
"""
import json
import re
import sys
from pathlib import Path


def main(catalogue: str) -> None:
    text = Path(catalogue).read_text(encoding="utf-8")
    body = text[text.index("## 2. Rule tables"):text.index("## 3. Summary")]
    rules = {}
    for line in body.splitlines():
        if not re.match(r"^\| [A-Z]{3}-\d{3} \|", line):
            continue
        cells = [c.strip() for c in re.split(r"(?<!\\)\|", line.strip().strip("|"))]
        rid, title, logic, params, sev, ref, fix, jorc, status = cells
        t_en, _, t_fa = title.partition(" / ")
        clean = lambda s: re.sub(r"\s+", " ", s.replace("\\|", "|")).strip()
        rules[rid] = {
            "id": rid, "family": rid[:3], "title_en": clean(t_en), "title_fa": clean(t_fa),
            "severity": clean(sev), "logic": clean(logic), "parameters": clean(params),
            "reference": clean(ref), "fix": clean(fix), "jorc": clean(jorc), "status": clean(status),
        }
    out = Path(__file__).resolve().parents[1] / "geovalid_pro" / "resources" / "rules_meta.json"
    out.write_text(json.dumps(rules, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(rules)} rules -> {out}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "../docs/03_rule_catalogue.md")
