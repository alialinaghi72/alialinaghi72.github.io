# GEOVALID PRO — 05 · Traceability Matrix
### ماتریس ردیابی الزامات (Requirements Traceability)

| | |
|---|---|
| Document | `05_traceability.md`, design package index and traceability record (brief §18) |
| Status | **DRAFT v0.1 for client approval.** No code is written until the design package (01–05) is approved. |
| Date | 2026-10-22 |
| Summary | Maps every requirement of the brief (`00_requirements_brief.md`, §0–§19) to the design section that satisfies it and to its delivery phase. Lists the deviations from the brief with their justification, assigns every catalogue rule to a phase, consolidates all open client decisions, and states what the design review did and did not cover. |

Document keys: **01** = `01_architecture.md`, **02** = `02_data_schema.md`, **03** = `03_rule_catalogue.md`, **04** = `04_phase_plan.md`. "P0"–"P5" are the phases of 04 §2. A requirement is **covered** when a design section specifies it precisely enough to implement and test; every row below is covered unless marked otherwise.

---

## 1. Requirement → design → phase

### §0–§1 Mission, technology, architecture

| Brief | Requirement | Design coverage | Phase |
|---|---|---|---|
| §0 | Standalone, offline desktop application | 01 A1, §1.2, §13.1 (offline enforced and tested) | P0–P5 |
| §0.1 | Ingest and auto-map any format, naming, units | 01 §2.1 `io/`, `mapping/`; 02 §5.2–§5.3, §6; 03 IMP family | P1 (tabular, vector), P2 (assay headers), P3 (DEM) |
| §0.2 | Configurable rule engine reproducing mainstream package checks plus extended checks | 01 §5; 03 (229 rules, `Mirrors` column) | P1–P4 |
| §0.3 | Statistical, geological and cross-table analysis | 01 §6.7–§6.8; 03 CRS, SPA, statistical rules (§1.9) | P2–P4 |
| §0.4 | Confidence score per hole, table, project; JORC/NI mapping | 01 §8; 02 §4.22 `drv_confidence`; 03 JORC/NI column | P4 |
| §0.5 | Figures, tables, DOCX/PDF/HTML report, error log, cleaned versioned DB, software exports | 01 §9, §9.9; 02 §9; 04 §2.0 | P1 (HTML, XLSX, exports), P4 (DOCX, PDF, full report) |
| §0 | Never change data silently; propose, review, accept/reject with reason, audit | 01 §7.8; 02 §1, §5.6–§5.8; 03 §1.7 | P1 |
| §1.1 | Python 3.11+, offline, Windows executable + CLI | 01 §3.1, A15, §14; 04 §4.1 (3.12 target, 3.11 supported) | P1 (packaging from P1) |
| §1.1 | PySide6 GUI with dockable panels, embedded plots, 2D map/section, optional 3D | 01 §10; A13 (pyqtgraph); D-f (3D in P5) | P3–P5 |
| §1.1 | pandas, numpy, scipy, statsmodels, scikit-learn, pyarrow; Parquet/SQLite project | 01 §3.1, A2–A3, §4.1 | P0–P1 |
| §1.1 | Spatial libraries (pyproj, shapely, geopandas, rasterio, fiona, …) | 01 §3.1, §3.3 (**pyogrio replaces fiona; ezdxf for DXF**, deviation 4.2) | P1, P3 |
| §1.1 | matplotlib, plotly (offline), mplstereonet | 01 §3.1, §3.8 | P2–P4 |
| §1.1 | python-docx, WeasyPrint or ReportLab, Jinja2 | 01 §3.2 (**Qt WebEngine PDF**, deviation 4.1), §9.6–§9.8 | P0 spikes S-01–S-03; P4 |
| §1.1 | Persian/RTL in figures (arabic_reshaper, python-bidi, Vazirmatn; Inter/Source Sans) | 01 A9–A10, §3.8, §10.10 | P0 spike; P1 onward |
| §1.2 | Module architecture | 01 §2.1–§2.2 (refined to module level) | P0 |
| §1.3 | Rule object fields (ID, table, titles fa/en, description, severity, parameters, reference, auto_fix, jorc_section) | 01 §5.2; 03 §1, §2 columns | P1 |
| §1.3 | Unified issue table with the listed fields | 02 §5.5 (+ `fingerprint`, `run_id`); 01 §5.3, §5.8 | P1 |
| §1.3 | YAML validation profiles; deposit-type presets | 01 §5.9; 03 §4 (nine profiles + variants) | P1 (mechanism), P2–P4 (profiles, 04 D-i) |

