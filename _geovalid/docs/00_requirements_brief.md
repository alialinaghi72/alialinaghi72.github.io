# MASTER PROMPT — GEOVALID PRO
## Exploration Drillhole Database Validation, Analysis & Reporting System

> Author of requirements: Ali Alinaghi (A.A) — Senior Mineral Exploration Specialist
> Intended use: paste this whole document into an AI coding agent (e.g. Claude Code) as the project brief. It can also be used to extend the existing GEOVALID v1.0 (Python, offline, collar/survey/interval checks + coverage/gap analysis).

---

## 0. ROLE AND MISSION

You are a senior software engineer **and** a senior resource geologist / database manager with deep experience in drillhole data management (acQuire, MX Deposit, Fusion), geological modelling and estimation software (Leapfrog Geo/Edge, Datamine Studio RM/EM, Micromine, Surpac, Vulcan, Deswik, Discover), geostatistics, QA/QC and public reporting codes (JORC 2012, NI 43‑101, PERC, SAMREC, CRIRSCO template).

Build a **standalone, offline, desktop application** that receives a raw exploration drillhole database (collar, survey and any number of interval/point tables, plus optional topography, geological map, licence boundary and QA/QC tables), and then:

1. **Ingests and auto-maps** the data (any common format, any field naming, any units).
2. **Validates** every table with a transparent, configurable **rule engine** that reproduces *every* check performed by the mainstream mining packages, plus the extended checks defined here.
3. **Analyses** each table statistically and geologically, and then **cross-analyses relationships** between tables (grade ↔ lithology ↔ alteration ↔ recovery/RQD ↔ density ↔ spatial position).
4. **Scores data confidence** per hole, per table and for the whole project, mapped to JORC Table 1 / NI 43‑101 Items 11–12.
5. **Produces publication-quality figures, tables, a full technical report (DOCX + PDF + interactive HTML), an error log, a cleaned & versioned database and software-ready exports.**

The program must never silently change data. Every correction is proposed, reviewed, accepted/rejected with a reason, and logged in an audit trail.

---

## 1. TECHNOLOGY AND ARCHITECTURE

### 1.1 Stack (recommended — justify any deviation)
- **Python 3.11+**, fully offline after install; packaged as a Windows executable (PyInstaller/Nuitka) + optional CLI.
- GUI: **PySide6 (Qt)** with dockable panels, embedded plots and a 2D map/section view; optional embedded 3D view (pyvista/vtk).
- Data: pandas, numpy, scipy, statsmodels, scikit-learn, pyarrow (internal storage as Parquet/SQLite project file).
- Spatial: pyproj, shapely, geopandas, rasterio, fiona, scipy.spatial (KD-tree, Delaunay, Voronoi), matplotlib.tri, laspy, ezdxf, trimesh.
- Plots: matplotlib (static, 300 dpi PNG + SVG/PDF), plotly (interactive HTML), mplstereonet (stereonets/roses).
- Reports: python-docx (DOCX), WeasyPrint or ReportLab (PDF), Jinja2 (HTML).
- Persian/RTL text in figures: `arabic_reshaper` + `python-bidi`, embedded font **Vazirmatn**; English font **Inter / Source Sans**.

### 1.2 Architecture
```
geovalid_pro/
  core/        project model, schema, units, CRS, audit log, versioning
  io/          readers/writers (tabular, DB, GIS, surfaces, software formats)
  mapping/     auto field mapping, code dictionaries, synonym tables
  rules/       rule engine + one module per table family (collar, survey, interval, assay, litho, geotech, alteration, density, qaqc, cross, spatial)
  analysis/    statistics, geochemistry, spatial statistics, desurvey, compositing
  plots/       chart factory + style guide
  report/      report builder (templates fa/en), figure/table numbering, captions
  gui/         wizard, dashboard, review/fix panel, map & section viewers
  cli/         batch / headless run
  tests/       synthetic databases with injected errors, unit + regression tests
```

### 1.3 Rule engine (mandatory design)
Every check is a **Rule** object with:
`rule_id` (e.g. `COL-012`), `table`, `title_en`, `title_fa`, `description`, `severity` (**CRITICAL / ERROR / WARNING / INFO**), `parameters` (user-editable thresholds with defaults), `reference` (which software/standard it mirrors), `auto_fix` (optional proposed fix), `jorc_section`.
Rule results → one unified **Issue table**: `issue_id, rule_id, severity, table, hole_id, from, to, field, value, expected, message_en, message_fa, suggested_fix, status (open/accepted/ignored/fixed), reviewer, reason, timestamp`.
Rules and thresholds are saved in a YAML **validation profile** (project-specific, re-usable, exportable). Profiles for deposit types (porphyry Cu, epithermal Au, VMS, iron oxide / skarn Fe, Pb‑Zn MVT/SEDEX, chromite, bauxite/laterite, industrial minerals, coal) preset sensible element lists, thresholds and expected relationships.

---

