# GEOVALID PRO — v2 upgrade progress

Read first: `06_v2_upgrade_brief.md` (the brief) and `07_v2_gap_analysis.md` (gap table, decisions, plan).

## Current phase

**Phase 1 (P1) — complete, awaiting owner approval** (GEOVALID PRO 0.3.0). Phase 2 starts after approval.

## Decisions

| # | Decision | Source |
|---|---|---|
| D1 | The v2 brief is applied to GEOVALID PRO, with its existing libraries (pandas, numpy, scipy, matplotlib, PySide6, openpyxl, PyYAML). Standard-library-only, single-file and licensing constraints do not apply. | Owner, 2026-11-09 |
| D2 | Severities: Critical = CRITICAL, Major = ERROR, Minor = WARNING, Info = INFO. | 07 §1 |
| D3 | Catalogue rule IDs are kept; brief IDs are aliases (`rule_alias`). New brief checks got new catalogue IDs (ASY-028/029/030; INT-012 used for precision artefacts). | 07 §1 |
| D4 | Windows build stays on Python 3.12. | 07 §1 |
| D5 | Phase 0 output is reported with the Phase 1 checkpoint, because the owner asked to proceed with development. | Owner, 2026-11-09 |
| D6 | The brief's default severities are a `severity_overrides` block in the default profile (editable, removable), not code changes, except where one rule emits different severities by case (INT-001, INT-002, SUR-013, SUR-015, SUR-023, INT-007). | P1 |
| D7 | SUR-023 compares the collar with the first station only when that station is within 50 m (`max_first_depth_m`). | P1 |
| D8 | ASY-030 "above detection" = above the column's largest DL and above its lowest reported value (unstated reporting floor). | P1 |
| D9 | Per-hole hashes use parsed values (trailing zeros, row and column order do not change them) and the table kind, not the file name. | P1 |

## Done

- **Phase 0:** brief saved (`06`), gap analysis and plan (`07`), this file.
- **Phase 1 (0.3.0):**
  - Core: issue fields (category, alias, source file, line, fix class, standards, emitted severity); registry (`core/registry.py`); severity overrides and disabled rules; global depth tolerance with precision artefacts (INT-012); file, per-hole, dataset and profile hashes; fix classes with approval, corrected copies and `fix_log.csv`; JSON profiles; generated `RULE_CATALOGUE.md`.
  - Rules: SRV-01…15 (SUR-007, 009, 012, 013, 014, 015, 023, 027 new or extended), SCH-05/04b (COL-003, SUR-001, INT-006), SCH-06 (IMP-006), COL-01 (COL-002), COL-04 (IMP-012), COL-08 (COL-014), INT-01…07 (INT-001, 002, 007, 012, SMP-001, SMP-002), VAL-01…10 (ASY-002, 003, 010, 015, 019, 028, 029, 030, INT-015). 90 rules run.
  - Outputs: `issues.json`, HTML report (PASS/FAIL per rule, status by hole, filters, fingerprints), evidence pack HTML + JSON (`EVIDENCE_SCHEMA.md`), `hole_hashes.csv`.
  - GUI: Survey QA, Values, Rules & profiles, Evidence pack pages; fix approval dialog; Issue Browser filters, source-row viewer and export.
  - Tests: 57 (recall and clean twin regressions, 29 v2 rule tests with positive and negative cases, 6 output tests, chart tests).
  - Performance: 10 000 holes, 1.09 M rows: ~105 s full validation (`tools/perf_bench.py`). INT-009 and IMP-012 were rewritten for speed.

## Pending

- **P2:** version comparison (three-stage interval diff, change classes, metal deltas, accepted snapshots, VER rules); lab and QA/QC reconciliation (REC-01…07, needs R1); cross-table (XTB-01…07); topography readers (R2) and licence-boundary formats; COL-06 exemptions; UTM ↔ WGS84.
- **P3:** project files and headless `--project`, log file; spatial clash / twins / drill-type bias (SPA-02…05); anomaly assist (F12).

## Open questions

1. **R1:** GEOQAQC source (`GEOQAQC.py`) or sample files, so the lab / QA-QC file format is identical. Needed for P2 reconciliation.
2. Packaging: GEOVALID PRO is built by `.github/workflows/geovalid-windows.yml` (PyInstaller, one portable folder with `GEOVALID.exe` and a console `geovalid-cli.exe`). Confirm this remains the delivery workflow.
