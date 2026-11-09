**GEOVALID PRO 0.3.0, Windows x64 (portable, offline).** Drillhole database validation — v2 upgrade, Phase 1.

Unzip the archive, then run `GEOVALID\GEOVALID.exe`. No installation is needed. The quick-start guide (Persian/English) is `README_RUN.md`; the changes are in `CHANGELOG.md`. Screenshots of this exact build are in `screenshots/`.

New in 0.3.0:
- Survey QA pack: missing 0 m stations, collar vs first station, neighbour-inconsistent stations, near-vertical suppression, north reference and magnetic interference, desurvey sensitivity (tangential, balanced tangential, minimum curvature).
- Hole-ID normalisation across tables with an approval-based ID mapping table; closest-collar suggestions for orphans.
- Completeness and value checks: missing-value ambiguity, CRS plausibility, dummy coordinates, drill-type codes, duplicate and missing sample numbers (QC-aware), below-detection coding by batch, detection limits, labs and methods, stoichiometric caps, downhole spikes, repeated values, code dictionaries.
- Editable severities, enabled rules and thresholds; JSON rule profiles with a profile hash.
- Data Verification Evidence Pack (HTML + JSON) by JORC, NI 43-101, S-K 1300 and CIM clauses; issues as JSON; per-hole fingerprints.
- Approved fixes write corrected copies and a fix log; source files are never modified.
- New app pages: Survey QA, Values, Rules & profiles, Evidence pack; Issue Browser with source-row viewer and export.

90 validation rules. This build was produced by GitHub Actions on Windows. Before publishing, its unit tests, injected-error recall tests, and CLI and GUI smoke tests all passed.

This is a decision-support tool. Final acceptance of data for public reporting rests with the Competent/Qualified Person.
