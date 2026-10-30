# GEOVALID PRO — application (v0.2.0)

Implementation of the design package in `../docs/`. User guide: [`README_RUN.md`](README_RUN.md).

```
python -m pip install -r requirements.txt
python -m geovalid_pro                      # GUI
python -m geovalid_pro run --sample --out out --lang both     # CLI on the synthetic database
python -m pytest -q                         # gates: 100 % recall on injected errors, clean twin free of ERROR/CRITICAL
python tools/gen_rules_meta.py ../docs/03_rule_catalogue.md   # refresh rule titles/severities from the catalogue
```

Windows build: `packaging\build_windows.bat`, or the GitHub Actions workflow `.github/workflows/geovalid-windows.yml`
(builds `dist/GEOVALID/GEOVALID.exe` + `geovalid-cli.exe`, smoke-tests both and uploads a zip artifact).

| Package | Content |
|---|---|
| `core/` | issue model and fingerprints, Persian-aware normalisation (digits, ٫, Jalali dates), canonical tables, context |
| `io/` | readers (CSV any delimiter/encoding, XLSX/XLS multi-sheet), automatic mapping with en/fa synonyms, DEM (.asc, XYZ→TIN), licence polygon, writers |
| `analysis/` | minimum-curvature / tangential desurvey, assay code and unit parsing, spatial statistics, collar survey-method inference, grade versus logged geology (`categorical.py`: η², Kruskal–Wallis, Cramér's V, contacts, swaths, grade–length) |
| `rules/` | 71 registered rules + 5 import-stage rules (COL, SUR, INT, ASY, QAQ, LIT, GEO, DEN, CRS, IMP), IDs from the catalogue |
| `report/` | visual identity (`theme.py`: palettes, Ivory/Obsidian themes, fonts), 26 matplotlib charts and the self-contained bilingual HTML report |
| `gui/` | PySide6 desktop application (`style.py`: Obsidian/Ivory style sheets and drawn icons) |
| `synth.py` | synthetic porphyry database (grade controlled by host rock, alteration and weathering) + error injector + manifest |
| `tools/` | `gen_rules_meta.py`, `make_icon.py`, `make_fonts.py` (cuts the bundled Vazirmatn/Inter font files) |