## 2. DATA INPUT

### 2.1 Tabular sources
CSV/TXT (any delimiter, auto-detected), XLSX/XLS (multi-sheet), DBF, MS Access (MDB/ACCDB via ODBC), SQLite, SQL Server/PostgreSQL (optional ODBC), Datamine `.dm` (where readable), Micromine `.DAT`, Surpac `.str`/database export, Leapfrog CSV exports, acQuire / MX Deposit exports.
- Encoding detection (UTF‑8, UTF‑16, Windows‑1256 Persian/Arabic), Persian digits (۰–۹) → Latin digits, decimal comma vs point, thousands separators, trailing spaces, hidden characters, Excel date serials, merged header rows.

### 2.2 Automatic field mapping
- Fuzzy matching of headers to the canonical schema (HoleID, X/East, Y/North, Z/RL, EOH/MaxDepth, Azimuth, Dip, Depth/At, From, To, etc.) including Persian header names; user confirms mapping; mapping saved.
- Detect the **table type** automatically from columns (collar / survey / assay / lithology / alteration / mineralisation / weathering / geotech / density / structure / magnetic susceptibility / sample / QAQC).
- Detect **depth units** (m / ft) and **coordinate format** (UTM, local grid, lat/long decimal, DMS); **swapped X/Y**; lat/long stored in UTM fields; UTM zone mismatch (e.g. zones 38–41 for Iran); request or infer EPSG.

### 2.3 Spatial inputs
- **Topography / DEM** — accept all of: GeoTIFF, ESRI ASCII grid (.asc), XYZ / CSV point clouds, LAS/LAZ, DXF (3D faces, polylines, contour lines with elevation), Surpac DTM/STR, Datamine wireframe (if readable), OBJ, STL, PLY, Leapfrog mesh exports, Shapefile/GeoPackage contours, KML/KMZ, SRTM/ALOS/ASTER tiles. Contours or points → build TIN or grid (Delaunay / natural neighbour), with resolution & interpolation error reported. Report DEM source, resolution, vertical datum.
- **Geological map** — Shapefile, GeoPackage, KML/KMZ, DXF polygons, GeoJSON; georeferenced raster maps (GeoTIFF) with a semi-automatic colour-to-unit legend classifier as fallback.
- **Licence / tenement boundary** — polygon (SHP, KML/KMZ, DXF, or coordinate list).
- Optional: geophysical grids (magnetics, IP chargeability/resistivity) for cross-checks; trench and surface sample tables.

---

## 3. COLLAR VALIDATION AND ANALYSIS (`COL-xxx`)

### 3.1 Integrity checks (mirroring Leapfrog / Datamine / Micromine / Surpac)
- Duplicate HoleIDs; HoleID case/space/format inconsistencies (`BH-01` vs `BH01` vs `bh 1`); naming convention pattern check.
- Missing / null / zero / non-numeric X, Y, Z or EOH.
- Holes in collar without survey (warning) / without any interval data (info); IDs in other tables not present in collar (error).
- Duplicate or near-duplicate collar coordinates (configurable distance, default < 1 m) → distinguish **twins, re-drills, wedges** (same collar, different survey) and **true duplicates**.
- Collars outside licence boundary / outside project extent; outliers in X/Y/Z (statistical and geometric).
- EOH inconsistencies: collar EOH vs max survey depth vs max interval depth in every table (Leapfrog "Collar Max Depth" logic) → propose fix.
- Date fields: start/end dates, illogical sequences (end before start, future dates), drilling rate (m/day) outliers per rig.
- Hole type, rig, contractor, diameter (NQ/HQ/PQ), drilling method (DD, RC, AC, RAB, percussion) completeness and consistency; mixing of methods flagged for downstream bias analysis.

### 3.2 Collar survey method inference — **Total station / DGPS / RTK vs handheld GPS vs planned vs digitised**
Infer, per collar, how the coordinates were obtained and give a **confidence score** with the evidence used:
1. **Explicit field** (survey method, instrument, surveyor) if present — checked against the evidence below.
2. **Numeric precision**: number of decimal places in X, Y, Z; proportion of integer-rounded values; trailing-zero patterns. (Total station/RTK typically 2–3 decimals; handheld GPS usually whole metres.)
3. **Terminal-digit test**: distribution of last digits (chi-square vs uniform) — rounding to 0/5 suggests manual/handheld or map-read values.
4. **Grid regularity**: collars falling exactly on round planned coordinates (e.g. multiples of 25/50/100 m) + design azimuth/dip (e.g. exactly 0/90/180/270, −60/−90) + round EOH → **planned (not as-drilled) coordinates**.
5. **Elevation behaviour**: residual against DEM (see 3.3) — RTK/total station residuals small and consistent; handheld GPS residuals large and noisy (typical vertical scatter ±10–20 m, horizontal ±3–10 m); repeated identical Z values suggest Z copied from map/DEM or a constant.
6. **Systematic vertical offset** constant across all holes → probable **datum mismatch** (ellipsoidal vs orthometric/geoid height, or different local datum) rather than random GPS error.
7. **Temporal / campaign pattern**: precision changing by drilling campaign, contractor or date.
8. **Spatial jitter**: comparison with any re-surveyed or twin collars.
Output: class (`RTK/DGPS/Total station`, `Handheld GPS`, `Planned/design`, `Digitised/map-derived`, `Unknown`), confidence %, evidence list; map of collars coloured by inferred method; summary table and recommendation (e.g. "re-survey 37 collars with DGPS before resource estimation" → JORC Table 1 "Location of data points").