### §2 Data input

| Brief | Requirement | Design coverage | Phase |
|---|---|---|---|
| §2.1 | CSV/TXT (delimiter detection), XLSX/XLS, DBF, MDB/ACCDB, SQLite, SQL Server/PostgreSQL | 01 §3.5 (Access tiered reader), §3.9; 04 D-e | P1 |
| §2.1 | Datamine `.dm`, Micromine `.DAT`, Surpac `.str`, Leapfrog/acQuire/MX exports | 01 §3.6 (`.dm`, `.DAT` as **time-boxed spikes**, deviation 4.3); 04 §1.8 | P2–P3 |
| §2.1 | Encoding detection (UTF-8/16, cp1256), Persian digits, decimal comma, thousands, hidden characters, Excel serials, merged headers | 02 §6.1–§6.3 (N01–N17); 03 IMP-002–IMP-007, IMP-014 (Jalali) | P1 |
| §2.2 | Fuzzy header mapping incl. Persian headers; user confirms; mapping saved | 02 §4 synonym columns, §5.2; 03 IMP-009, IMP-010 | P1 |
| §2.2 | Table-type detection | 02 §5.1; 03 IMP-008, IMP-017 | P1 |
| §2.2 | Depth units, coordinate format, swapped X/Y, lat/long in UTM fields, UTM zones 38–41, EPSG | 02 §6.4–§6.5; 03 IMP-011, IMP-012, IMP-013, COL-006 | P1 |
| §2.3 | DEM in all listed formats; TIN/grid from contours/points with interpolation error; source, resolution, datum | 01 §6.8; 02 §4.21; 03 COL-025 | P3 |
| §2.3 | Geological map (vector; raster with colour classifier fallback) | 02 §4.21 `geomap_unit`; 01 §6.8 | P2 (vector); raster colour classifier P4 (04 WP4.10; scope lever L6 may defer it to v1.1) |
| §2.3 | Licence boundary (SHP, KML, DXF, coordinate list) | 02 §4.21 `licence`; 03 COL-005, SPA-004 | P1 |
| §2.3 | Optional geophysical grids; trench and surface samples | 02 §4.21 `GEOPHYS_GRID`, `SURFACE_SAMPLES`; 03 SUR-013 correlation, SUR-026, LIT-009 | P3 |

### §3 Collar

| Brief | Requirement | Design coverage | Phase |
|---|---|---|---|
| §3.1 | Duplicate IDs; ID format; missing/zero coordinates; collars without survey/intervals; orphan IDs | 03 COL-001–COL-003, COL-008, COL-009, SUR-001, INT-006 | P1 |
| §3.1 | Near-duplicate coordinates: twins, re-drills, wedges, true duplicates | 03 COL-004, COL-021, SUR-025, CRS-010 | P1 (CRS-010: P4) |
| §3.1 | Outside licence or extent; X/Y/Z outliers | 03 COL-005, COL-016 | P1 |
| §3.1 | EOH vs maximum depths (Leapfrog "Collar Max Depth") | 03 COL-007, COL-022 | P1 |
| §3.1 | Dates, drilling rate per rig | 03 COL-014, SMP-008 | P1 (SMP-008: P2) |
| §3.1 | Hole type, rig, contractor, diameter, method; method mixing | 03 COL-017, COL-018 | P1 |
| §3.2 | Collar survey-method inference (eight evidence lines), class + confidence + evidence; map; recommendation | 01 §6.10 (weights of evidence, A11); 02 §4.22 `drv_collar_method`; 03 COL-010, COL-013, COL-020, COL-023 | P3 (COL-013, COL-020, COL-023 in P1) |
| §3.3 | ΔZ against DEM, statistics, plots, thresholds by method, systematic bias, clusters, DEM age, proposed fixes | 03 COL-011, COL-012, COL-024, COL-026; 02 §4.22 `drv_collar_spatial`; 01 §9.3 figures | P3 |
| §3.3 | Traces exiting above topography | 03 SUR-016 (topography branch) | P3 |
| §3.4 | Nearest-neighbour spacing; spacing at depth (pierce points); density; Clark–Evans, Ripley K/L, grid orientation; declustering preview | 01 §6.8; 02 `drv_pierce_point`; 03 COL-015, COL-027 | P3 |
| §3.4 | Twin and close-pair inventory | 03 COL-004 → CRS-006 | P3 (inventory), P4 (comparison) |
| §3.4 | Spacing vs classification guidance (indicative); drilling orientation vs structure | 03 COL-027, §4; SPA-005, STR-006 | P3 (COL-027), P4 (SPA-005) |

