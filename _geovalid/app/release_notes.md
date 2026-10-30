**GEOVALID PRO 0.2.0, Windows x64 (portable, offline).** Exploration drillhole database validation and grade analysis.

Unzip the archive, then run `GEOVALID\GEOVALID.exe`. No installation is needed. The quick-start guide (Persian/English) is `README_RUN.md`. To try the program, click **Sample data**, then **Run validation**. Screenshots of this exact build are in `screenshots/`.

New in 0.2.0:
- Redesigned desktop app: dark Obsidian & Gold theme with a light Ivory alternative, sidebar navigation, KPI dashboard, interactive charts.
- Grade versus logged geology: η² and Kruskal–Wallis association between grade and lithology, alteration, weathering and any coded logging column; grade by unit, two-way median grade, Cramér's V, contact analysis (hard/soft boundaries), suggested estimation domains (CRS-004, CRS-005).
- New charts: swath plots, grade × thickness map, grade–length curve, units with depth, downhole strip log, density/RQD by unit, scatter by unit; all charts restyled with a consistent palette and Persian labels.
- Premium HTML report layout with a new section on grade versus geology, and `grade_vs_geology.xlsx`.
- ASY-004 now also detects unit mix-ups by batch or hole.

76 validation rules from the approved catalogue. Source files are never modified.

This build was produced by GitHub Actions on Windows. Before publishing, its unit tests, injected-error recall tests, and CLI and GUI smoke tests all passed.

This is a decision-support tool. Final acceptance of data for public reporting rests with the Competent/Qualified Person.