### 3.3 Collar elevation vs topography
- Sample DEM/TIN at each collar (bilinear / TIN interpolation); compute **ΔZ = Z_collar − Z_topo**.
- Statistics (n, mean, median, SD, MAD, min, max, percentiles), **histogram + KDE**, box plot by campaign/method/hole type, Q-Q plot, **map of ΔZ** (diverging colour scale), ΔZ vs Z_topo scatter (slope-dependent error), ΔZ vs local slope (steep terrain amplifies horizontal error).
- Flag collars with |ΔZ| > threshold (defaults: WARNING > 2 m, ERROR > 5 m; tunable per inferred method).
- Detect: collars floating above/buried below surface, systematic bias (datum), local clusters (DEM artefacts), DEM older than mining/earthworks (pads, trenches, pits).
- Proposed fixes (never automatic): drape to topo, apply constant datum shift, or keep and flag; record decision.
- Also check **drillhole traces exiting above topography** after desurvey.

### 3.4 Drill spacing, distribution and density
- Nearest-neighbour distance (1st, 2nd, 3rd NN) per collar: histogram, cumulative curve, stats, map.
- **Effective spacing at depth**: also compute spacing using 3D **pierce points** at a user-chosen elevation/level or on a mineralised-zone midpoint (collar spacing alone is misleading for inclined holes).
- **Density**: kernel density heatmap, holes/km², metres drilled/km², Voronoi (Thiessen) polygon areas, quadrat counts.
- **Pattern analysis**: Clark–Evans index (clustered / random / regular), Ripley's K/L function, dominant grid spacing and orientation (from NN vectors / FFT), identification of drill fences/sections, detection of clustering in high-grade areas (preferential drilling → declustering needed); cell-declustering weights preview and declustered vs naive mean.
- Twin-hole and closely-spaced pair inventory for later grade comparison.
- Data spacing vs typical classification guidance (configurable spacing table per deposit type) — indicative only, clearly labelled.
- Orientation of drilling relative to dominant structure/mineralisation trend (if provided) — JORC "Orientation of data in relation to geological structure".

---

## 4. SURVEY (DOWNHOLE) VALIDATION AND ANALYSIS (`SUR-xxx`)

### 4.1 Integrity checks (Datamine Drillhole Importer / Discover / Leapfrog / Micromine equivalents)
- Survey without collar; collar without survey; duplicate survey depth; non-increasing depths; negative depth.
- Dip out of range (−90…+90); azimuth out of range (0–360), 360 vs 0 normalisation.
- **Dip sign convention**: mixed positive/negative dips within project or within one hole (Discover "Dip sign discrepancy"); detect convention (negative-down vs positive-down) and up-holes (underground).
- Survey depth beyond EOH; no survey at/near collar (first station depth > threshold) — collar orientation used?; survey station spacing too large (e.g. > 30–50 m) or irregular.
- Constant azimuth/dip for the whole hole, or identical to collar design → **"unsurveyed / design-only" hole** (flag; JORC Table 1 relevance).
- Survey type/instrument (single-shot, multi-shot, gyro, north-seeking gyro, MEMS, EMS) completeness; magnetic vs non-magnetic instruments.

### 4.2 Deviation and error analysis
- **Dogleg severity** (°/30 m) between consecutive stations; WARNING/ERROR thresholds (defaults 3°/30 m and 6°/30 m, editable).
- **Large dip change** and **large azimuth change** between adjacent stations (Datamine "Large dip/azimuth curvature" logic, defaults 5° dip, 10° azimuth) — but **suppress azimuth alerts for near-vertical intervals** (dip steeper than −85°) where azimuth is mathematically unstable.
- Azimuth spikes (single-station outliers returning to trend) → probable **magnetic interference**; correlate azimuth anomalies with magnetite/pyrrhotite logging, Fe assays, magnetic susceptibility or magnetic grid → separate "instrument error" from "real deviation".
- **Magnetic declination / grid convergence**: check azimuth reference (magnetic / true / grid); detect constant azimuth offset between survey types or between collar design and first station; compute and apply declination (by date & location model, user override) and UTM grid convergence.
- Lift and drift rates by hole type, rig, diameter, lithology, depth (box plots).
- Desurvey with **minimum curvature** (default), balanced tangential, tangential; report end-of-hole position differences between methods; flag holes where the difference > threshold.
- 3D hole-to-hole minimum distance → **intersecting/crossing traces** (likely survey error).
- Plots: dip vs depth and azimuth vs depth per hole (with error flags), deviation drift plot, rose diagram of collar azimuths, stereonet of collar orientations, plan and section views of traces with planned vs actual where design data exist.