### §4 Downhole survey

| Brief | Requirement | Design coverage | Phase |
|---|---|---|---|
| §4.1 | Orphans, duplicates, non-increasing and negative depths, range checks, 0/360 | 03 SUR-001–SUR-004, SUR-017, SUR-020 | P1 |
| §4.1 | Dip sign convention, up-holes | 03 SUR-005; 02 §6.4 | P1 |
| §4.1 | Survey beyond EOH; first station too deep; spacing too large | 03 SUR-006–SUR-008 | P1 |
| §4.1 | Design-only (unsurveyed) holes | 03 SUR-009, COL-019 | P1 |
| §4.1 | Instrument and survey type completeness | 03 SUR-018, SUR-029 | P1 (SUR-029: P3) |
| §4.2 | Dogleg severity; large dip/azimuth change with near-vertical suppression | 03 SUR-010–SUR-012; 02 §4.22 (minimum curvature, DLS) | P1 |
| §4.2 | Azimuth spikes and magnetic interference correlation | 03 SUR-013, SUR-027 | P1 (pattern), P3 (correlation evidence) |
| §4.2 | Declination, grid convergence, azimuth reference | 01 §3.7, §6.4; 03 SUR-014 | P1 |
| §4.2 | Lift and drift by group | 03 SUR-019 | P3 |
| §4.2 | Desurvey methods compared | 01 §6.3; 03 SUR-015 | P1 |
| §4.2 | Crossing traces | 03 SUR-016 | P1 |
| §4.2 | Survey plots (dip/azimuth vs depth, drift, rose, stereonet, plan/section with design) | 01 §9.3, §10.5 | P3 |

### §5 Generic interval checks

| Brief | Requirement | Design coverage | Phase |
|---|---|---|---|
| §5 | Missing/non-numeric keys; From ≥ To; zero length; negative | 03 INT-001, INT-010 | P1 |
| §5 | Overlaps, duplicates and conflicts, gaps (top, internal, bottom), beyond EOH | 03 INT-002–INT-005 | P1 |
| §5 | Coverage per hole and table; completeness heat map | 03 INT-011; 02 `drv_hole_summary`; 01 §9.3 | P1 |
| §5 | Interval length distribution, short/long, precision artefacts | 03 INT-007, INT-012 | P1 |
| §5 | Unmerged identical records; mandatory fields; controlled vocabulary | 03 INT-013–INT-016, LIT-002 | P1 |
| §5 | Samples crossing geological contacts | 03 INT-008 | P1 (on `ext_` tables), P2 (promoted families) |
| §5 | Copy-paste repetition | 03 INT-009 | P1 |

### §6 Assays and QA/QC

