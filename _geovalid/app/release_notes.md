**GEOVALID PRO 1.0.0, Windows x64 (portable, offline).** Drillhole database validation — v2 upgrade complete (Phases 1–3).

Unzip the archive, then run `GEOVALID\GEOVALID.exe`. No installation is needed. The quick-start guide (Persian/English) is `README_RUN.md`; the changes are in `CHANGELOG.md`. Screenshots of this exact build are in `screenshots/`.

New in 1.0.0:
- Project files: save and reopen the whole set-up (tables, mappings, optional inputs, profile, output); profiles also carry column mappings and the hole-ID merge table.
- Headless batch runs: `GEOVALID.exe --cli --project project.json --out folder`, exit codes 0/1/2/3, and a log file for every run.
- Spatial checks: hole clash by exact 3-D segment distance; twin candidates and twin comparison (paired statistics, QQ); drilling-method bias (RC vs DD and others) from paired composites.
- Optional anomaly assist (off by default, suggestions only): code-mapping suggestions and an explainable multi-element anomaly score.
- New app page: Spatial (clash, twins, bias).

113 validation rules. This build was produced by GitHub Actions on Windows. Before publishing, its unit tests, injected-error recall tests, and CLI and GUI smoke tests all passed.

This is a decision-support tool. Final acceptance of data for public reporting rests with the Competent/Qualified Person.
