# GEOVALID PRO — v2 upgrade progress

Read first: `06_v2_upgrade_brief.md` (the brief) and `07_v2_gap_analysis.md` (gap table, decisions, plan).

## Current phase

**Phase 2 (P2) — complete (GEOVALID PRO 0.4.0); awaiting the owner's approval.** Phase 1 (0.3.0) was approved on 2026-11-09.

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
| D10 | R1 option B: GEOQAQC format inferred from sample files; sample-type codes, IS/LNR = not analysed, CRM certified values converted by the declared UNIT, repeated SAMPLE_ID = re-assay (report all). | Owner, 2026-11-09 |
| D9 | Per-hole hashes use parsed values (trailing zeros, row and column order do not change them) and the table kind, not the file name. | P1 |
| D11 | Laboratory reconciliation maps to catalogue IDs SMP-004 (REC-01), ASY-020 (REC-02/03/04), ASY-009 (REC-05), CRS-008 (REC-06); the brief ID of each issue is in `rule_alias`. REC-07 is a workflow (`audit.py`), not a rule. | P2 |
| D12 | Sample and CRM IDs are matched exactly (sample IDs after trimming spaces; CRM IDs also ignoring case). Near matches are suggestions only, taken from the other side's unmatched IDs; `crm_id_aliases` maps CRM spellings explicitly. | P2 |
| D13 | CRS-008 raises CRITICAL for a CRM, blank, pulp duplicate or umpire sample stored as a downhole interval (catalogue), above the brief's Major, because such a row enters composites as real grade. | P2 |
| D14 | XTB-04 user density ranges by code are ERROR (brief Major); robust fences are per code × weathering state (oxidised rock is lighter), falling back to all samples under 20 per group. XTB-06 (WTH-001) is INFO through the profile's severity override (brief Info; catalogue WARNING). | P2 |
| D15 | Topography: scipy (an existing library) provides the local Delaunay triangulation and k-d tree; the brief's "pure Python" applies to formats, which have no third-party readers (no GDAL). Points and contours never form a full-area TIN. | P2 |
| D16 | A geographic surface or boundary is converted to the declared UTM zone, or to the zone of its own location when none is declared; the inference is reported (COL-025). Only WGS 84 is converted; other datums are reported. | P2 |
| D17 | A gross topography sanity failure (no overlap, feet vs metres) stops the per-collar ΔZ rules (COL-011/012) for the run and is reported once by COL-025, instead of one ΔZ error per collar. | P2 |
| D18 | The brief's VER-01 is catalogue VER-009 (VER-001…008 were already defined). Version comparison runs on a previous-version folder (or file list); accepted snapshots are separate JSON manifests. | P2 |

## Done

- **Phase 0:** brief saved (`06`), gap analysis and plan (`07`), this file.
- **Phase 1 (0.3.0):**
  - Core: issue fields (category, alias, source file, line, fix class, standards, emitted severity); registry (`core/registry.py`); severity overrides and disabled rules; global depth tolerance with precision artefacts (INT-012); file, per-hole, dataset and profile hashes; fix classes with approval, corrected copies and `fix_log.csv`; JSON profiles; generated `RULE_CATALOGUE.md`.
  - Rules: SRV-01…15 (SUR-007, 009, 012, 013, 014, 015, 023, 027 new or extended), SCH-05/04b (COL-003, SUR-001, INT-006), SCH-06 (IMP-006), COL-01 (COL-002), COL-04 (IMP-012), COL-08 (COL-014), INT-01…07 (INT-001, 002, 007, 012, SMP-001, SMP-002), VAL-01…10 (ASY-002, 003, 010, 015, 019, 028, 029, 030, INT-015). 90 rules run.
  - Outputs: `issues.json`, HTML report (PASS/FAIL per rule, status by hole, filters, fingerprints), evidence pack HTML + JSON (`EVIDENCE_SCHEMA.md`), `hole_hashes.csv`.
  - GUI: Survey QA, Values, Rules & profiles, Evidence pack pages; fix approval dialog; Issue Browser filters, source-row viewer and export.
  - Tests: 57 (recall and clean twin regressions, 29 v2 rule tests with positive and negative cases, 6 output tests, chart tests).
  - Performance: 10 000 holes, 1.09 M rows: ~105 s full validation (`tools/perf_bench.py`). INT-009 and IMP-012 were rewritten for speed.

- **Phase 2 (0.4.0):**
  - R1 laboratory / QA-QC files (GEOQAQC format, `QAQC_FORMAT.md`): readers, REC-01…06, QAQ-006/007/008/010, CRM unit conversion, random audit (REC-07).
  - Cross-table XTB-01…07 (ASY-008, GEO-001, GEO-002, DEN-001, INT-011, WTH-001, CRS-001).
  - R2 topography: 17 formats with auto-detection, GeoTIFF reader with LZW / Deflate / PackBits / predictors / tiles / BigTIFF and windowed reading, local Delaunay for points and contours, grid-indexed TIN; WGS 84 ↔ UTM; licence boundaries in 5 formats with parts and holes; COL-025 sanity checks; COL-011 exemptions and dated topographies; COL-012 datum offset.
  - Version comparison: hash skipping, three-stage interval diff, change classes, metal deltas for all / common holes, change log; accepted snapshots and VER-009.
  - App pages Cross-table, Lab & QA/QC, Topography & boundary, Versions; evidence-pack sections; CLI options.
  - Tests: 126 (69 new). Rules: 109.

## Pending

- **P3:** project files and headless `--project`, log file; spatial clash / twins / drill-type bias (SPA-02…05); anomaly assist (F12).

## Open questions

1. ~~R1: GEOQAQC format~~ — resolved 2026-11-09 (`QAQC_FORMAT.md`). **Still open:** the owner's GEOQAQC sample files are kept local in `reference/qaqc_samples/` and are not committed, because the repository is public. Ask the owner before publishing them; until then `test_reference_counts` is skipped on CI.
2. Packaging: GEOVALID PRO is built by `.github/workflows/geovalid-windows.yml` (PyInstaller, one portable folder with `GEOVALID.exe` and a console `geovalid-cli.exe`). Confirm this remains the delivery workflow.
3. Proprietary topography formats: Vulcan `.00t` and Datamine `.dm` have no public specification and are refused with that reason (brief R2 asks to report this).
