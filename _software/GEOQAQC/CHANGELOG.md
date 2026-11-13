# Changelog

## 2.1 (P1, first part) — 2026-11-13

- **R10** Acceptance limits per element: every criterion (the five rating
  boundaries; GOOD is the acceptance limit) can be set for one element on the
  Criteria page ("Element" selector); elements without their own boundaries
  use the defaults. The analysis, the findings, the charts (including the
  max-min acceptance line) and the report use each element's limits. The
  protocol appendix prints the limits actually used per element.
- **R11** QC reference DL per element (Elements page): it replaces the
  laboratory DL in the blank limits, the low-grade pair cut, the
  Thompson-Howarth reference grade and the C14 / C15 / C16 grade filters.
- **R12** Blank warning and failure limits per element, as x QC DL or as an
  absolute value with unit. A blank above the warning limit makes the batch
  "accepted with conditions"; above the failure limit it fails the batch.
- **R13** High-grade predecessor of the carry-over test as an absolute grade
  per element (otherwise the percentile rule as before).
- **R19** One-click preset **NLR-QAQC-SPC-001 Rev. 0** (Elements page):
  methods, QC DLs, upper limits, absolute blank limits, duplicate / Thompson-
  Howarth / umpire boundaries per element and class, CRM rules and the global
  parameters of section 4. The preset name is saved in the session and shown
  in the document control table and the protocol appendix.

## 2.1 (P0) — 2026-11-13

Correctness fixes from the review of NLR Batch 16 (NLR-QAQC-SPC-001 Rev. 0).
No statistical formula was changed. Behaviour changes:

### Certificates and values
- **R1** A certificate row matches a column by element **and analytical
  method**. An element without suffix is its primary method (Au fire assay;
  Cu, Mo total / four-acid); `_AR` is aqua regia; `Sol` / `CuSol` is acid-
  soluble Cu and never matches a total-Cu column; an optional `METHOD` column
  wins. If two rows still match one CRM x column the run stops with a message
  naming them (before, the last row silently won). Each column's method is
  set on the new **Elements** page. The report lists the certificate row used
  per CRM x element, and each control chart shows it in its footer.
- **R2** A CRM without a certified value for an element is shown as "not
  certified for this element -- not evaluated": no rating, no finding (1.1
  rated its repeatability; rule `crm_rate_uncertified` restores that).
- **R3** Values written with a unit (`>5%`, `> 5 %`, `>10000 ppm`) are parsed,
  converted to the column unit and flagged over-limit (before: missing, C04).
  New finding "Over-limit results requiring ore-grade re-assay" (Important)
  lists the samples.
- **R4** New rule **C19**: spreadsheet error strings (`#N/A`, `#VALUE!`,
  `#REF!`, `#DIV/0!`, `#NAME?`, `#NUM!`, `#NULL!`) are a data-management
  finding (Important), no longer laboratory codes.
- A CRM certified below 10 x QC DL is monitoring only (rule `crm_min_kdl`).

### Duplicates: exclusion review (R5, R14, R24)
- C16 no longer excludes pairs; it marks **mispair candidates**: the multi-
  element vote, plus a single-element vote for pulp and coarse pairs of
  low-nugget elements (Cu, Mo, Pb, Zn, Fe, S; never Au, never field pairs).
- Two triggers per element and class -- **low-grade** (pair mean below k x
  QC DL, default 10) and **outlier** (HARD at or above 50 % for Cu/Mo pulp and
  coarse, 67 % for field and for Au, or a C16 candidate) -- each with an
  action: exclude, keep or ask. Defaults: low-grade exclude; Cu/Mo outliers
  ask (pre-set exclude); Au outliers ask (pre-set keep).
- A **review window** opens before the results whenever a pair awaits a
  decision. Every excluded outlier needs a reason; decisions are saved in the
  session by pair ID and re-applied on every run.
- Every duplicate statistic and Thompson-Howarth is computed twice: all
  pairs, and after the review. The verdict, the error-source diagnosis and
  the error budget use the reviewed set. An exclusion marked "suspected, not
  verified" makes the precision verdict provisional.
- New report section "Data excluded from the precision statistics".

### Severity, decisions and ranges
- **B** Spec rule violations set the severity directly: CRM failure (1-3s;
  2-2s on one CRM or on two CRMs of one batch) and any blank failure are
  Critical with their re-assay range; cumulative CRM bias above 10 % is
  Critical, 5-10 % Important, and is rated only from 10 results.
- **R6** Drift needs 10 results per CRM or 15 pooled and is never Critical; a
  two-segment step-shift test reports "step shift after result k" with the
  bias before and after; finding texts name the Westgard pattern.
- **R7** The error budget needs 30 pairs per class; a negative variance
  difference is "not estimable", never 0 %.
- **R8** Re-assay ranges stay inside the failed batch, list the sample IDs,
  are bracketed by the last and next passing control, and name the remedy
  (pulp re-assay; coarse-blank failure: re-preparation from the coarse
  reject). A missing batch column is reported.
- **C** The report leads with a **batch decision** per element (accepted /
  accepted with conditions / rejected + re-assay range / not assessable) from
  the spec rules, kept apart from the cumulative data-adequacy statement.
- The weighted overall score is removed from the cover, the dashboard and the
  text; the per-method ratings are in an appendix, labelled diagnostic.
- **R9** Limits print as entered (7.5, not 8).
- **D** Every finding carries a root cause (data management, laboratory,
  sampling, programme design). New CSV exports: exclusion review, mispair
  candidates, orphan duplicates with suggested parents (edit distance <= 2,
  suggestions only), over-limit samples, spreadsheet errors, certificates
  used, re-assay list by sample.
- Demo: Ag CRMs raised above 10 x DL.

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
- Persian numbers: the Arabic thousands separator (٬) is no longer read as a
  decimal comma (a silent x1000 error), the Iranian slash decimal (۰/۱۲۳) and the
  Unicode minus are read; Excel "Unicode Text" (UTF-16) files are read.
- Very small and very large numbers are printed in plain Persian digits; an
  exponent such as 5.0e-04 broke apart in right-to-left text.
- New rules: minimum blanks before contamination is judged (fewer give only a
  minor warning), and the link between a blank and the sample before it, which
  stops a laboratory carry-over from being blamed on the blank material.
- Cleaning is linear in the size of the project (100 000 samples took about an
  hour); the analysis runs behind a progress window instead of freezing it.
- A control character in a data cell no longer stops the Word report; a Latin
  name with parentheses ("Sungun Cu (Phase 2)") keeps its order on the cover;
  verdict cards are no longer stretched.

### Added after release
- Duplicate pairs whose mean is below 10 x the detection limit are left out of
  the precision statistics, and check-laboratory pairs likewise (rules
  `dup_min_kdl` and `ump_min_kdl`, 0 = off). Thompson-Howarth keeps every
  pair. The cut needs a real detection limit (declared, or read from '<'
  results); the report states how many pairs were left out.

### Compatibility
- With every cleaning rule and the 10 x DL pair rules switched off, results
  equal GEOQAQC 1.1 on the 1.1 sample data (checked by an automated test).
- 1.1 session files still load.

## 1.1
- Fixed the empty-cell crash of the detection-limit flag and short duplicate
  codes; grouping by hole, batch, drill type and laboratory; Q-Q plots;
  check/umpire module.