---

## 5. GENERIC INTERVAL-TABLE CHECKS (applied to EVERY interval table) (`INT-xxx`)

For each interval table (assay, lithology, alteration, mineralisation, weathering, geotech, density, structure, sample, etc.):
- Missing HoleID / From / To; non-numeric depths; From ≥ To; zero-length; negative depths.
- **Overlaps** (partial and full), **duplicates** (identical rows; same interval different values → conflict), **gaps** (top gap from 0, internal gaps, bottom gap to EOH — the GEOVALID coverage logic), intervals beyond EOH.
- Coverage % per hole and per table; data completeness heat-map **holes × tables**.
- Interval length distribution (histogram per table, per hole type); non-standard sample lengths; very short (< 0.2 m) or very long intervals; depth precision (decimals) and rounding artefacts.
- Unmerged consecutive identical records; mandatory fields empty; values outside a controlled vocabulary.
- Cross-table boundary alignment: sample intervals **crossing lithology/alteration/mineralisation contacts** (% of samples crossing, with list) — sampling-to-geology practice.
- Repetition patterns suggesting copy‑paste errors (blocks of identical values repeated between holes).

---

## 6. ASSAY TABLE (`ASY-xxx`)

### 6.1 Element and unit recognition
- Parse headers with a robust regex + dictionary: element symbol / oxide (Cu, Au, Ag, Mo, Pb, Zn, Fe, Fe2O3, FeO, SiO2, Al2O3, TiO2, P, P2O5, S, As, Sb, Bi, Co, Ni, Cr2O3, Mn, MnO, U, REE…, LOI), **unit** (ppm, ppb, %, g/t, oz/t, ppm = g/t), **method / lab / digestion** suffix (FA, AAS, ICP‑OES, ICP‑MS, XRF, 4A, AR, LECO), repeat columns (`Au_rpt`, `Au_1`, `Au_2`), units in a separate row.
- If unit missing or ambiguous: infer from value magnitude and distribution, geochemical plausibility and inter-element relationships (e.g. Cu values 0–2 → %, 0–20 000 → ppm); show the inference, require confirmation.
- Convert all to a canonical unit set; keep the original columns.
- Detect **multiple methods for the same element** (e.g. Cu ICP and Cu AAS ore-grade) and build a "preferred value" rule (user-editable priority, over-range logic).

### 6.2 Value-level checks
- Text codes and placeholders: `<0.01`, `>10`, `-0.01`, `-1`, `-99`, `-999`, `0`, `NS`, `IS`, `LNR`, `NA`, `X`, blank → classify (below detection, above range, not sampled, insufficient sample, lost) and convert using a configurable policy (e.g. ½ DL) with counts reported.
- Detection limits per element and per lab/batch/period; **% below DL**; changes in DL over time; values exactly at DL; over-range values not re-assayed.
- Impossible values (negative real grades, > 100 %, oxide sums > 101 %, Au in % etc.), unit-mix within a column (bimodal by order of magnitude).
- Numeric precision and rounding by batch; zeros vs nulls confusion.
- Geochemical sanity: Cu (or Cu+Zn+Pb sulphide-equivalent) vs total S stoichiometry; Fe vs Fe2O3/FeO consistency (Fe_total = 0.6994·Fe2O3 + 0.7773·FeO); major-oxide total 98–101 % (with LOI); CuO/acid-soluble Cu ≤ total Cu; Au–Ag, Pb–Zn, Mo–Re, Cu–Au ratio stability; user-defined inequality rules.
- Missing assays inside logged mineralised zones; unsampled intervals flagged by lithology/mineralisation.

### 6.3 Exploratory statistics and graphics (per element, length-weighted and unweighted)
- Summary table: n, n missing, n<DL, min, P5, P25, median, mean, P75, P95, P99, max, SD, **CV**, skewness, kurtosis, geometric mean.
- Histograms (linear and log), **log-probability plots** (population breaks), box plots, ECDF; by lithology, alteration, weathering, hole type, campaign, lab.
- Outliers: Tukey fences on log values, MAD, log-probability breakpoints, spatial outliers (see §11); **top-cut analysis** (CV-based, decile analysis/Parrish, metal-at-risk, cumulative metal curve) — suggestion only.
- Correlations: Pearson on log data, Spearman, **CLR-transformed** correlation (compositional data), correlation heat-map with hierarchical clustering, scatter-plot matrix for key elements, PCA biplot, element ratio plots.
- Downhole grade strip plots per hole.

