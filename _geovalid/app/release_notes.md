**GEOVALID PRO 0.1.0, Windows x64 (portable, offline).** Exploration drillhole database validation.

Unzip the archive, then run `GEOVALID\GEOVALID.exe`. No installation is needed. The quick-start guide (Persian/English) is `README_RUN.md`. To try the program, click **Sample data**, then **Run validation**.

- 74 validation rules from the approved catalogue: collar, survey, intervals, assays, QA/QC, lithology, geotech, density.
- Automatic mapping of English and Persian headers; Jalali dates are converted.
- Outputs: HTML report (fa/en), Excel issue log, flagged copies of every input table, desurveyed traces, run metadata. Source files are never modified.
- Command line: `geovalid-cli.exe run --files ... --out ...`

This build was produced by GitHub Actions on Windows. Before publishing, its unit tests, injected-error recall tests, and CLI and GUI smoke tests all passed.

This is a decision-support tool. Final acceptance of data for public reporting rests with the Competent/Qualified Person.