| Brief | Requirement | Design coverage | Phase |
|---|---|---|---|
| §6.1 | Element, oxide, unit, method, repeat-column parsing; units in a separate row | 02 §4.8–§4.9; 03 ASY-001, IMP-008 | P2 |
| §6.1 | Unit inference shown with evidence and confirmed | 01 §6.9; 03 ASY-001, IMP-016 | P2 |
| §6.1 | Canonical units, originals kept | 02 §2, §4.9 | P2 |
| §6.1 | Multiple methods per element; preferred-value rule | 02 §4.9.3; 03 ASY-009, ASY-019 | P2 |
| §6.2 | Text codes and placeholders, BDL policy | 03 ASY-002; 02 §4.9.1–§4.9.2 | P2 |
| §6.2 | DL per element, lab, batch, period; % below DL; values at DL; over-range | 03 ASY-005, ASY-010–ASY-012, ASY-023 | P2 |
| §6.2 | Impossible values; mixed units; precision; zero vs null | 03 ASY-003, ASY-004, ASY-013, ASY-014 | P2 |
| §6.2 | Stoichiometric checks (Cu–S, Fe–Fe₂O₃/FeO, oxide total, partial ≤ total, ratios); user inequalities | 03 ASY-006, ASY-015, ASY-016; `ASY-901…` (§1.2) | P2 |
| §6.2 | Missing assays in mineralised zones | 03 ASY-008, SMP-005 | P2 |
| §6.3 | Summary statistics (weighted and unweighted) | 01 §6.7; 04 §2.3 | P2 |
| §6.3 | Histograms, log-probability, box plots, ECDF by group | 01 §9.3 | P2 |
| §6.3 | Outliers and top-cut analysis (suggestion only) | 03 ASY-007, SPA-001 | P2 (statistical), P4 (spatial) |
| §6.3 | Correlations (Pearson log, Spearman, CLR), heat map, PCA | 01 §6.7 | P2 |
| §6.3 | Downhole grade strip plots | 01 §9.3, §10.5 | P2 (report), P3 (GUI) |
| §6.4 | Insertion rates; no QA/QC → CRITICAL | 03 QAQ-001 | P2 |
| §6.4 | CRM control charts, bias, Westgard, mislabelled CRM | 03 QAQ-002, QAQ-005, QAQ-006, QAQ-008, QAQ-009, QAQ-011 | P3 |
| §6.4 | Blanks: threshold, carry-over, time series | 03 QAQ-003 | P3 |
| §6.4 | Duplicates: HARD, ranked HARD, MPD, RMA, Q-Q, Thompson–Howarth | 03 QAQ-004, QAQ-016, QAQ-017; 03 §1.10 definitions | P3 |
| §6.4 | Umpire checks | 03 QAQ-007 | P3 |
| §6.4 | Batch pass/fail and re-assay list | 03 QAQ-018, QAQ-019 | P3 |

### §7–§10 Logging and other tables