### 6.4 QA/QC (if QAQC data or sample-type flags exist; if absent → CRITICAL gap in report)
- Insertion rates (CRM, blanks, field / coarse / pulp duplicates, umpire) vs industry practice (configurable targets).
- **CRMs**: Shewhart control charts (±2SD warning, ±3SD failure), bias %, consecutive-failures rules (Westgard), mislabeled standard detection (value matches another CRM).
- **Blanks**: contamination threshold (e.g. > 5–10 × DL), carry-over test (blank immediately after high-grade sample), time-series plot.
- **Duplicates**: scatter with 1:1 and ±10/20 % lines, **HARD**, ranked HARD plot, MPD, RMA regression, Q-Q plot, Thompson–Howarth precision plot, by duplicate type.
- Umpire/inter-lab checks: bias, paired t-test / Wilcoxon, RMA.
- Batch-level pass/fail summary and list of batches requiring re-assay.

---

## 7. LITHOLOGY TABLE (`LIT-xxx`)

- Code inventory: list of unique codes, frequency (count and metres), proportion chart; detect **spelling variants / synonyms** (fuzzy matching, case, Persian/English mixing, abbreviations), propose a harmonised **code dictionary** (user-confirmed), flag codes absent from the project legend.
- Diversity metrics: number of units per hole, Shannon diversity per hole/campaign/geologist → detect over-splitting or lumping by different loggers.
- Thickness distribution per unit; very thin intervals (< 0.5 m, configurable); unmerged identical consecutive units.
- **Stratigraphic/sequence logic**: transition-probability matrix (Markov chain) of downhole contacts; flag rare/illogical transitions; user-defined forbidden sequences (e.g. overburden below bedrock).
- Logger effect: unit proportions by geologist/date (chi-square) — logging consistency.
- Cross-hole consistency: compare neighbouring holes at similar elevation (pierce points) — unit mismatch rate vs distance.
- Strip logs (graphic logs) per hole; fence diagrams/sections along drill lines.

### 7.1 Lithology vs geological map (first logged unit at collar)
- Intersect each collar with the geological map polygons; obtain map unit.
- User-editable **correlation table** map-unit ↔ logged lithology codes (many-to-many; with "cover" units such as alluvium/scree/soil handled: compare map unit with the first logged bedrock unit when cover is logged).
- Distance from collar to nearest map contact → if within buffer (default = map scale tolerance, e.g. 1:25 000 → ~25 m), downgrade mismatch to WARNING ("near contact").
- Results: confusion matrix (map unit × first logged unit), agreement %, Cohen's kappa, map of matches/mismatches, table of mismatching holes with possible causes (collar position error, map generalisation, logging error, cover thickness).
- Optional: compare trench/surface samples and outcrop points with the map.

---

## 8. GEOTECHNICAL — CORE RECOVERY (CR) AND RQD (`GEO-xxx`)

- Range checks: CR 0–100 % (> 100 % → run-length or block error; allow small tolerance), RQD 0–100 %, **RQD ≤ CR** (and ≤ 100 %), negative values.
- If raw measurements exist (run length, recovered length, sum of pieces > 10 cm, fracture counts): **recompute CR and RQD** and compare with recorded values; recompute fracture frequency.
- Run length distribution vs core barrel length; runs overlapping or crossing; gaps.
- Statistics and histograms of CR and RQD; by lithology, alteration, weathering, depth, hole type, rig/driller, diameter.
- **Recovery–grade relationship** (sample bias): scatter, binned recovery classes (e.g. < 70, 70–85, 85–95, > 95 %) vs mean grade, test whether low-recovery samples are systematically higher/lower grade (preferential loss of fines/sulphides or washing) — JORC Table 1 "Drill sample recovery". For RC: recovered sample weights vs theoretical, wet/dry samples.
- RQD/CR vs alteration intensity and vs structural zones; downhole plots with lithology/alteration strips.
- Correlation CR ↔ RQD ↔ grade ↔ lithology summarised in a matrix and narrative.

---

## 9. ALTERATION, MINERALISATION, WEATHERING (`ALT-xxx`, `MIN-xxx`, `WTH-xxx`)

