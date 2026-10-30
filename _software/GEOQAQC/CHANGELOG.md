# Changelog

## 2.0 — 2026-10-30

### Added
- Automatic validation and cleaning of raw data (rules C01–C18) with a full
  cleaning log; genuine QC failures are never removed.
- Diagnosis engine: findings attributed to eight stages of the sample chain,
  with severity, evidence, probable cause, actions, owner and timing; a verdict
  per element (suitable / restricted / remediate).
- New methods: pooled laboratory drift and CUSUM, bias per batch, accuracy
  curve (proportional vs constant bias), grade coverage of the CRMs, coarse vs
  pulp blanks and carry-over test, max-min plot, precision by grade quartile,
  splitting-bias test, error budget by stage, batch acceptance and re-assay
  ranges, source-of-error matrix and scorecard.
- Persian consultant report in HTML, PDF (via Edge/Chrome) and Word.
- Rules page: every cleaning, diagnosis, batch and severity threshold is
  editable, saved in the session and flagged in the protocol when changed.
- Excel (.xlsx) input; decimal-comma tables; Persian and Arabic-Indic digits.
- New interface: navigation rail, dashboard, diagnosis with the chart behind
  each finding, anti-aliased charts with zoom, pan, sample-ID hover and
  PNG/SVG/PDF export.
- Demonstration dataset with planted defects; `--selftest`; Windows build on
  GitHub Actions.

### Changed
- The code is a package (`geoqaqc/`); `GEOQAQC.py` remains the entry point.
- Requires matplotlib and python-docx (bundled in the EXE).
- Blanks are analysed per blank type; CRMs keyed by their certificate label.

### Compatibility
- With every cleaning rule switched off, results equal GEOQAQC 1.1 on the 1.1
  sample data (checked by an automated test).
- 1.1 session files still load.

## 1.1
- Fixed the empty-cell crash of the detection-limit flag and short duplicate
  codes; grouping by hole, batch, drill type and laboratory; Q-Q plots;
  check/umpire module.