| Brief | Requirement | Design coverage | Phase |
|---|---|---|---|
| §7 | Code inventory, synonyms, harmonised dictionary, legend | 03 LIT-001; 02 §4.20 | P2 |
| §7 | Diversity metrics; thickness; thin and unmerged | 03 LIT-002, LIT-006 | P2 |
| §7 | Sequence logic, Markov transitions, forbidden sequences | 03 LIT-003, LIT-008; `LIT-901…` | P2 |
| §7 | Logger effect | 03 LIT-005, INT-019 | P2 |
| §7 | Cross-hole consistency at similar elevation | 03 LIT-007 | P4 |
| §7 | Strip logs and fence diagrams | 01 §9.3, §10.5 | P2 (report), P3–P4 (GUI) |
| §7.1 | First logged unit vs map; correlation table; cover handling; near-contact buffer; κ, confusion matrix; surface samples | 03 LIT-004, LIT-009; 02 `map_unit_lith_corr` | P2 |
| §8 | CR/RQD ranges; RQD ≤ CR; recomputation; fracture frequency | 03 GEO-001–GEO-003, GEO-008 | P2 |
| §8 | Run length vs barrel; overlaps and gaps | 03 GEO-005, INT-002, INT-004 | P2 |
| §8 | Recovery–grade relationship; RC sample weights; wet/dry | 03 GEO-004, GEO-006, GEO-007, ASY-026 | P2 |
| §8 | CR/RQD by group; correlation matrix; strip plots | 01 §6.7, §9.3 | P2 |
| §9 | Alteration codes, intensity scales, missing intensity, primary/secondary, zoning | 03 ALT-001, ALT-003–ALT-005 | P2 |
| §9 | Alteration vs lithology contingency (χ², Cramér's V, mosaic) | 01 §6.7 (analysis output, no rule) | P2 |
| §9 | Logging vs geochemistry (AI, CCPI, molar ratios; sulphide vs S; magnetite vs Fe/MS; oxidation vs CuAS/S; quartz vs SiO₂) | 03 ALT-002, MIN-003, MAG-003, WTH-003 | P2 (MAG-003: P3) |
| §9 | Mineralisation codes and abundances | 03 MIN-001, MIN-002, MIN-004–MIN-007 | P2 |
| §9 | Weathering order; base of oxidation per hole; neighbour inconsistency | 03 WTH-001, WTH-002, WTH-004, WTH-005 | P2 (WTH-004: P4) |
| §10 | Density: range per lithology, method, vs grade, coverage, regression | 03 DEN-001–DEN-007 | P2 |
| §10 | Magnetic susceptibility: units, range, vs magnetite and Fe | 03 MAG-001–MAG-004 | P3 |
| §10 | Structure: ranges, true orientation via survey, stereonets, oriented-core flags | 03 STR-001–STR-006; 02 §4.18 | P3 |
| §10 | Sample table: uniqueness, sequence gaps, weights, dispatch/batch linkage, chain of custody | 03 SMP-001–SMP-011; 02 §4.6 | P2 |
| §10 | Unknown tables: generic checks and profiling | 02 §4.19 (`ext_`); 03 INT family | P1 |

### §11–§13 Integration, versions, confidence

| Brief | Requirement | Design coverage | Phase |
|---|---|---|---|
| §11 | Desurveyed interval master table with XYZ midpoints | 01 §6.5; 02 `drv_interval_master` | P2 (04 P5) |
| §11 | High grade in barren units and the inverse; zone continuity | 03 CRS-001, CRS-003 | P4 |
| §11 | Grade by lithology × alteration; ANOVA/Kruskal–Wallis; domain suggestion | 03 CRS-004 | P4 |
| §11 | Contact analysis (hard/soft) | 03 CRS-005 | P4 |
| §11 | Grade maps, local Moran's I, Getis–Ord, NN grade difference | 03 SPA-001, SPA-002; 01 §6.8 | P4 |
| §11 | Twin-hole comparison; drilling-method bias | 03 CRS-006, CRS-002, CRS-007 | P4 |
| §11 | Swath plots; variogram preview; compositing preview and length recommendation | 01 §6.6, §6.8, §9.3; 03 CRS-009 | P4 |
| §12 | Version diff: holes, coordinates, surveys, intervals, values, renamed codes; diff report and change map | 01 §6.11; 02 §9; 03 VER-001–VER-008 | P4 |
| §13 | Score 0–100 per hole and table; project index; traffic light | 01 §8.1–§8.2; 02 `drv_confidence` | P4 |
| §13 | JORC Table 1 Section 1 and NI 43-101 Items 11–12 mapping | 01 §8.3–§8.4; 03 §1.8 | P4 |
| §13 | Indicative fit-for-purpose statement with CP/QP disclaimer | 01 §8.5 | P4 |

### §14–§16 Outputs, style, UI

| Brief | Requirement | Design coverage | Phase |
|---|---|---|---|
| §14.1 | Issue log (XLSX + CSV) with pivot sheets | 01 §9.9 | P1 |
| §14.2 | Cleaned, versioned database with `QC_FLAG`, `QC_COMMENT`, audit trail | 01 §7; 02 §5.7–§5.8, §9 | P1 |
| §14.3 | Exports for Leapfrog, Datamine, Micromine, Surpac, Vulcan, generic CSV; GIS layers | 01 §2.1 `io/writers`; 03 IMP-018 | P1 (Leapfrog, generic CSV, GIS), P3–P4 (others) |
| §14.4 | Figures as PNG 300 dpi + SVG, numbering and captions fa/en | 01 §9.3 | P1 onward |
| §14.5 | DOCX + PDF + interactive HTML; fa / en / bilingual; A4; branding placeholder | 01 §9.5–§9.8 (A19 bilingual mode); 04 D-c, D-g | P1 (HTML), P4 (DOCX, PDF) |
| §14.6 | YAML profile and run metadata (version, hashes, parameters, date) | 01 §5.9, §9.10; 02 §5.9 | P1 |
| §14.1 (report) | Thirteen-chapter structure, appendices, interpretive narrative, no placeholders | 01 §9.2, §9.4 (phrasebook engine, A14), §9.10 (lint); 04 §2.0 | P1–P4 |
| §15 | Style guide: palettes, shared legends, map furniture, log axes, fonts, tables, A4 sizes | 01 §9.3; 01 §3.8 | P1 onward |
| §16 | Wizard steps; dashboard; review panel with context; bulk actions with mandatory reason | 01 §10.2–§10.4 (non-modal stepper, A21) | P3–P5 |
| §16 | Map and section viewer (2D, optional 3D) | 01 §10.5; 04 D-f | P3–P5 |
| §16 | Settings (thresholds, dictionaries, language, branding) | 01 §10.9 | P3 |
| §16 | CLI `geovalid run …` | 01 §11 | P1 |
| §16 | ≥ 5 000 holes / 1 M interval rows; progress; responsive UI | 01 §12 (targets), §10.7; 04 §3.8 | P1 onward (benchmarked every phase) |

### §17–§19 Rule catalogue, QA, research

| Brief | Requirement | Design coverage | Phase |
|---|---|---|---|
| §17 | All 68 brief rules | 03 §2 (all present with original IDs and default severities; mechanically verified, §6 below) | P1–P4 (§3 below) |
| §18 | Phases 1–5 | 04 §2 (Phase 0 added; re-sequencing in 04 §1.4) | — |
| §18 | Synthetic generator with injected errors; per-rule detection and no false positives; real anonymised DB regression | 04 §3.2–§3.4, §3.9 | P0 onward |
| §18 | Type hints, docstrings, logging, no hard-coded thresholds, one file per rule | 01 A12, §5.4; 04 §4.1 | P0 |
| §18 | Present architecture, schema, catalogue, phase plan and wait for approval | 01, 02, 03, 04 (this package) | Now |
| §18 | Runnable build and short test report after each phase | 04 §4.5, §7.3 | Every phase |
| §19 | Research further checks from named software and audit practice; list as proposed additions with source | 03 §3 (84 NEW rules), Appendix B (provenance) | — |
| §19 | Every inference shows evidence and is overridable | 01 §6.9; 02 §5.3 | P1 |
| §19 | Interpretive text geologically meaningful | 01 §9.4 | P1–P4 |
| §19 | All thresholds default, editable, listed in the appendix | 01 §5.9; 03 §1.5 | P1 |
| §19 | Decision support only; CP/QP statement in the report | 01 §8.5, §9.2 | P4 |

---

## 2. Deviations from the brief

| # | Brief | Deviation | Justification | Where |
|---|---|---|---|---|
| 2.1 | §1.1 PDF via WeasyPrint or ReportLab | PDF rendered from the same Jinja2 HTML by **Qt WebEngine** `printToPdf` | WeasyPrint needs a GTK/Pango runtime that is fragile to bundle on Windows; ReportLab does not shape Persian without extra work. Chromium shapes Persian correctly, and Qt WebEngine is already part of the GUI stack. | 01 §3.2 |
| 2.2 | §1.1 fiona | **pyogrio** for vector I/O; **ezdxf** for DXF | pyogrio is faster and is the geopandas default; ezdxf reads 3D faces and polylines that the GDAL DXF driver loses | 01 §3.3 |
| 2.3 | §2.1 Datamine `.dm`, Micromine `.DAT` | **Time-boxed spikes** against client sample files; CSV exports are the supported path until a spike passes | Undocumented binary formats; promising them unconditionally would be dishonest | 01 §3.6; 04 §1.8 |
| 2.4 | §1.1 Packaging in Phase 5 | Packaging pipeline **from Phase 1** | Packaging problems (Qt WebEngine, GDAL, fonts) are cheapest to find early; each phase ships an installer | 01 A15; 04 P8 |
| 2.5 | §18 phase contents | Phase 0 added; desurvey, declination and vector GIS moved to P1; interval master and sample register to P2 | Phase-1 rules need traces; QA/QC needs the sample register (04 §1.4) | 04 §1.4 |
| 2.6 | §16 wizard | **Non-modal stepper** with linked views | A modal wizard blocks the review/fix/re-run loop the brief describes | 01 §10.2 |
| 2.7 | §1.1 Source Sans | **Inter** chosen as the Latin font | One OFL font with matching metrics in all outputs | 01 A10 |
| 2.8 | §14.1 interpretive narrative | Deterministic **phrasebook engine**, no language model | The tool must be fully offline and reproducible | 01 A14, §9.4 |
| 2.9 | §1.1 GUI charts | Qt Charts and Qt Data Visualization **not used** | GPL-only modules would force the licence | 01 A13 |
| 2.10 | §17 ALT-002 | The umbrella "logging contradicts geochemistry" is split: ALT-002 (alteration), MIN-003 (sulphide vs S), MAG-003 (magnetite vs MS/Fe), WTH-003 (oxidation vs CuAS/S) | Each finding lands in the family a reviewer would look in; meaning of ALT-002 is unchanged | 03 §2.9 |
| 2.11 | §6.2 and §7 user-defined rules | Implemented as declarative `FAM-901…999` rules, not catalogue entries | A mechanism, not a check (03 §1.2) | 01 §5.11 |
| 2.12 | §13 JORC Section 1 only | Proposed secondary tags `S3.DI` and `S3.BD` (Section 3 database integrity and bulk density) | Without them the most-cited Section 3 evidence would be untagged; client decision | 03 §1.8 |
| 2.13 | §17 DEN-001 (WARNING) | Default WARNING kept; **escalates to ERROR** outside absolute physical bounds | A density no rock can have is a unit or keying error | 03 §2.12 |
| 2.14 | §13 confidence index | **No confidence index before Phase 4** | A score without location, QA/QC and recovery components would overstate confidence | 04 P9 |


---

## 3. Delivery phase of every catalogue rule

04 §1.6 assigns the 68 brief rules to phases and leaves the catalogue additions to "the phase in which their inputs exist". This table makes that assignment explicit for all rules, using the same input logic (traces and vector GIS in P1; assays, sample register, logging tables and interval master in P2; DEM, QA/QC analytics, magnetic susceptibility and structure in P3; cross-table, spatial and version work in P4). It is a proposal for confirmation at the P0 gate (04 D-j).

| Family | P1 | P2 | P3 | P4 |
|---|---|---|---|---|
| IMP | IMP-001–020 (20) | — | — | — |
| COL | COL-001–009, COL-013–014, COL-016–023 (19) | — | COL-010–012, COL-015, COL-024–027 (8) | — |
| SUR | SUR-001–018, SUR-020–021, SUR-023–026 (24) | — | SUR-019, SUR-022, SUR-027–029 (5) | — |
| INT | INT-001–016 (16) | INT-017–019 (3) | — | — |
| ASY | — | ASY-001–027 (27) | — | — |
| QAQ | — | QAQ-001 (1) | QAQ-002–022 (21) | — |
| SMP | — | SMP-001–011 (11) | — | — |
| LIT | — | LIT-001–006, LIT-008–009 (8) | — | LIT-007 (1) |
| GEO | — | GEO-001–008 (8) | — | — |
| ALT | — | ALT-001–005 (5) | — | — |
| MIN | — | MIN-001–007 (7) | — | — |
| WTH | — | WTH-001–003, WTH-005 (4) | — | WTH-004 (1) |
| DEN | — | DEN-001–007 (7) | — | — |
| MAG | — | — | MAG-001–004 (4) | — |
| STR | — | — | STR-001–006 (6) | — |
| CRS | — | — | — | CRS-001–010 (10) |
| SPA | — | — | — | SPA-001–005 (5) |
| VER | — | — | — | VER-001–008 (8) |
| **Rules per phase** | **79** | **81** | **44** | **25** |

Total 229 rules. Split rules (one rule, branches delivered in two phases): SUR-013 (pattern P1; magnetic-correlation evidence P3); SUR-016 (crossing P1; topography exit P3); ASY-007 (statistical P2; spatial branch P4); IMP-016 (analyte-unit kinds active from P2); COL-016 (z-vs-DEM evidence from P3); INT-008 (on ext_ tables P1; promoted families P2).

---

## 4. Open decisions for the client (consolidated)

Sources: 04 §6 (D-a…D-r), 01 §16 (Q1–Q13), 02 §10 (Q1–Q10), 03 Appendix E (E1–E13). Each item is listed once, at the latest point it can be decided. The detail stays in the source section.

| When | Decision | Source | Default if unanswered |
|---|---|---|---|
| **Before Phase 0 (blocking)** | Approve this design package (01–05), or request changes | brief §18 | — (blocking) |
| | Repository location: a dedicated private repository instead of the public website repository | 04 D-a | — (blocking) |
| | Software licence | 04 D-b | Proprietary |
| | Approve the IMP, COL, SUR and INT additions (rolling approval of the 84 NEW rules) | 04 D-j; 03 §3, E1 | Must-tagged rules included |
| | Gate-review SLA and named acceptor; Persian-language reviewer | 04 D-n, D-l | A.A, 10 working days |
| **Before Phase 1** | Real anonymised databases with known-issue registers; proprietary-format priority and samples | 04 D-d, D-e; 01 Q4, Q13 | Synthetic data only; CSV exports |
| | Target hardware | 04 D-h; 01 Q2 | Reference laptop of 01 §12.1 |
| | Schema questions: canonical concentration units, calendar, vertical datum, legacy CRS, embedding limit, hole-ID joins, trenches | 02 Q1–Q4, Q7, Q8, Q10 (04 D-o) | 02 recommendations |
| | Deployment, encryption, licence protection | 01 Q5, Q7, Q10 (04 D-r) | Per-user install; BitLocker; none |
| | Secondary JORC tags `S3.DI`, `S3.BD` | 03 §1.8, E2 | Not used |
| | Software versions in use, for export ID limits | 03 IMP-018, E9 | Generic CSV limits only |
| | Iranian specifics: licence elevation limits, Jalali dates in fa outputs | 03 E11; 02 Q2 | No elevation limit; Jalali in fa |
| **Before Phase 2** | Lab-internal QC types, alteration intensity scale, weathering scheme | 02 Q5, Q6, Q9 | 02 recommendations |
| | First deposit-type profiles; indicative cut-offs and spacing guides | 04 D-i; 03 §4, E4 | Porphyry Cu and epithermal Au; §4 placeholders |
| | Alteration expectations for non-porphyry deposits | 03 E8 | ALT-002 (a)–(b) only |
| | Which optional inputs exist (certificates, reported intercepts, QC schedule, prep QC, sampling protocol, photo index, void models) | 03 E10, Appendix C | Dependent rules `NOT_APPLICABLE` |
| | Real map and licence layers | 04 D-q | Synthetic layers |
| **Before Phase 3** | Company QA/QC protocol (insertion targets, CRM and blank rules, HARD limits) | 04 D-p; 03 E3 | 03 defaults |
| | Commodity K and α for QAQ-021; MAG-003 on or off | 03 E6, E7 | Default K with caveat; on |
| | Real DEMs | 04 D-q | Synthetic DEM |
| | Code signing identity | 04 D-k; 01 Q3 | Internal certificate |
| **Before Phase 4** | Branding assets and house template | 04 D-c; 01 Q12 | Placeholder branding |
| | Bilingual report mode, report authenticity, PDF/A, hole atlas | 01 Q1, Q6, Q9, Q11; 04 D-g | As designed in 01 §9.5; release anchor; no PDF/A; atlas on request |
| | 3D viewer in v1 | 04 D-f | Included (P5) |
| | Applicable coal guideline (if a coal project is in scope) | 03 E13 | Coal profile stays a skeleton |
| **Any time** | Commercial-software cross-check datasets (Leapfrog, Datamine) | 04 D-m | Skipped; residual risk |
| | Concurrent review by several reviewers | 01 Q8 | One writer per project |
| | Review of rules whose basis is domain knowledge | 03 E5 | Coded with the stated defaults |

---

## 5. Review status of this design package

**What was planned.** The design was produced by a multi-agent workflow:
- three research streams (03 Appendix B);
- three authors for 01, 02 and 04;
- one author for 03;
- **two independent reviewers**, one on requirement coverage and cross-document consistency, one on domain and technical correctness;
- an editor to apply their findings.

**What actually ran.** The research, 01, 02 and 04 completed. The session then hit its usage limit twice. The 03 author was stopped after the ASY family, and the two reviewers and the editor never ran. The rest of 03 (QAQ to VER, §3–§5) and this document were completed directly by the lead author, from the research results and the finished 01, 02 and 04.

**What has been verified (mechanically, 2026-10-22).**
- 03 defines **229 rules** with unique IDs, every row having all nine columns.
- **All 68 brief §17 rules** are present with their original ID and meaning, and a default severity compatible with the brief. The one adjustment is DEN-001, whose default stays WARNING with an escalation to ERROR (deviation 2.13).
- **No dangling rule references:** every rule ID cited in 01, 02, 03 and 04 resolves to a rule defined in 03 (the reserved `FAM-901…999` range excluded).
- Every NEW rule in 03 §3 has a rationale. Every research candidate has a final ID and a verification flag (03 Appendix B).
- Spot checks of 01 against this matrix (PDF engine, GIS I/O, raster classifier phase) found one phase error in a draft of this document, now corrected.

**What has not been independently reviewed.**
- The correctness of every formula and default threshold in 03, beyond the author's own checking.
- The feasibility and sizing claims of 01 §3, §12 and §14.
- The effort estimates of 04.

An independent domain review of 03 (especially the QAQ and statistical rules) and a technical review of 01 §3 are recommended before approval. They can be run as a follow-up on request.