- Code inventory, synonym harmonisation, intensity scale validation (e.g. 0–4 or weak/moderate/strong/pervasive), mixed scales, missing intensity where type is logged.
- Multiple alteration fields (primary/secondary) consistency; assemblage logic (e.g. potassic vs phyllic vs argillic vs propylitic zoning order for porphyry profiles).
- Alteration vs lithology contingency table (chi-square, Cramér's V) and mosaic plot.
- Alteration / intensity vs grade box plots and grade-by-class statistics.
- **Logging vs geochemistry cross-checks** (where majors/traces exist): K/Al, Na/Al molar ratios, Ishikawa AI, CCPI, alteration box plot; logged sulphide % vs S assay; logged magnetite vs Fe / magnetic susceptibility; logged oxidation vs CuO/acid-soluble Cu or S depletion; logged quartz veining vs SiO2.
- Weathering/oxidation profile: logical downhole order (oxide → transition → fresh), depth of oxidation surface per hole, map of base of oxidation; inconsistencies between neighbouring holes.

---

## 10. OTHER INTERVAL / POINT TABLES

- **Density/SG**: range per lithology (geologically plausible bounds), method (Archimedes, wax-coated, pycnometer, gamma), vs grade (e.g. Fe, sulphides), vs weathering, outliers, coverage relative to mineralised zones, regression density = f(grade) suggestion.
- **Magnetic susceptibility**: units (SI ×10⁻³ vs ×10⁻⁵), range, vs magnetite logging and Fe.
- **Structure** (alpha/beta, dip/dip direction): range checks, conversion to true orientation using survey, stereonets per domain, consistency with oriented-core flags.
- **Sample table**: sample number uniqueness, sequence gaps, sample-weight checks, dispatch/batch linkage, chain-of-custody fields.
- Any unknown interval table: generic checks (§5) + automatic numeric/categorical profiling.

---

## 11. CROSS-TABLE AND SPATIAL INTEGRATION (`CRS-xxx`, `SPA-xxx`)

- Build a merged, desurveyed **interval master table** (all tables split to common boundaries) with XYZ midpoints.
- High grades in "barren" logged units; low grades in logged ore zones; mineralised-zone continuity between holes.
- Grade by lithology × alteration two-way table; ANOVA / Kruskal–Wallis between domains; candidate **estimation domains** suggestion (statistical separation + contact analysis).
- **Contact analysis** (grade vs distance from lithology/alteration contacts): hard vs soft boundaries.
- Spatial statistics: plan and section maps of grades (max/average per hole, grade-thickness), **local Moran's I / Getis–Ord** to detect spatial outliers (a high value surrounded by lows → possible sample swap/error), nearest-neighbour grade difference vs distance.
- **Twin-hole comparison**: paired composites, Q-Q plots, mean differences, by drilling method (e.g. RC vs DD bias).
- **Drilling method bias**: grade distributions by method (Q-Q, KS test) for spatially comparable samples.
- Swath plots (along X, Y, Z) of raw grade and sample count — trend and clustering diagnosis.
- Experimental variogram preview (omnidirectional + main directions) for key elements — optional, informative only.
- Compositing preview (length, by domain) and composite length recommendation from sample-length statistics.

---

## 12. DATABASE VERSION COMPARISON (`VER-xxx`)

- Compare two versions of the same database (or database vs software export): added/removed holes, changed coordinates/EOH, changed survey stations, changed intervals, changed values (per field, with magnitude), renamed codes.
- Diff report (summary + detailed table) and visual change map.

---

## 13. DATA CONFIDENCE SCORING

- Score (0–100) per hole and per table from weighted issue counts and severities, coverage, collar method confidence, survey quality, QA/QC status.
- Project **Data Confidence Index** with a traffic-light dashboard.
- Matrix of findings mapped to **JORC 2012 Table 1 Section 1** items (Sampling techniques, Drilling techniques, Drill sample recovery, Logging, Sub-sampling & preparation, Quality of assay data & laboratory tests, Verification of sampling & assaying, Location of data points, Data spacing & distribution, Orientation of data, Sample security, Audits) and **NI 43‑101 Items 11–12**.
- "Fit-for-purpose" statement per use (exploration targeting / Inferred / Indicated support) — clearly labelled as indicative, not a Competent Person opinion.

---

## 14. OUTPUTS

1. **Issue log** (XLSX + CSV): all issues, filterable, with rule ID, severity, location, value, suggested fix, status; summary pivot sheets per table/rule/hole.
2. **Cleaned database** (never overwrites original): versioned, with flag columns (`QC_FLAG`, `QC_COMMENT`), change log / audit trail (who, when, what, why).
3. **Exports** ready for Leapfrog Geo (CSV set), Datamine (CSV/DM where possible), Micromine, Surpac, Vulcan, generic CSV; GIS layers (GeoPackage, KML/KMZ, SHP) of collars and traces with flags and inferred collar-survey method.
4. **Figures**: every chart as PNG (300 dpi) + SVG; consistent numbering and captions (fa/en).
5. **Technical report**: DOCX (editable) + PDF + interactive HTML dashboard; language Persian, English or bilingual (user choice); A4; Arad/A.A branding placeholder (logo, header/footer).
6. **Validation profile** (YAML) and run metadata (software version, input file hashes, parameters, date) for reproducibility and audit.

### 14.1 Report structure
1. Executive summary (key findings, confidence index, top 10 critical issues, recommendations)
2. Database inventory (tables, holes, metres, samples, campaigns, methods, coverage matrix)
3. Collar (integrity, survey-method inference, ΔZ vs topography, spacing & density)
4. Downhole survey
5. Interval integrity (all tables)
6. Assays (units, DL, statistics, outliers, correlations, QA/QC)
7. Lithology (+ geological map comparison)
8. Geotechnical (CR, RQD, recovery–grade)
9. Alteration / mineralisation / weathering
10. Density and other tables
11. Cross-table & spatial analysis (domains, contacts, twins, method bias, swaths)
12. Data confidence & JORC Table 1 mapping
13. Recommendations & action plan (prioritised, with effort estimates)
Appendices: full issue list, rule catalogue with thresholds, code dictionaries, method notes, glossary (fa/en).
Every section: auto-generated narrative interpreting the figures (not just describing them), with numbers pulled from results; no placeholder text in final output.

---

## 15. FIGURE AND TABLE STYLE GUIDE (report-quality)

- One style module used by all charts: colour-blind-safe palettes (viridis/cividis for continuous; Okabe–Ito / Tableau 10 for categories; diverging RdBu for residuals), consistent lithology/alteration colour legend shared across all plots.
- Always show: title, axis labels with units, n (and n excluded), scale bar + north arrow + grid coordinates on maps, legend, source/caption.
- Log axes where appropriate with readable tick labels; avoid overplotting (alpha, hexbin).
- Fonts: Vazirmatn (Persian), Inter/Source Sans (English); correct RTL shaping in figures and DOCX.
- Tables: zebra rows, thousands separators, significant figures appropriate to the data, units in headers, highlighted failures.
- Export sizes matching A4 portrait/landscape report widths.

---

## 16. USER INTERFACE AND WORKFLOW

Wizard: **Create project → Import files → Map fields & units → Set CRS → Load topo/map/boundary → Choose validation profile → Run → Review → Fix/annotate → Re-run → Export & report.**
- Dashboard: issue counts by severity/table, confidence gauges, mini-maps.
- Review panel: filter by severity/rule/hole; clicking an issue shows the record in context (previous/next rows, hole strip log, location on map/section).
- Bulk actions: accept fix / ignore with mandatory reason / edit value.
- Map & section viewer (2D, optional 3D) with hole traces coloured by any field or by issue flags.
- Settings: thresholds, dictionaries, synonym tables, report language, branding.
- CLI: `geovalid run --project x.gvp --profile porphyry_cu.yaml --report fa` for batch use.
- Performance target: ≥ 5 000 holes / 1 000 000 interval rows on a normal laptop; progress bars; responsive UI (background workers).

---

## 17. RULE CATALOGUE (minimum — extend as needed)

| ID | Table | Check | Default severity |
|---|---|---|---|
| COL-001 | Collar | Duplicate HoleID | CRITICAL |
| COL-002 | Collar | Missing/zero/non-numeric X, Y, Z, EOH | ERROR |
| COL-003 | Collar | HoleID format inconsistent / near-duplicate IDs | WARNING |
| COL-004 | Collar | Duplicate / near-duplicate coordinates (twins, wedges, true duplicates) | WARNING |
| COL-005 | Collar | Outside licence boundary / project extent | ERROR |
| COL-006 | Collar | Swapped X/Y, wrong UTM zone, lat/long in UTM fields | CRITICAL |
| COL-007 | Collar | EOH < max depth in survey/interval tables | ERROR |
| COL-008 | Collar | Collar without survey | WARNING |
| COL-009 | Collar | Collar without any interval data | INFO |
| COL-010 | Collar | Inferred survey method = handheld GPS / planned / digitised | WARNING |
| COL-011 | Collar | \|ΔZ\| collar–topography above threshold | WARNING/ERROR |
| COL-012 | Collar | Systematic ΔZ offset (datum suspicion) | WARNING |
| COL-013 | Collar | Repeated identical Z values | WARNING |
| COL-014 | Collar | Date inconsistencies / drilling-rate outliers | WARNING |
| COL-015 | Collar | Spacing outlier / clustered drilling (declustering needed) | INFO |
| SUR-001 | Survey | HoleID not in collar | ERROR |
| SUR-002 | Survey | Duplicate survey depth | ERROR |
| SUR-003 | Survey | Dip out of range | ERROR |
| SUR-004 | Survey | Azimuth out of range | ERROR |
| SUR-005 | Survey | Mixed dip sign convention | ERROR |
| SUR-006 | Survey | Survey depth > EOH | ERROR |
| SUR-007 | Survey | First station too deep / no collar orientation | WARNING |
| SUR-008 | Survey | Station spacing too large/irregular | WARNING |
| SUR-009 | Survey | Design-only / constant survey (unsurveyed) | WARNING |
| SUR-010 | Survey | Dogleg severity above threshold | WARNING/ERROR |
| SUR-011 | Survey | Large dip change between stations | WARNING |
| SUR-012 | Survey | Large azimuth change (dip shallower than −85° only) | WARNING |
| SUR-013 | Survey | Azimuth spike — probable magnetic interference | WARNING |
| SUR-014 | Survey | Azimuth reference (magnetic/true/grid) inconsistency | WARNING |
| SUR-015 | Survey | Desurvey-method EOH difference above threshold | INFO |
| SUR-016 | Survey | Trace crosses another trace / exits above topography | ERROR |
| INT-001 | Any interval | From ≥ To / zero / negative | ERROR |
| INT-002 | Any interval | Overlapping intervals | ERROR |
| INT-003 | Any interval | Duplicate / conflicting intervals | ERROR |
| INT-004 | Any interval | Top / internal / bottom gaps | WARNING |
| INT-005 | Any interval | Interval beyond EOH | ERROR |
| INT-006 | Any interval | HoleID not in collar | ERROR |
| INT-007 | Any interval | Non-standard / extreme sample length | INFO |
| INT-008 | Any interval | Sample crosses geological contact | INFO |
| INT-009 | Any interval | Copy-paste repetition pattern | WARNING |
| ASY-001 | Assay | Unit unknown / inferred | WARNING |
| ASY-002 | Assay | Text codes / placeholders / negative DL codes | INFO |
| ASY-003 | Assay | Impossible value (> 100 %, negative real grade, oxide sum) | ERROR |
| ASY-004 | Assay | Mixed units in a column | ERROR |
| ASY-005 | Assay | Over-range not re-assayed | WARNING |
| ASY-006 | Assay | Stoichiometric/ratio inconsistency (Cu–S, Fe–Fe2O3, CuO > Cu) | WARNING |
| ASY-007 | Assay | Statistical / spatial outlier | INFO |
| ASY-008 | Assay | Missing assays in logged mineralised interval | WARNING |
| QAQ-001 | QAQC | Insufficient insertion rate / no QAQC | CRITICAL |
| QAQ-002 | QAQC | CRM failure (±3SD) / bias | ERROR |
| QAQ-003 | QAQC | Blank contamination / carry-over | ERROR |
| QAQ-004 | QAQC | Duplicate precision failure (HARD) | WARNING |
| LIT-001 | Lithology | Code not in dictionary / synonym variants | WARNING |
| LIT-002 | Lithology | Thin interval / unmerged consecutive codes | INFO |
| LIT-003 | Lithology | Illogical sequence | WARNING |
| LIT-004 | Lithology | First unit ≠ geological map unit | WARNING |
| LIT-005 | Lithology | Logger-dependent bias | INFO |
| GEO-001 | Geotech | CR > 100 % or < 0 | ERROR |
| GEO-002 | Geotech | RQD > CR or > 100 % | ERROR |
| GEO-003 | Geotech | Recorded vs recomputed CR/RQD mismatch | WARNING |
| GEO-004 | Geotech | Recovery–grade bias detected | WARNING |
| ALT-001 | Alteration | Invalid code / intensity scale | WARNING |
| ALT-002 | Alteration | Logging contradicts geochemistry | WARNING |
| WTH-001 | Weathering | Illogical oxidation sequence | WARNING |
| DEN-001 | Density | Implausible value for lithology | WARNING |
| CRS-001 | Cross | High grade in logged barren unit (and inverse) | INFO |
| CRS-002 | Cross | Drilling-method grade bias | WARNING |
| SPA-001 | Spatial | Spatial outlier (local Moran's I) | INFO |

---

## 18. DEVELOPMENT PLAN AND QUALITY ASSURANCE

- **Phase 1**: core model, IO, field mapping, collar/survey/interval rules, issue log, basic report.
- **Phase 2**: assays (units, DL, stats, correlations), lithology (+map), geotech, alteration, plots style guide.
- **Phase 3**: topo ΔZ, collar method inference, spacing/density, desurvey & survey analytics, QA/QC.
- **Phase 4**: cross-table & spatial analysis, confidence scoring, JORC mapping, full DOCX/PDF/HTML reports, version comparison.
- **Phase 5**: GUI polish, 3D viewer, packaging, user manual (fa/en).
- Build a **synthetic test database generator** that injects every error type of §17 at known locations; each rule must have unit tests proving detection and no false positives on clean data. Also regression-test on at least one real anonymised database.
- Code quality: type hints, docstrings, logging, no hard-coded thresholds, modular rules (new rule = new file + registration).
- Before writing code, present: (1) the final architecture, (2) the canonical data schema, (3) the rule catalogue with any additions you propose, (4) the phase plan — and wait for approval. After each phase, deliver a runnable build and a short test report.

---

## 19. ADDITIONAL INSTRUCTIONS TO THE AI

- Research and include any further checks used by acQuire GIM Suite, MX Deposit, Fusion, Leapfrog, Datamine (Drillhole Importer, Discover), Micromine, Surpac, Vulcan, Deswik and published database-audit practice that are not listed here; list them as proposed additions with source software.
- Prefer transparency over automation: every inference (unit, survey method, synonym, fix) must show its evidence and be overridable.
- Interpretive text must be geologically meaningful (explain *why* an issue matters for modelling/estimation and *what to do*), concise, and free of generic filler.
- All thresholds are defaults, editable, and reported in the appendix.
- The software is a decision-support tool; final acceptance of data for public reporting remains with the Competent/Qualified Person — state this in the report.
