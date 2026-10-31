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

### Fixed after the independent review
- Laboratory drift is fitted with one slope and a separate level for each CRM,
  so replacing one CRM with another is no longer reported as drift.
- A laboratory that writes below-detection results as 0 no longer switches the
  blank test off (the detection limit ignores zero '<' values).
- CRMs with no certificate for an element limit its verdict (accuracy unknown).
- C03 no longer drops CRMs or blanks named by their code, or a repeat filed under
  its parent's number; C08 keeps an over-range blank as a failure; C13 counts an
  element only when it both fails its own CRM and matches the other; C15 only
  flags on single-element evidence; "two-thirds" accepts 2 of 3.
- The PDF is printed with a private browser profile, so an open Edge window no
  longer stops it.
- The Windows package unpacks into one folder, `GEOQAQC-2.0`.

### Compatibility
- With every cleaning rule switched off, results equal GEOQAQC 1.1 on the 1.1
  sample data (checked by an automated test).
- 1.1 session files still load.

## 1.1
- Fixed the empty-cell crash of the detection-limit flag and short duplicate
  codes; grouping by hole, batch, drill type and laboratory; Q-Q plots;
  check/umpire module.
