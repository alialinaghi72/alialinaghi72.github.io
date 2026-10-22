# GEOVALID PRO — 01 · Final Architecture
### معماری نهایی سامانه (Final Architecture)

| | |
|---|---|
| Document | `01_architecture.md`, design package item (1) of brief §18 |
| Status | **DRAFT v0.1 for client approval.** No code is written against it until it is approved. |
| Date | 2026-10-22 |
| Governs | Process and module structure; technology stack and licences; physical project container; rule-engine mechanics; derived-product cache; change-management mechanics; scoring engine; reporting pipeline; GUI; CLI; performance; security; packaging |
| Defers to | `02_data_schema.md` (tables, fields, enums, keys, normalisation steps N01–N18, fingerprint formula), `03_rule_catalogue.md` (rule logic, parameters, thresholds, numbering of new rules), `04_phase_plan.md` (schedule of modules and spikes), `05_traceability.md` (brief clause → design → test) |

Section numbers §0–§19 refer to the requirements brief. "02 §x" refers to the data schema. Rule IDs are the brief §17 IDs; a rule this document needs but the brief does not list is written `FAM-*` and is numbered in `03_rule_catalogue.md`.

---

## 0. Decisions at a glance

| # | Area | Decision | Relation to brief |
|---|---|---|---|
| A1 | Process model | One **headless engine** (`geovalid_pro` without `gui/`). The CLI calls it in-process. The GUI calls it in-process for short read-only tasks and through a **worker subprocess** (the same executable) for long jobs. | Refines §1.1 |
| A2 | Project file | `.gvp` = **one SQLite file** holding system and reference tables plus content-addressed **Parquet blobs**. A disposable local cache is used for fast columnar reads (02 §8). | Refines §1.1 "Parquet/SQLite project file" |
| A3 | Data engine | **pandas (≥ 2.2, Copy-on-Write) on pyarrow dtypes** is the only in-memory API that rules and analysis see. **DuckDB** is embedded for four named set-based operations. Polars is rejected. | Addition |
| A4 | PDF | The **same Jinja2 HTML** is rendered to PDF by **Qt WebEngine** (`QWebEnginePage.printToPdf`). WeasyPrint and ReportLab are rejected. | **Deviation** (§1.1 Reports) |
| A5 | GIS I/O | **pyogrio** (through geopandas 1.x) replaces fiona. **ezdxf** reads DXF instead of the GDAL DXF driver. rasterio and shapely 2 are kept. | **Deviation** (§1.1 Spatial) |
| A6 | MS Access | Tiered reader: **ACE ODBC (pyodbc)** → **pure-Python fallback (access-parser, vendored)** → guided CSV export. | Refines §2.1 |
| A7 | Proprietary formats | Surpac ASCII `.str`/`.dtm`: implemented. Datamine `.dm` and Micromine `.DAT`: **time-boxed spikes** against client sample files. CSV exports are the supported path until a spike passes. | Honest scoping of §2.1/§2.3 |
| A8 | Declination | Own **IGRF-14 / WMM2025** spherical-harmonic synthesis from bundled coefficient files, with project override. Grid convergence comes from pyproj. | Addition (§4.2) |
| A9 | Persian text | matplotlib: `arabic_reshaper` + `python-bidi` per wrapped line, Vazirmatn. DOCX: `w:bidi`/`w:rtl`/complex-script fonts with Vazirmatn **embedded**. HTML/PDF: native Chromium shaping. | As §1.1, made precise |
| A10 | Fonts | **Vazirmatn** (Persian) and **Inter** (Latin), both OFL-1.1, bundled and embedded in every output | Chooses Inter over Source Sans 3 |
| A11 | Collar method inference | **Weights-of-evidence scoring** with log-odds contributions that are shown and editable. No trained ML model. scikit-learn is kept only for Gaussian mixtures and robust covariance. | Refines §3.2 |
| A12 | Rule packaging | One sub-package per family, **one file per rule**, decorator registration. User rules are declarative (safe expressions). No user Python by default. | Reconciles §1.2 with §18 |
| A13 | GUI plotting | **pyqtgraph** for the interactive map, section and strip log. **matplotlib-Qt** for report-identical charts. Qt Charts and Qt Data Visualization are **banned** (GPL-only). | Refines §1.1 |
| A14 | Narrative | Deterministic **phrasebook engine** (YAML, fa/en) driven by computed findings and thresholds. **No LLM**: the report is produced fully offline. | Makes §14.1 implementable offline |
| A15 | Packaging | **PyInstaller one-dir + Inno Setup**. Nuitka is not used. The packaging pipeline runs **from Phase 1**, not first in Phase 5. | **Deviation in timing** (§18) |
| A16 | Offline | Enforced technically (socket guard, WebEngine request interceptor, PROJ/GDAL/DuckDB network off) and proven by a no-network CI job | Makes §1.1 testable |
| A17 | Determinism | Seeded statistics, stable sorts, content hashes. Identical inputs give identical issues, fingerprints and report numbers (02 §1.10). | Addition |
| A18 | Reports from working data | Final reports and **all exports** come from a `RELEASE` (02 §9). A **draft** report from the working version is allowed, watermarked on every page. | Clarifies 02 §9.5 |
| A19 | Report language `bi` | **Primary-language body** (default fa) with bilingual headings, captions, table headers, chapter key findings, executive summary and action plan. Figure and table numbers are identical in fa, en and bi. A full second-language report comes from the same job on request (§9.5). | Interprets §14 item 5 |
| A20 | Report outputs | One Report Document Model feeds DOCX, print HTML → PDF and a **self-contained** dashboard. Lint blocks placeholders and untraceable numbers. **PDF/A is not produced** (§9.8). | Refines §14 |
| A21 | GUI workflow | **Non-modal stepper** instead of a modal wizard; linked views through a selection bus. Maps, sections, strip logs, charts, IDs and numeric fields are **never mirrored** in RTL. A language change applies on restart (§10). | Refines §16 |
| A22 | Large tables | `ArrowTableModel` over memory-mapped Arrow with DuckDB-computed permutations; **no `QSortFilterProxyModel`**. Grids are read-only; edits go only through change sets (§10.8). | Makes §16 performance achievable |
| A23 | CLI | Non-interactive; decisions come from files; stable exit codes (0–7, 70, 130); `--fail-on` threshold with a `--baseline` ratchet; JUnit output (§11) | Extends §16 |
| A24 | Performance targets | Dataset L (5 000 holes, 1.05 M interval rows, 12 M assays) on a 16 GB, 4-core laptop: full validation **≤ 150 s**, incremental ≤ 45 s, peak worker RSS ≤ 5 GB. Gated nightly on a reference machine (§12). | Makes §16 testable |
| A25 | Persistence | No Save command for review work: every decision is committed at once. Rolling `VACUUM INTO` backups. A release anchor printed in every report (§13.2, §13.3). | Addition |
| A26 | Distribution | Two executables (GUI; console CLI and worker) in one one-dir bundle; **per-user install without admin rights**; side-by-side major versions. Linux gets a headless wheel only (§14). | Refines §1.1 |

---

## 1. Architectural overview

### 1.1 Principles
1. **Headless core.** All behaviour lives in the engine. The GUI and the CLI are thin clients of `geovalid_pro.api`. Nothing in the engine imports Qt widgets. Qt WebEngine is imported only by the PDF renderer.
2. **Data are immutable; edits are change sets.** The raw snapshot is frozen. Every edit is a change set with who, when, old, new and why (02 §1.2, §5.7).
3. **Rules are pure.** A rule is a function of (dataset version, derived products, parameters) → issues. It cannot write data, and this is enforced (§7.8).
4. **Every inference is a record with evidence**, and every one can be overridden (02 §1.9, brief §19).
5. **Columnar and vectorised.** Hot paths contain no per-row Python loops. Every algorithm is expressed as sort, group, shift, searchsorted or KD-tree operations.
6. **Offline by construction.** No code path opens a network connection.
7. **Bilingual by construction.** Every user-facing string has fa and en forms. RTL correctness is tested, not assumed.
8. **Reproducible.** Every number in a report can be regenerated from the source bytes, the decisions taken and the software version.

### 1.2 System overview

```mermaid
flowchart TB
  subgraph Clients
    GUI["GUI — PySide6<br/>wizard · dashboard · review · map/section/strip log"]
    CLI["CLI — geovalid<br/>run · validate · report · export · diff · profile · gen-synthetic"]
  end
  GUI -- "short read-only tasks<br/>(in-process, QThreadPool)" --> API
  GUI -- "long jobs: geovalid worker<br/>(subprocess, NDJSON progress, cancel)" --> CLI
  CLI --> API["geovalid_pro.api — application services<br/>Project · Job · Progress · CancelToken"]
  subgraph ENGINE["Headless core engine"]
    direction TB
    IO["io<br/>readers · sniffing · writers"] --> NORM["io.normalise<br/>N01–N18 cell normalisation"]
    NORM --> MAP["mapping<br/>field match · table type · codes"]
    MAP --> INF["analysis.inference<br/>units · CRS · dip · azimuth ref"]
    INF --> CORE[("core<br/>schema · versions · change sets<br/>issues · audit · units · CRS · geomag")]
    CORE --> RUL["rules<br/>engine · 18 families · profiles"]
    CORE --> ANA["analysis<br/>products · desurvey · stats · spatial"]
    ANA --> RUL
    RUL --> SCO["scoring<br/>confidence · JORC · NI 43-101"]
    ANA --> SCO
    ANA --> PLT["plots<br/>figure registry · style"]
    SCO --> REP["report<br/>RDM → DOCX · HTML · PDF"]
    PLT --> REP
    RUL --> REP
  end
  API --> ENGINE
  CORE <--> GVP[(".gvp — SQLite file<br/>system tables + Parquet blobs")]
  ANA <--> CACHE[("working cache<br/>%LOCALAPPDATA%\geovalid_pro\cache")]
```

### 1.3 Data flow

```
 source files ──► IMPORT ──► NORMALISE ──► MAP ──────► VALIDATE ──► ANALYSE ──► SCORE ──► REVIEW / FIX ──┐
   (bytes)        V0 raw     N01–N18        Vb          issues        drv_*       DCI       change sets    │
                  snapshot   (cell text)    canonical   (fingerprint) products    JORC      (DRAFT→APPLIED)│
                                            base +                                                         │
                                            inferences          ▲ incremental re-run                       │
                                                                └──────────── Vw = Vb ⊕ CS₁…CSₙ ◄──────────┘
                                                                                   │ freeze (release gates §7.6)
                                                                                   ▼
                                                                     RELEASE Vr ──► EXPORT · REPORT · CLEANED DB
```

| Stage | Input → output | Module | Persisted in | Re-runs when |
|---|---|---|---|---|
| Import | bytes → `source_file`, `raw_<n>` (all text) | `io.readers`, `io.sniff` | `.gvp` blobs (V0) | A new file is added |
| Normalise | raw text → normalised text and typed candidates + `normalisation_log` | `io.normalise` | `.gvp` (logs); output is part of Vb | Never on its own. It is part of the Vb build |
| Map | raw + `field_mapping` + decided inferences → canonical base Vb | `mapping`, `analysis.inference`, `mapping.build` | `.gvp` blobs (Vb) | The mapping or an inference decision changes (change sets are then rebased, §7.5) |
| Validate | Vw + products + profile → `issue`, `issue_context` | `rules.engine` | `.gvp` (SQLite) + Parquet issue snapshot in cache | On request; incremental (§5.4.4) |
| Analyse | Vw → `drv_*` products | `analysis` | cache (L1/L2); copied into `.gvp` on release | Its input column hashes or parameters change |
| Score | issues + products → `drv_confidence` | `scoring` | cache; `.gvp` on release | After each validation run |
| Review/fix | issues → `issue_review`, `change_set`, `change` | `api.review`, `core.changes` | `.gvp` (SQLite, append-only) | User action |
| Release | Vw → frozen Vr + frozen products | `core.versions` | `.gvp` | User action, after release gates pass |
| Export/report | Vr → files | `io.writers`, `report` | Output folder + `blob` (kind `REPORT`) + `audit_log` | User action |

### 1.4 Process and thread model

| Process / thread | Runs | Why |
|---|---|---|
| **GUI process — Qt main thread** | Widgets, models and painting only. It never runs a computation that takes more than ~50 ms. | Keeps the UI responsive |
| GUI process — `TaskPool` (QThreadPool, ≤ 4 threads) | Short, read-only tasks of a few seconds at most: issue filtering, record context, a chart's data, a strip log | Avoids subprocess start-up cost for interactive work |
| **Worker subprocess** (`geovalid worker --job <job.json>`) | Import, Vb build, validation run, release, report, export, diff. **At most one writing job per project.** | **Isolation:** a crash in a native library (GDAL, ACE driver, Chromium) cannot take the GUI down with unsaved review work. **No GIL contention** with the UI. **Hard cancel** is possible. **Memory:** a peak of several GB is returned to the OS when the job ends, whereas CPython would keep it resident in a long-lived GUI process. The GUI also exercises **exactly the CLI code path**: one engine, one behaviour. |
| CLI process | Same engine, in-process. Creates a headless `QGuiApplication` (`QT_QPA_PLATFORM=offscreen`) only when a PDF is requested. | CI and batch use |
| Figure-render pool (`concurrent.futures.ProcessPoolExecutor`, ≤ 4 processes) | matplotlib rendering of report figures | matplotlib is not thread-safe. Figure rendering is the longest single step of report generation. |

Inside the engine, **rules run sequentially in a deterministic order** (§5.4). Parallel speed-up comes from vectorised NumPy/BLAS kernels and from chunked permutation tests. This keeps determinism and avoids relying on pandas thread-safety, which is not guaranteed.

The GUI and its worker communicate through:
1. **NDJSON on stdout/stdin** (progress, log lines, cancel request, result summary);
2. **the project file itself** (SQLite in WAL mode; the worker writes in short transactions of ≤ 50 000 rows);
3. a **Parquet issue snapshot** in the cache, so the GUI loads a 1 M-issue run in under a second instead of reading it row by row from SQLite.

---

## 2. Package and module tree

### 2.1 Tree with responsibilities

```
geovalid_pro/
├── __init__.py               version; re-exports api.Project
├── __main__.py               `python -m geovalid_pro` → cli.main
├── api/                      APPLICATION SERVICES: the only surface gui/ and cli/ may call
│   ├── project.py            Project.create/open/close; lock; migrate; release; verify
│   ├── jobs.py               Job, JobResult, ProgressEvent, CancelToken, NDJSON codec, job manifest
│   ├── importing.py          add sources, preview, propose/confirm mapping, decide inferences, build Vb
│   ├── validation.py         plan and run rules (full or incremental); rule-execution matrix
│   ├── review.py             issue queries, status changes, bulk actions, draft change sets, apply/revert
│   ├── analysis.py           on-demand analyses for GUI panels (chart data, statistics, sections)
│   ├── reporting.py          report build (fa/en/bi; DOCX/PDF/HTML), figure set, issue log
│   ├── exporting.py          software, GIS and cleaned-database exports (from a release)
│   └── diffing.py            version comparison (VER family)
├── core/                     DOMAIN MODEL AND PERSISTENCE (no Qt, no plotting)
│   ├── container/            .gvp store (SQLite, blob store, chunked blob I/O), cache, locks, backups, migrations
│   ├── schema/               table specifications generated from 02 (fields, Arrow types, enums), validators
│   ├── store.py              ProjectStore (02 §8): column-projected, filtered, read-only reads by version
│   ├── versions.py           DatasetVersion (V0/Vb/Vw/Vr), manifests, column hashes, recipe hash, freeze
│   ├── changes.py            ChangeSet/Change model; apply (optimistic), revert, rebase, conflicts
│   ├── issues.py             Issue model, fingerprint (02 §5.5), status carry-over, message rendering
│   ├── inference.py          Inference/Evidence records; decision workflow
│   ├── audit.py              hash-chained audit_log (02 §5.8); chain verification on open
│   ├── units.py              unit catalogue and conversions (02 §2.5)
│   ├── crs.py                pyproj wrappers: transform, operation choice, convergence, geoid, local grids
│   ├── geomag.py             IGRF-14 / WMM2025 synthesis → declination, field, inclination
│   ├── calendar.py           Jalali ↔ Gregorian (33-year arithmetic cycle), Excel serials (1900/1904)
│   ├── i18n.py               language modes, digit and separator localisation, bidi isolates, glossary
│   ├── query.py              DuckDB facade (offline-locked configuration) for set-based operations
│   ├── hashing.py, ids.py    streaming SHA-256; UUIDv7
│   ├── offline.py            network guard (socket patch; PROJ/GDAL/DuckDB/Qt environment)
│   ├── settings.py           application settings (platformdirs); reviewer identity
│   └── log.py                logging configuration, run-log capture, crash handler
├── io/                       READERS AND WRITERS (bytes ⇄ raw tables ⇄ files)
│   ├── sniff.py              file type, encoding (N01), delimiter, header rows (N17), Excel date system
│   ├── normalise/            N01–N18 pipeline (02 §6); writes normalisation_log
│   ├── readers/
│   │   ├── text.py           CSV/TXT/fixed-width
│   │   ├── excel.py          XLSX/XLSM/XLSB/XLS: calamine values + openpyxl/xlrd number formats + merged ranges
│   │   ├── dbf.py            DBF (code page from LDID/.cpg)
│   │   ├── access.py         MDB/ACCDB, tiered (§3.5)
│   │   ├── sql.py            SQLite (stdlib); SQL Server/PostgreSQL through user-installed ODBC (read-only)
│   │   ├── surpac.py         .str/.dtm ASCII (binary variants are detected and refused with a message)
│   │   ├── datamine.py       .dm (SPIKE S-05; feature-flagged until it passes)
│   │   ├── micromine.py      .DAT (SPIKE S-06; feature-flagged)
│   │   ├── presets.py        acQuire, MX Deposit, Leapfrog export conventions (mapping templates)
│   │   ├── vector.py         SHP, GPKG, GeoJSON, KML/KMZ, FileGDB (read) via pyogrio
│   │   ├── raster.py         GeoTIFF, ESRI ASCII, SRTM .hgt, ALOS/ASTER tiles via rasterio
│   │   ├── points.py         XYZ/CSV point clouds; LAS/LAZ (laspy + lazrs)
│   │   ├── dxf.py            3DFACE, MESH, POLYFACE, POLYLINE/LWPOLYLINE (+elevation), POINT via ezdxf
│   │   └── mesh.py           OBJ, STL, PLY via trimesh
│   └── writers/
│       ├── software.py       Leapfrog, Datamine, Micromine, Surpac, Vulcan, generic CSV sets (export profiles)
│       ├── gis.py            GPKG, SHP, KML/KMZ: collars, 3D traces, intervals, flags, inferred method
│       ├── issue_log.py      issue log XLSX (XlsxWriter, pivot sheets) + CSV
│       ├── cleaned_db.py     cleaned database (02 §9.6): CSV set + XLSX + SQLite, QC_FLAG/QC_COMMENT, change log
│       └── surpac_str.py     .str writer; datamine_dm.py only if S-05 passes
├── mapping/                  SCHEMA MAPPING AND CODE HARMONISATION
│   ├── headers.py            header keys (N13), synonym index (en/fa) from field_dictionary
│   ├── matcher.py            candidate scoring (rapidfuzz + content checks) + one-to-one assignment
│   ├── table_type.py         table-kind classifier (collar, survey, interval, point, assay, QA/QC, …)
│   ├── assay_headers.py      analyte/unit/method/repeat token parser (02 §4.8)
│   ├── codes.py              code dictionaries; synonym proposals (fuzzy + abbreviations + fa/en equivalents)
│   ├── templates.py          mapping templates keyed by source signature; system presets
│   └── build.py              V0 + mapping + inferences → canonical base Vb (deterministic)
├── analysis/                 DERIVED PRODUCTS AND ANALYTICS (pure functions; persistence only through products.py)
│   ├── products.py           @product registry, keys, L1/L2/L3 cache, invalidation, variants
│   ├── desurvey.py           MIN_CURV / BAL_TAN / TAN; exact arc interpolation; drv_trace, drv_trace_compare
│   ├── survey_metrics.py     dogleg, lift/drift, spikes, magnetic-interference correlation
│   ├── intervals.py          interval algebra (overlap, gap, coverage); drv_interval_master
│   ├── composite.py          BEST_FIT / FIXED / DOMAIN_WHOLE compositing → drv_composite
│   ├── assay_wide.py         preferred values (02 §4.9.3) → drv_assay_wide (DuckDB pivot)
│   ├── inference/            depth unit, analyte unit, % scale, MS unit, coordinate format, CRS, zone, X/Y swap,
│   │                         Z datum, dip convention, azimuth reference, table type, campaign, sample type,
│   │                         collar survey method (weights of evidence)
│   ├── stats/                weighted descriptive statistics, outliers, top-cut, correlation/CLR/PCA,
│   │                         hypothesis tests, declustering, distribution fitting (GMM)
│   ├── geochem.py            stoichiometry, oxide factors, AI/CCPI, molar ratios, user inequalities
│   ├── qaqc.py               CRM/blank/duplicate/umpire metrics, Westgard rules, HARD, Thompson–Howarth, RMA
│   ├── logging_stats.py      code inventories, Markov transitions, diversity, logger effect, contingency tables
│   ├── spatial/              KD-tree service, TIN/grid DEM, sampling, slope, Voronoi, point pattern
│   │                         (Clark–Evans, Ripley K/L, grid detection), local Moran's I, Getis–Ord Gi*,
│   │                         variogram preview, pierce points, trace proximity, polygon overlay, swaths
│   └── version_diff.py       VER diff engine (DuckDB full outer joins on natural keys)
├── rules/                    RULE ENGINE AND CATALOGUE
│   ├── base.py               Rule, RuleMeta, RuleParams, Messages, IssueFrame schema
│   ├── registry.py           @register, discovery, catalogue export (md/xlsx/yaml, en/fa)
│   ├── profile.py            YAML loading (ruamel), inheritance, validation (pydantic), provenance, hashing
│   ├── engine.py             planner (applicability, dependency DAG), executor, result cache, post-processing
│   ├── severity.py           bands, aggregate escalation, demotion, suppressions
│   ├── messages.py           en/fa template rendering; placeholder parity checks
│   ├── expressions.py        safe expression language (user rules, narrative conditions, escalations)
│   ├── fixes.py              FixProposal → fix_json → DRAFT change set
│   └── imports/ collar/ survey/ interval/ assay/ qaqc/ lithology/ geotech/ alteration/ mineralisation/
│       weathering/ density/ magsus/ structure/ sample/ cross/ spatial/ version/
│                             one package per family (IMP COL SUR INT ASY QAQ LIT GEO ALT MIN WTH DEN MAG STR
│                             SMP CRS SPA VER); one file per rule, e.g. interval/int_002_overlap.py
├── scoring/
│   ├── confidence.py         component scores; hole, table and project DCI; caps; sensitivity
│   ├── jorc.py               JORC Table 1 Section 1 items T1.01–T1.12; NI 43-101 Items 11–12
│   └── fitness.py            indicative fit-for-purpose decision table
├── plots/
│   ├── style.py              style guide (§15): palettes, rcParams, size classes, shared code-colour registry
│   ├── text.py               Persian shaping for matplotlib (wrap → reshape → bidi, per line); numerals
│   ├── furniture.py          scale bar, north arrow (grid north + convergence note), grid ticks, n / n excluded, source line
│   ├── registry.py           @figure registry: key, section, captions fa/en, size class, data dependencies
│   ├── figures/              one module per report chapter (collar, survey, interval, assay, qaqc, lithology, …)
│   ├── interactive/          plotly builders for the HTML dashboard
│   └── render.py             300-dpi PNG + SVG; process-pool rendering; figure cache by data hash
├── report/
│   ├── model.py              Report Document Model (RDM): Document, Section, Block types
│   ├── findings.py           Finding objects built from analysis and scoring results
│   ├── narrative/            phrasebook engine + phrasebooks/*.yaml (fa/en); plural and number rules
│   ├── sections/             one builder per §14.1 chapter and appendix
│   ├── numbering.py          section/figure/table numbering; cross-references
│   ├── docx_builder.py       python-docx on reference templates; bidi/rtl; SEQ/TOC fields; font embedding
│   ├── html_builder.py       Jinja2 → print HTML and dashboard HTML
│   ├── pdf.py                Qt WebEngine renderer; header/footer overlay; two-pass TOC; PDF outline
│   ├── lint.py               no placeholders; every figure referenced; every number traceable to a finding
│   └── templates/            Jinja2 templates; print.css, dashboard.css; DOCX reference templates
├── gui/
│   ├── app.py                bootstrap: offline guard, fonts, translators, layout direction, exception hook
│   ├── main_window.py        docks, actions, selection bus
│   ├── wizard/               project wizard pages (§16)
│   ├── dashboard/            counts by severity/table, custom-painted gauges, mini-maps
│   ├── review/               issue table, filter bar, record-in-context, bulk actions, change-set panel
│   ├── viewers/              map, section, strip log (pyqtgraph); charts (matplotlib-Qt); view3d (optional)
│   ├── models/               ArrowTableModel, IssueTableModel (no proxy models)
│   ├── workers/              TaskPool (QThreadPool/QRunnable), JobRunner (QProcess), progress UI
│   ├── settings/             profile editor (forms generated from JSON Schema), dictionaries, branding
│   └── resources/            .qrc icons (compiled at build)
├── cli/
│   ├── main.py               click group `geovalid`
│   ├── commands/             run, validate, report, export, diff, profile, gen-synthetic, project, worker
│   ├── exit_codes.py
│   └── output.py             human output, --json, --junit, NDJSON progress
├── synth/                    synthetic database generator, error injectors, ground-truth manifest
├── _vendor/                  vendored, patched third-party code (access-parser, Sibson interpolation)
├── i18n/
│   ├── ts/geovalid_fa.ts     Qt Linguist source (UI strings)
│   ├── qm/                   compiled translations (build artefact)
│   ├── glossary.yaml         fa/en glossary (report appendix, tooltips), seeded from 02 Appendix A
│   └── labels/               enum, table and field labels fa/en (seeded from field_dictionary)
└── resources/
    ├── fonts/                Vazirmatn and Inter (TTF + WOFF2) + OFL texts
    ├── geomag/               IGRF-14 coefficients, WMM2025.COF, reference test values
    ├── geoid/                EGM96 15′ and EGM2008 2.5′ grids clipped to Iran (+ buffer)
    ├── profiles/             base.yaml; deposit/*.yaml (9 deposit types); examples
    ├── dictionaries/         field synonyms; analyte and method catalogue; lithology/alteration seeds; CRM seeds
    ├── export_profiles/      leapfrog.yaml, datamine.yaml, micromine.yaml, surpac.yaml, vulcan.yaml, generic.yaml
    ├── report/               branding placeholders; DOCX reference templates (fa, en)
    ├── js/                   plotly.min.js (pinned); dashboard.js (vanilla, no framework)
    └── licences/             third-party notices (generated at build)

tests/                        (repository root; not shipped)
├── unit/                     per module
├── rules/                    one test module per rule; driven by the synth ground-truth manifest
├── property/                 hypothesis tests (interval algebra, desurvey invariants, fingerprints)
├── regression/               anonymised real database + golden outputs (issue counts, fingerprints, scores)
├── gui/                      pytest-qt
├── bench/                    pytest-benchmark on synthetic S/M/L datasets
└── packaging/                smoke tests on the installed build
```

### 2.2 Layering and dependency rules
The rules below are enforced in CI by `import-linter` contracts. A violation fails the build.

```
   gui ─┐
        ├─► api ─► report ─► plots ─► analysis ─► core
   cli ─┘     │      │                   ▲          ▲
              │      ├─► scoring ─► rules┘          │
              │      └─► rules                      │
              ├─► io, mapping ──────────────────────┘
              └─► synth ─► io, core
```

- `core` imports nothing from `geovalid_pro`.
- `analysis` never imports `rules`. Products are computed independently of who consumes them.
- `rules` never imports `report`, `plots` or Qt.
- `plots` never imports `rules` or `report`.
- Nothing imports `gui`. `cli` imports `api` only (plus `core` types).
- `report.pdf` is the only engine module that imports `PySide6`, and it imports only `QtCore`, `QtGui`, `QtWebEngineCore` and `QtPrintSupport`.
- Heavy optional modules (`pyvista`, `vtk`, `pyodbc`) are imported lazily inside the functions that need them, so a missing component degrades one feature and not the application.

---

## 3. Technology stack

### 3.1 Stack table
Version floors are the minimum supported versions. The build uses an exact, hash-pinned lock file (`uv.lock`), and every release records `dependency_lock_sha256` (02 §5.9). Licences are re-verified by an automated audit on every build (§3.10).

| Library | Floor | Purpose in GEOVALID PRO | Licence | Windows packaging notes |
|---|---|---|---|---|
| **Runtime and UI** | | | | |
| CPython | 3.12 (3.11+ supported) | Runtime | PSF-2.0 | Bundled from the python.org x64 build |
| PySide6 (Essentials + Addons), shiboken6 | 6.8 (LTS) | GUI; **Qt WebEngine (PDF)**; QtPdf (in-app PDF preview); QtSvg | **LGPL-3.0** | One-dir keeps the Qt DLLs replaceable (LGPL relinking). **GPL-only modules are excluded and import-banned** (§3.10). `QtWebEngineProcess.exe`, ICU data and `.pak` resources come through the PyInstaller hook. WebEngine locales are trimmed to `en-US` and `fa`. |
| pyqtgraph | 0.13.7 | Interactive map, section and strip log; issue overlays | MIT | Pure Python |
| pyvista, pyvistaqt, vtk | 0.44 / 0.11 / 9.3 | **Optional** 3D viewer (Phase 5) | MIT / MIT / BSD-3 | Separate installer component (~230 MB unpacked). Imported lazily. |
| **Data** | | | | |
| numpy | 2.0 | Arrays, vectorised kernels | BSD-3 | OpenBLAS DLL is inside the wheel |
| pandas | 2.2 (Copy-on-Write on; 3.x tested) | In-memory tables for rules and analysis | BSD-3 | — |
| pyarrow | 17 | Parquet I/O, Arrow memory, compute kernels, Arrow-backed strings | Apache-2.0 | Large (~100 MB). Unused Arrow DLLs (Flight, Substrait) are excluded after an import-graph check. |
| duckdb | 1.1 | Set-based operations: wide pivot, version diff, assay joins, issue aggregation (§3.4) | MIT | One extension module. **Extension auto-install and auto-load are disabled.** |
| scipy | 1.13 | KD-tree, Delaunay, Voronoi, interpolation, statistics, linear assignment | BSD-3 | Bundles OpenBLAS and libgfortran (GCC runtime exception) |
| statsmodels | 0.14.2 | ANOVA, regression diagnostics, robust statistics | BSD-3 | — |
| scikit-learn | 1.5 | **Only** `GaussianMixture` (log-population decomposition, unit-mix detection) and `MinCovDet` (robust multivariate outliers) | BSD-3 | ~40 MB; includes the OpenMP runtime |
| pydantic | 2.7 | Rule parameter schemas, profile validation, JSON Schema → GUI forms | MIT | Rust core |
| ruamel.yaml | 0.18 | Round-trip YAML profiles (comments preserved when the GUI edits a profile) | MIT | — |
| rapidfuzz | 3.9 | Fuzzy header and code matching | MIT | C++ extension |
| psutil | 5.9 | Memory-budget monitor; process control | BSD-3 | — |
| platformdirs | 4.2 | Per-user data, cache and log folders | MIT | — |
| **Input** | | | | |
| charset-normalizer | 3.3 | Encoding candidates for N01 (combined with the Persian heuristics of 02 §6.1) | MIT | chardet is rejected (LGPL, weaker on cp1256) |
| python-calamine | 0.2 | Fast cell values from XLSX/XLSM/XLSB/XLS/ODS (≈ 10× openpyxl) | MIT | Rust extension |
| openpyxl | 3.1 | XLSX number formats (decimals for 02 `precision_source = EXCEL_FORMAT`), the `date1904` flag | MIT | Uses defusedxml automatically when present |
| xlrd | 2.0 | Legacy XLS number formats (XF records) | BSD-3 | — |
| defusedxml | 0.7 | XML hardening (XLSX, KML, DOCX templates) | PSF-2.0 | — |
| dbfread | 2.0 | DBF, with code page from LDID/.cpg | MIT | Pure Python |
| pyodbc | 5.1 | Access through the ACE driver; SQL Server and PostgreSQL through user-installed ODBC drivers | MIT | **Drivers are not bundled.** The ACE x64 redistributable is an optional installer component (§14.3). |
| access-parser | pinned commit, **vendored** | Pure-Python read-only MDB/ACCDB fallback | Apache-2.0 | Vendored in `_vendor/` with our fixes and tests (§3.5) |
| laspy + lazrs | 2.5 / 0.6 | LAS/LAZ point clouds | BSD-2 / MIT | lazrs is chosen over the LASzip binding (LGPL) |
| ezdxf | 1.3 | DXF: 3DFACE, MESH, POLYFACE, 2D/3D polylines with elevation, points | MIT | Pure Python |
| trimesh | 4.4 | OBJ/STL/PLY meshes | MIT | Installed without optional extras |
| **GIS** | | | | |
| pyproj | 3.7 | CRS, transformations, grid convergence, geoid heights | MIT (PROJ: MIT) | Ships `proj.db`. **Network disabled.** Geoid grids are bundled in `resources/geoid`. |
| shapely | 2.0 | Vectorised predicates, STRtree, Voronoi polygons, overlays | BSD-3 (GEOS: **LGPL-2.1**) | GEOS is a separate DLL (relinkable) |
| geopandas | 1.0 | GeoDataFrame for spatial layers | BSD-3 | pyogrio is the default engine in 1.x |
| pyogrio | 0.9 | Vector I/O through GDAL | MIT (GDAL: MIT) | Vendored GDAL with delvewheel-mangled DLL names |
| rasterio | 1.4 | Raster I/O, windows, sampling, COG writing | BSD-3 (GDAL) | Its own vendored GDAL. Coexistence with pyogrio's GDAL is verified in S-12. |
| **Plots** | | | | |
| matplotlib | 3.9 | All static figures (report, GUI charts) | Matplotlib licence (PSF-style, BSD-compatible) | The font cache is pre-built at build time, so first start does not stall |
| mplstereonet | 0.6 | Stereonets, rose diagrams | MIT | Small; vendored if it goes unmaintained |
| matplotlib-scalebar | 0.8 | Map scale bars | BSD-2 | — |
| plotly | 5.24 (6.x tested) | Interactive figures in the HTML dashboard | MIT | `plotly.min.js` is embedded once per HTML file. **No CDN.** |
| arabic-reshaper | 3.0 | Persian contextual glyph shaping for matplotlib | MIT | — |
| python-bidi | 0.5 | Unicode bidi reordering for matplotlib | **LGPL-3.0** | Kept as a separate, replaceable module (one-dir) |
| **Reports** | | | | |
| Jinja2 | 3.1.4 | HTML templates (print and dashboard) | BSD-3 | — |
| python-docx (+ lxml) | 1.1 | DOCX builder | MIT (lxml: BSD-3) | — |
| XlsxWriter | 3.2 | Issue log and pivot sheets; cleaned-database XLSX | BSD-2 | `constant_memory` mode for large logs |
| pypdf | 5.0 | PDF post-processing: header/footer overlay, page "n / N", outline, TOC pass | BSD-3 | Pure Python |
| Qt WebEngine (in PySide6) | — | HTML → PDF (§3.2) | LGPL-3.0 | see PySide6 |
| Vazirmatn, Inter | 33.003 / 4.0 | Fonts | OFL-1.1 | Bundled as TTF and WOFF2 |
| **CLI, build, test** | | | | |
| click | 8.1 | CLI | BSD-3 | — |
| PyInstaller | 6.10 | Freezing (one-dir) | GPL-2.0 **with bootloader exception** | The exception means the frozen application's licence is unaffected |
| Inno Setup | 6.3 | Windows installer | Inno Setup licence (free, commercial use allowed) | Build machine only |
| uv | 0.4 | Lock file, reproducible environments | MIT / Apache-2.0 | Build machine only |
| pytest, pytest-qt, hypothesis, pytest-benchmark, ruff, mypy, import-linter, pip-licenses, cyclonedx-py | current | Tests, lint, types, layering, licence audit, SBOM | permissive | Development only; never shipped |
| *Test oracles only:* esda, ppigrf, jdatetime | current | Cross-checks for local Moran's I, IGRF and Jalali conversion | BSD / MIT / PSF | Development only |

### 3.2 Decision D1: PDF engine = Qt WebEngine `printToPdf`
**Requirement.** The PDF must have correct Persian shaping, RTL paragraphs, mixed fa/en lines and embedded fonts. It must be the same content as the HTML report, built offline and headless in CI, and packageable on Windows without native dependency trouble.

| Criterion | **Qt WebEngine** (chosen) | WeasyPrint | ReportLab | LibreOffice (DOCX→PDF) | Typst (runner-up) |
|---|---|---|---|---|---|
| Persian shaping and bidi | **Chromium/HarfBuzz/ICU: correct**, including mixed runs | Correct (Pango) | Weak. Experimental HarfBuzz shaping; poor justified bidi paragraphs | Correct | Correct (rustybuzz) |
| Same template as the HTML report | **Yes** | Yes | No (separate flowable layout) | No (DOCX only) | No (third template language) |
| Windows packaging | **Already in the bundle (Qt), zero extra** | Needs a Pango/GLib/HarfBuzz/fontconfig runtime (MSYS2/GTK DLLs), which is fragile under PyInstaller | Easy | ~300 MB external install; cannot be bundled sensibly | Easy (~30 MB wheel) |
| Headless/CI | Yes, with `QT_QPA_PLATFORM=offscreen` (verified in S-01) | Yes | Yes | Yes | Yes |
| Running headers, page "n / N", TOC page numbers | **Not native.** Solved by overlay + two-pass (below) | Native (CSS Paged Media) | Native | Native | Native |
| Vector figures | Yes (SVG in HTML) | Yes | Yes | EMF/PNG | Yes |
| Licence | LGPL-3.0 | BSD | BSD (open-source edition) | MPL-2.0 | Apache-2.0 |

**Decision.** Qt WebEngine. It is the only option that gives correct Persian with the *same* template at *zero* packaging cost, using the shaping engine Iranian users already see in Chrome. The weakness is paged-media furniture, which is solved in ~300 lines:

1. **Render.** The print HTML is written to a temporary file and loaded with `QWebEnginePage.load(QUrl.fromLocalFile(...))`. `setHtml()` is not used because it has a 2 MB limit. The renderer waits for `loadFinished`, then for `document.fonts.ready` through `runJavaScript`, then calls `printToPdf(path, QPageLayout(A4, portrait|landscape, margins))`, which signals `pdfPrintingFinished`.
2. **Two-pass TOC.** Every heading carries an invisible marker token. Pass 1 renders, and pypdf text extraction finds each marker's page. Pass 2 renders with TOC page numbers filled in. The TOC uses a fixed-width number column, so pass 2 cannot shift pagination. Internal anchor links remain clickable.
3. **Header/footer overlay.** A per-page overlay PDF is drawn with `QPdfWriter` + `QPainter`. Qt's text engine also shapes with HarfBuzz, so Persian is correct here too. The overlay carries the logo, report title, release ID, "صفحه ۷ از ۱۲۰" / "Page 7 of 120", and the DRAFT watermark when applicable. It is merged with `pypdf` (`page.merge_page`), and the PDF outline (bookmarks) is added from the pass-1 marker positions.
4. **Fonts.** `@font-face` points at bundled WOFF2 through `file://` URLs. Chromium subsets and embeds them.
5. **Offline.** A `QWebEngineUrlRequestInterceptor` allows only the `file:`, `data:` and `qrc:` schemes and blocks everything else. JavaScript is not needed for print HTML and is disabled in the print profile.
6. **Headless.** `QT_QPA_PLATFORM=offscreen` and `--disable-gpu`. On Linux containers run as root, `QTWEBENGINE_DISABLE_SANDBOX=1` is set. The required apt packages are listed in the CI image.

**Contingency.** Some PySide6 versions ship Chromium ≥ 131, which supports CSS `@page` margin boxes. If S-01 confirms margin boxes in the pinned version, step 3 becomes pure CSS and the overlay is retired. If S-01 fails on Persian or headless operation, the fallback is a Typst backend fed from the same Report Document Model (§9.2); only the template layer changes.

### 3.3 Decision D2: GIS I/O
- **pyogrio, not fiona.** pyogrio reads and writes whole layers to and from Arrow/NumPy in bulk, 5–20× faster than fiona's per-feature iteration. It is the default engine of geopandas 1.x and halves the number of GDAL-bearing wheels in the bundle. fiona is not shipped.
- **rasterio** is kept for rasters: windowed reads, nodata handling, COG writing and `sample()`. Collar sampling is done with our own vectorised bilinear interpolation (`scipy.ndimage.map_coordinates`, order 1, nodata-aware) on a window read, so that nodata and edge behaviour are explicit.
- **Two vendored GDALs** (pyogrio's and rasterio's) coexist because delvewheel mangles their DLL names. The cost is ~60–80 MB. S-12 verifies the drivers we rely on: GPKG, ESRI Shapefile, KML (+ `/vsizip/` for KMZ), GeoJSON, OpenFileGDB, GTiff, AAIGrid, SRTMHGT. It also verifies **Unicode (Persian) file paths**, which are common on client machines.
- **ezdxf instead of GDAL's DXF driver.** GDAL flattens DXF into a generic layer and loses 3DFACE/MESH topology and elevation semantics. ezdxf gives direct access to entity types, elevation and layers, which TIN building from contours and faces needs.
- **shapely 2** vectorised operations (`contains_xy`, `distance`, `STRtree.query`) handle collar-in-licence, distance to licence edge and map contact, and map-unit lookup for 5 000 collars in milliseconds. `shapely.voronoi_polygons` + `intersection` gives Voronoi areas clipped to the licence or project extent. SciPy's Voronoi is not used for areas because of its unbounded cells.
- **geopandas** is the container for spatial layers in the API and for GIS exports. Rules receive plain NumPy coordinates, not GeoDataFrames.
- **DEM building.** Contours and points → **Delaunay TIN** (default). Collars are sampled directly on the TIN by barycentric interpolation, with no gridding loss. Where a grid is needed (slope, hillshade, export), it is built by **natural-neighbour (Sibson)** interpolation, vendored from MetPy's BSD-3 algorithm. The proportion of **flat triangles** (all three vertices on one contour: terracing) and the leave-one-out RMSE (02 `interp_rmse_m`) are reported as surface-quality metrics.

### 3.4 Decision D3: pandas + pyarrow baseline; DuckDB for four named operations; no Polars
- **The single in-memory API is pandas** on Arrow-backed dtypes: `string[pyarrow]` for text, categoricals for codes, `float64` for depths and values (never downcast), and `int32`/`int64` surrogate keys for joins. The rule contract returns pandas (§5.2). Copy-on-Write semantics mean a rule cannot mutate a shared frame.
- At the target scale (1 M interval rows across tables, ~25 columns), a table is 150–250 MB in memory. pandas handles this comfortably when columns are projected and operations are vectorised.
- **DuckDB** (in-process, MIT, ~25 MB) is used **only** behind `core.query`, for:
  1. the long → wide assay pivot with preferred values (`drv_assay_wide`). 300 k samples × 60 analytes is 18 M long rows, and DuckDB does this out of core;
  2. **version diffs** (VER), which are full outer joins of two versions on natural keys at millions of rows;
  3. **assay-long joins** with sample, batch and CRM tables for QA/QC rules;
  4. **issue aggregation and filtering** for the dashboard, pivots and the review panel (over Arrow, zero-copy).

  DuckDB reads the hash-verified Parquet files in the cache directly and returns Arrow. Configuration: `autoinstall_known_extensions=false`, `autoload_known_extensions=false`, `memory_limit` = 25 % of RAM, `temp_directory` in the cache, `threads` = physical cores. The configuration is then locked (`lock_configuration=true`).
- **Polars is rejected.** It would be a third tabular API next to pandas and Arrow. The scientific stack (statsmodels, geopandas, matplotlib) expects pandas, and DuckDB already covers the out-of-core cases.
- **Numba is rejected.** It adds ~100 MB of LLVM, JIT warm-up at every start, and PyInstaller cache problems. No kernel in this design needs it.

### 3.5 Decision D4: MS Access (MDB/ACCDB): tiered reader
0. **Copy first.** The source is copied to a temporary local ASCII path, hashed, and opened read-only from there. This guarantees the original is never touched: ACE creates `.laccdb` lock files and can fail on read-only network shares and Persian folder names.
1. **Tier 1: ACE ODBC through pyodbc.** Used when `pyodbc.drivers()` lists `Microsoft Access Driver (*.mdb, *.accdb)`. Only drivers of the process bitness are listed, so a listed driver is x64.
   - Connection: `DBQ=<copy>;ReadOnly=1;Exclusive=0`.
   - Tables are read with chunked `SELECT *`. Saved queries are offered as optional sources.
   - Full fidelity for types, Unicode and encrypted databases (password prompt).
   - Access `Double` fields do not carry display decimals through ODBC (the `DecimalPlaces` field property is DAO-only). Collar decimals from Access are therefore recorded as `precision_source = FLOAT_REPR` and down-weighted in the collar-method inference (§6.10).
2. **Tier 2: access-parser (pure Python, vendored).** Used automatically when ACE is absent, or when Office 32-bit blocks the x64 ACE install. It reads Jet 3 (Access 97, code page from the database header, e.g. cp1256), Jet 4 and ACE.
   - Limitations: no encrypted databases, no attachment/OLE/multi-value fields. These limitations are irrelevant for drillhole tables.
   - Self-check: the parsed row count is compared with the row count in each table definition (TDEF). A mismatch is an `IMP-*` ERROR, and the table is still imported.
   - Slower (~3× tier 1) but adequate.
3. **Tier 3: guided CSV export.** The GUI shows step-by-step export instructions. CSV is always supported.

Which tier was used is recorded in `source_file` evidence and in the run metadata. S-04 validates tier 2 against tier 1 on the client's corpus, cell by cell.

### 3.6 Decision D5: Proprietary software formats: feasibility and plan

| Format | Public specification | Feasibility | Plan | Fallback |
|---|---|---|---|---|
| **Surpac `.str`** (ASCII) | De facto public: header line, axis line, records `string, Y, X, Z, D1…` (**Y before X**), segment end `0,0,0,0`, file end `0, 0.000, 0.000, 0.000, END` | High | Reader and writer implemented (collars, traces, contours, boundaries). Binary `.str` is detected and refused with a "save as text" message. | — |
| **Surpac `.dtm`** (ASCII) | De facto public: references its `.str` for points; triangle records with neighbours | High | Reader implemented (topography). The companion `.str` is required and checked. | DXF/OBJ export from Surpac |
| Surpac database | Usually Access, SQL Server or ODBC | — | Covered by §3.5 and `io.readers.sql` | CSV |
| **Datamine `.dm`** (binary; single and extended precision) | **None published.** Partial community descriptions exist (page-structured file, field table with 8-character names, A/N types, numeric absent value −1.0E+30, trace value +1.0E−30). | Medium. Reverse engineering, with risk of variants. | **Spike S-05 (4 days).** Corpus of ≥ 10 client files exported from Studio RM/EM, each with a CSV twin. Acceptance: 100 % cell equality, absent → NULL, trace → `BDL`. A pass enables `.dm` read (wireframe `_tr`/`_pt` pairs follow), and `.dm` write is a separate decision. | Datamine CSV export (always supported) |
| **Micromine `.DAT`** (binary) | **None published.** A header with field definitions (name, type, width, decimals) followed by fixed-length records is generally described. | Medium | **Spike S-06 (3 days)** with the same acceptance protocol | Micromine Text/CSV export |
| Leapfrog Geo | Native `.lfproj`/`.msh` are proprietary | Not attempted | CSV exports (collar, survey, intervals) through `presets.py`; meshes through OBJ/DXF/STL exports | — |
| acQuire, MX Deposit | Server or cloud data models vary by site and licence | Not attempted directly | Export **presets** (column templates) for their CSV/XLSX exports | — |
| Vulcan `.00t`, ISIS | Proprietary binary | Not attempted | DXF/OBJ for triangulations; CSV for ISIS exports | — |

### 3.7 Decision D6: Magnetic declination and grid convergence (offline)
- **Model.** Own implementation of the spherical-harmonic synthesis in `core/geomag.py` (~150 lines of NumPy):
  - inputs: the official **IGRF-14** coefficient file (DGRF 1900–2020, IGRF 2025, secular variation 2025–2030) and **WMM2025** (`WMM.COF`), both in `resources/geomag`;
  - method: geodetic → geocentric conversion (WGS 84), Schmidt semi-normalised associated Legendre recursion, then X, Y, Z → declination `D = atan2(Y, X)`, inclination and total field;
  - time handling: linear interpolation between epochs, and secular-variation extrapolation to 2030. A date beyond the model validity raises a WARNING.
- **Why our own implementation.** The available packages (ppigrf, pyIGRF, pygeomag) are small and sporadically maintained. Owning ~150 tested lines means IGRF-15 (expected around 2030) is a data-file swap, not a dependency upgrade. ppigrf is a test oracle. The test suite includes ~50 reference values from the BGS and NOAA calculators at Iranian locations, 1970–2029. Tolerance: 0.01° against the published model; this checks the code, not the model's accuracy.
- **Model accuracy is reported honestly.** Main-field models do not contain crustal anomalies, and near magnetite skarns or ultramafics local declination can differ by degrees. That is exactly what `SUR-013`/`SUR-014` look for, using the EMS-reported total field against IGRF (02 `mag_field_nt`).
- **Date used.** `survey_date`, falling back to the collar completion date, then the campaign start, then the project default. Every fallback is evidence on the `AZ_REFERENCE` inference.
- **Override.** `project.declination_override_deg` (02 §4.1) replaces the model for the whole project, and the report states it.
- **Grid convergence.** pyproj `Proj.get_factors(lon, lat).meridian_convergence`, computed **per collar**. A unit test checks the sign against the closed-form UTM expression `γ ≈ atan(tan(λ − λ₀)·sin φ)` (positive east of the central meridian in the northern hemisphere, as 02 §4.4 defines). Then `azimuth_true = az_mag + δ` and `azimuth_grid = azimuth_true − γ`. Desurvey always uses `azimuth_grid`.
- **Scale factor.** Downhole lengths are ground lengths and are not scaled to grid. The error is below 0.04 % of horizontal displacement in UTM. This is stated in the method notes.

### 3.8 Decision D7: Persian and RTL text, fonts, offline plotly

| Output | Mechanism |
|---|---|
| **matplotlib** (PNG/SVG) | `plots.text.fa()`: wrap the *logical* string to the target width first. Then, **per line**, apply `arabic_reshaper.reshape` (Persian configuration, ligatures on) and `bidi.get_display(base_dir="R")`. Reordering a multi-line string as one block scrambles line order, which is a classic bug. Strings without Arabic-script characters pass through untouched. Font family list: `["Vazirmatn", "Inter", "DejaVu Sans"]` for fa figures and `["Inter", "Vazirmatn", "DejaVu Sans"]` for en, using matplotlib's per-glyph font fallback. SVG uses `svg.fonttype = "path"`, so it renders identically everywhere. **S-02** verifies that Vazirmatn covers every presentation form the reshaper emits (U+FB50–FDFF, U+FE70–FEFF, including پ چ ژ گ). If upstream matplotlib adopts complex text layout, the reshaper step is removed behind the same `fa()` helper. |
| **DOCX** | Styles live in a Word-authored reference template (`resources/report/reference_fa.dotx`, `reference_en.dotx`), so the client can restyle without code changes. Per paragraph: `w:pPr/w:bidi`. Per run: `w:rPr/w:rtl`, `w:rFonts w:ascii="Inter" w:hAnsi="Inter" w:cs="Vazirmatn"`, `w:szCs`, `w:lang w:bidi="fa-IR"`, and `w:cs` where complex-script formatting must apply. Tables: `w:tblPr/w:bidiVisual`. Sections: `w:sectPr/w:bidi` + `w:rtlGutter`. Latin hole IDs, rule IDs and formulas are separate LTR runs. **Fonts are embedded** (obfuscated embedded-font parts as defined in ECMA-376 Part 1 for WordprocessingML fonts, permitted by OFL), so the report renders on PCs without Vazirmatn. Figures are inserted as 300-dpi PNG. Captions use `SEQ` fields and the TOC is a field, so Word can regenerate both (`w:updateFields` is set). **S-03** verifies the result in Word 2016/2019/365 and LibreOffice. |
| **HTML / PDF** | `<html lang="fa" dir="rtl">`. CSS uses logical properties (`margin-inline-start`, `text-align: start`). IDs sit in `<bdi>` or `<span dir="ltr">`. Fonts are `@font-face` WOFF2 subsets embedded as data URIs in the dashboard and as files for print. `font-variant-numeric: tabular-nums` aligns numeric columns. |
| **Digits and separators** | The i18n layer emits Persian digits (U+06F0–U+06F9), momayyez `٫` (U+066B), `٬` (U+066C) and `٪` (U+066A) in fa prose, tables and axis ticks. The font or CSS is never relied on for this. **Latin digits are kept** in hole and sample IDs, rule IDs, EPSG codes, chemical formulas and map/section coordinate ticks, so they can be transcribed unambiguously. This is a profile setting (`report.fa_digits`); the default is as stated. |
| **Bidi isolates in messages** | Interpolated IDs in fa messages are wrapped in U+2066 LRI … U+2069 PDI. Without this, `BH-01` inside a Persian sentence renders as `01-BH`. |
| **plotly (offline)** | `plotly.min.js` from the pinned package is embedded **once** per HTML file (`include_plotlyjs=False` per figure). There are no CDN or MathJax references and `displaylogo` is off. The browser shapes Persian in plotly's SVG text natively, so the reshaper is not used there. |
| **Qt UI** | `QFontDatabase.addApplicationFont` for both fonts. Vazirmatn is the application font in fa and Inter in en. `QLocale(QLocale.Persian, QLocale.Iran)` for UI number formatting. |
| **Fonts** | **Vazirmatn** (OFL-1.1): a complete Persian character set, Latin glyphs designed to match, and many weights. **Inter** (OFL-1.1) is chosen over Source Sans 3 for its tabular figures and screen legibility in dense tables. Both are bundled as TTF (matplotlib, Qt, DOCX embedding) and WOFF2 (HTML). The OFL texts ship in `resources/licences`. |

### 3.9 Decision D8: Tabular readers
- **CSV/TXT.** charset-normalizer candidates combined with the 02 N01 Persian and mojibake heuristics. The delimiter is chosen by field-count consistency over the first 500 lines for `, ; \t | space`, with `csv.Sniffer` as a tie-breaker. Every cell is read as text (`dtype=str`, `keep_default_na=False`) because the raw snapshot stores text (02 §1.3). Fixed-width files are detected by column alignment.
- **Excel.** python-calamine reads values for all formats. openpyxl in read-only mode samples cell number formats (decimals) and reads `workbookPr/@date1904`. Merged header ranges are read directly from the sheet XML `<mergeCells>` element; openpyxl's read-only mode does not expose them. Hole IDs are read from the formatted text, never the numeric value (02 N12). Hidden sheets and rows are imported and flagged.
- **DBF.** dbfread with the code page taken from LDID or `.cpg`, falling back to cp1256 for Persian content.
- **SQL (SQLite, SQL Server, PostgreSQL).** The user picks tables or views and the import runs as a read-only `SELECT`. Connection strings are stored without passwords.

### 3.10 Decision D9: Licence policy
- **Allowed:** MIT, BSD, Apache-2.0, PSF, ISC, Zlib, MPL-2.0 (file-level copyleft, unmodified), OFL-1.1 (fonts), and **LGPL (dynamically loaded, unmodified, replaceable)**.
- **Banned:** GPL (any version), AGPL, SSPL, and non-commercial licences.
- **Enforcement.** `pip-licenses` runs against an allow-list in CI and fails the build on any violation. A CycloneDX SBOM ships with every release. Third-party notices are generated into `resources/licences`.
- **LGPL obligations** (Qt/PySide6, shiboken6, GEOS, python-bidi):
  - the one-dir layout keeps each library a separate, replaceable file;
  - nothing is statically linked;
  - the licence texts and a pointer to the corresponding sources ship with the product;
  - the end-user licence agreement does not forbid reverse engineering for debugging the replaced libraries (LGPL-3 §4).
- **PyQt is rejected.** PyQt6 is GPL-3.0 or commercial; PySide6 is LGPL.
- **Qt modules that are GPL-only** in the open-source offering are excluded from the bundle and import-banned (ruff `banned-api` + import-linter): **Qt Charts, Qt Data Visualization, Qt Graphs, Qt Quick 3D, Qt Virtual Keyboard** (the list is re-checked against the Qt licensing page for the pinned version). Dashboard gauges are therefore custom-painted with `QPainter`, and all charts are pyqtgraph or matplotlib.

### 3.11 Decision D10: Rejected libraries (summary)

| Library | Reason |
|---|---|
| WeasyPrint | Pango/GTK runtime on Windows, fragile under PyInstaller (D1) |
| ReportLab | Weak Persian shaping; a second layout system (D1) |
| fiona | Superseded by pyogrio for bulk I/O; one GDAL copy fewer (D2) |
| Polars | A third tabular API (D3) |
| Numba | Size, JIT warm-up, freezing problems (D3) |
| PyQt6 | GPL-3.0 (D9) |
| chardet | LGPL; weaker cp1256 detection (D8) |
| simplekml | LGPL; KML/KMZ is written through GDAL instead |
| kaleido | Version 1.x needs an installed Chrome. Static figures come from matplotlib instead. |
| mdbtools | GPL utilities (D4) |
| Any LLM or online service | Offline requirement (§13.1); narrative is deterministic (§9.4) |

---

## 4. Project container and data access

### 4.1 The `.gvp` file
The container is the one fixed in 02 §8: **one SQLite 3 file** holding the system and reference tables as rows and every bulk table as **content-addressed Parquet blobs** (02 §5.11). The physical details governed here:

| Item | Setting | Reason |
|---|---|---|
| SQLite pragmas | `application_id` = `0x47565030` ("GVP0"); `user_version` = schema version; `page_size = 65536`; `journal_mode = WAL` while open; `synchronous = NORMAL` for routine writes and `FULL` around change-set apply, release and migration; `foreign_keys = ON`; `busy_timeout = 10000` | Large pages suit blob chunks. WAL allows the GUI to read while its worker writes. FULL durability where it matters. |
| Blob chunks | ≤ 64 MiB per `blob_chunk` row, streamed with `Connection.blobopen` | Stays far below SQLite's 1 GB value limit. Constant memory on write and extract. |
| Parquet | zstd level 3; dictionary encoding for codes and IDs; row groups of 128 k rows; stable sort by `(hole_id, from_m/depth_m, row_uid)` (assay: `(analyte_code, hole_id, from_m)`, 02 §1.4); Parquet statistics on; no wall-clock timestamps inside files | Byte-identical output for identical input (02 §1.10). Row-group pruning on hole and analyte. |
| Partitions (`table_manifest.part`) | `assay`: **one part per analyte**. Other tables: one part per ≤ 2 M rows. | A change set touching Cu rewrites only the Cu part. Per-analyte rules read one part. |
| Column hashes | SHA-256 per column (of its Arrow IPC buffer) stored in the Parquet key-value metadata `geovalid.column_sha256`, and loaded into memory on open | Column-precise invalidation of derived products and rule results (§5.4.4, §6.1) without extra system tables |
| Sources | Embedded up to `schema.storage.embed_max_mb` (02 §8); larger files are external and re-hashed on open | 02 §8 |
| Snapshots, "Save as" | `VACUUM INTO` | Consistent copy even while open |

### 4.2 Working cache (disposable)
- Location: `%LOCALAPPDATA%\geovalid_pro\cache\<project_uid>\` (Linux: `$XDG_CACHE_HOME/geovalid_pro/…`).
- **L2 files:** `<sha256>.parquet` blobs, extracted on first use and **verified by hash at extraction**. pyarrow reads them memory-mapped and DuckDB scans them directly.
- **Derived products and rule-result frames** are also written here (Parquet), keyed by product or result key (§5.4.4, §6.1).
- LRU eviction above a size cap (default 20 GB or 10 % of free disk, whichever is smaller). Deleting the cache loses nothing; it is rebuilt.
- The cache is never the source of truth. On release, the products used by exports and reports are copied into the `.gvp` (L3), so a release reproduces byte-identically even after a software upgrade.

### 4.3 Data access
All reads go through `ProjectStore.read_table(table, version_id, columns, filters)` (02 §8), which returns Arrow. `core.store` adds a pandas view with a fixed dtype policy:

| Data | In-memory dtype | Note |
|---|---|---|
| Depths, coordinates, values | `float64` | Never downcast. Depth comparisons use `schema.depth_eps_m`. |
| Surrogate keys (`row_uid`, `hole_uid`, `sample_uid`) | `int64` / `int32` | All joins use these |
| `hole_id`, `sample_id`, free text, `*_raw` | `string[pyarrow]` | Display and messages |
| Codes, enums | `category` (from Arrow dictionary) | Categories are sorted for determinism |
| Dates | `datetime64[ns]` (UTC) | — |

**Column projection is mandatory.** `ctx.table()` without `columns=` raises an error, which keeps memory proportional to what a rule actually uses.

### 4.4 Locking and concurrency
- **One writing application instance per project.** An OS file lock on `<name>.gvp.lock` (PID, user, host, start time) plus a `project_lock` row.
- A second instance, or a project on a read-only medium, opens **read-only** with a banner.
- A stale lock (dead PID on the same host) is offered for takeover. A lock from another host is never taken over silently.
- Inside the writing instance, the GUI and its worker subprocess interleave **short** write transactions under WAL (§1.4).
- **Network drives.** SQLite locking over SMB is unreliable. A project opened from a UNC path or a network-mapped drive (`GetDriveTypeW`) triggers a recommendation to work on a local copy. Read-only opening remains available.

---

## 5. Rule engine

### 5.1 Concepts

| Term | Meaning |
|---|---|
| **Rule** | A class with metadata (`RuleMeta`), a typed parameter model (`Params`), bilingual message templates and a vectorised `check()`. Optionally `propose_fix()`. |
| **RuleTask** | One rule bound to one table, with resolved parameters. A generic `INT-*` rule expands to one task per interval table in `table_registry` (02 §1.6), which is how "applied to EVERY interval table" is guaranteed. |
| **Product** | A derived, cached computation that rules declare in `requires` (desurvey, DEM sample, interval master, …), §6.1 |
| **IssueFrame** | The DataFrame a rule returns: one row per issue, fixed column contract (§5.3) |
| **Profile** | A resolved YAML validation profile (base → deposit type → project): enabled rules, parameters, bands, suppressions (§5.9) |
| **Rule-execution matrix** | Per run: every rule × table as `RAN`, `CACHED`, `DISABLED` (with reason), `NOT_APPLICABLE` (with the missing inputs) or `FAILED`. It is printed in the report appendix, so a clean report can never hide checks that were not run. |

### 5.2 Rule contract (signatures)

```python
# geovalid_pro/rules/base.py  — interface sketch, not an implementation
from dataclasses import dataclass
from enum import StrEnum
from typing import ClassVar, Literal, Protocol, Sequence, Any
import numpy as np, pandas as pd
from pydantic import BaseModel, ConfigDict

class Severity(StrEnum): CRITICAL = "CRITICAL"; ERROR = "ERROR"; WARNING = "WARNING"; INFO = "INFO"
class Family(StrEnum):   IMP="IMP"; COL="COL"; SUR="SUR"; INT="INT"; ASY="ASY"; QAQ="QAQ"; LIT="LIT"; GEO="GEO"; ALT="ALT"
                         MIN="MIN"; WTH="WTH"; DEN="DEN"; MAG="MAG"; STR="STR"; SMP="SMP"; CRS="CRS"; SPA="SPA"; VER="VER"
class Stage(StrEnum):    IMPORT="IMPORT"; TABLE="TABLE"; CROSS="CROSS"; SPATIAL="SPATIAL"; VERSION="VERSION"
class Scope(StrEnum):    # grain of one issue → fingerprint key form of 02 §5.5
    ROW="ROW"; MULTI_ROW="MULTI_ROW"; HOLE="HOLE"; SAMPLE="SAMPLE"; ASSAY="ASSAY"; BATCH="BATCH"; TABLE="TABLE"; PROJECT="PROJECT"

@dataclass(frozen=True)
class TableSel:
    kinds: tuple[str, ...] = ()            # table_registry.kind, e.g. ("INTERVAL", "EXT_INTERVAL")
    names: tuple[str, ...] = ()            # explicit tables, e.g. ("collar",)
    required_fields: tuple[str, ...] = ()  # task is NOT_APPLICABLE when any is absent or 100 % NULL

@dataclass(frozen=True)
class Ref:
    source: str; item: str; note: str = "" # Ref("Datamine Drillhole Importer", "Large dip curvature")

@dataclass(frozen=True)
class Bands:                               # dual (or triple) thresholds on the issue's `measure`
    direction: Literal["above", "below", "abs_above"]
    unit: str                              # "m", "deg/30m", "%"
    defaults: dict[Severity, float]        # {WARNING: 3.0, ERROR: 6.0}
    key: str | None = None                 # contextual bands, e.g. "drv_collar_method.inferred_method"

@dataclass(frozen=True)
class Messages:
    en: str; fa: str                       # str.format templates over the m_* columns
    fix_en: str | None = None; fix_fa: str | None = None
    version: int = 1                       # templates are versioned; old versions are kept

@dataclass(frozen=True)
class RuleMeta:
    rule_id: str                           # "INT-002"
    family: Family
    tables: TableSel
    title_en: str; title_fa: str
    description_en: str; description_fa: str
    severity: Severity                     # default severity (lowest band when banded)
    scope: Scope = Scope.ROW
    bands: Bands | None = None
    reference: tuple[Ref, ...] = ()        # software/standard mirrored (brief §1.3 'reference')
    jorc_items: tuple[str, ...] = ()       # "T1.01" … "T1.12"
    ni43101_items: tuple[str, ...] = ()    # "11", "12"
    requires: tuple[str, ...] = ()         # products, e.g. ("drv_trace", "drv_collar_spatial")
    stage: Stage = Stage.TABLE
    version: int = 1                       # bump on any logic change → invalidates cached results
    brief_ref: str = ""                    # "§5", used by 05_traceability

class RuleParams(BaseModel):               # subclass per rule; unknown keys are a profile error
    model_config = ConfigDict(extra="forbid", frozen=True)

def P(default: Any, *, unit: str | None = None, ge: float | None = None, le: float | None = None,
      en: str = "", fa: str = "", choices: Sequence[Any] | None = None) -> Any:
    """Parameter field: default + unit + range + bilingual label (pydantic Field + JSON-schema extras).
    The GUI generates its threshold editor from this schema; the report appendix prints it."""

class RuleContext(Protocol):
    run_id: str
    version_id: str                        # dataset version under validation (WORKING or RELEASE)
    table_name: str | None                 # current table of a multi-table task
    def table(self, name: str | None = None, *, columns: Sequence[str],
              where: Sequence[tuple] | None = None, active_only: bool = True) -> pd.DataFrame: ...
    def product(self, name: str, **variant: Any) -> Any: ...     # must be declared in meta.requires
    def dictionary(self, domain: str) -> "CodeDictionary": ...
    def registry(self) -> "TableRegistry": ...
    def setting(self, path: str) -> Any: ...                     # resolved profile value, e.g. "schema.depth_eps_m"
    def rng(self) -> np.random.Generator: ...                    # seeded: hash(run.random_seed, rule_id, table)
    cancel: "CancelToken"; progress: "ProgressSink"

class Rule:
    meta: ClassVar[RuleMeta]
    Params: ClassVar[type[RuleParams]] = RuleParams
    messages: ClassVar[Messages]

    def check(self, ctx: RuleContext, p: RuleParams) -> pd.DataFrame:
        """Vectorised. Returns an IssueFrame (§5.3). Must not mutate inputs or write anything."""
        raise NotImplementedError

    def propose_fix(self, issues: pd.DataFrame, ctx: RuleContext, p: RuleParams) -> pd.DataFrame | None:
        """Optional and vectorised over the rule's own issues. Returns a FixFrame aligned on issues.index:
        a list of proposed changes per issue (op, table, row_uid, natural_key, field, old, new, why).
        Stored as issue_context.fix_json; becomes a DRAFT change set only on reviewer action."""
        return None
```

`ctx` **records every (table, column) a task reads.** The record feeds the result-cache key (§5.4.4) and the traceability matrix ("which data did this rule look at").

### 5.3 IssueFrame contract (what `check()` returns)

| Column | Type | Required | Engine use |
|---|---|---|---|
| `table` | str | defaults to `ctx.table_name` | `issue.table` |
| `hole_id` | str | for hole-linked scopes | `issue.hole_id` |
| `from_m`, `to_m` | float | interval/point scopes (`to_m = from_m` for points) | `issue.from` / `issue.to` |
| `field` | str | optional | `issue.field` (the analyte code for assays) |
| `value` | str | optional | The offending value **in raw form**. Rules read `*_raw` twins for this. |
| `expected` | str | optional | `issue.expected`, e.g. `≤ 412.50 (collar EOH)` |
| `fp_key` | str | yes | The record key of 02 §5.5, built by helpers `keys.collar()`, `keys.interval()`, `keys.multi()`, … |
| `measure` | float | for banded rules | Severity banding (§5.6) |
| `m_<name>` | any | per template | Message placeholders |
| `row_uids`, `related_hole_ids` | list | optional | `issue_context` |
| `x`, `y`, `z` | float | optional | Map and section display (the engine fills these from collar or trace if absent) |
| `sample_id`, `analyte_code`, `method_id`, `batch_id` | str | optional | `issue_context` |
| `evidence` | dict | optional | `issue_context.evidence` (statistics behind the detection) |
| `severity`, `demotion_reason` | str | optional | Rule-internal demotion (e.g. "near map contact") |

The engine adds `issue_id`, `rule_id`, the final `severity`, `message_en`, `message_fa`, `suggested_fix`, `fingerprint`, `run_id` and the carried-over `status`/`reviewer`/`reason`/`timestamp`. It also writes `jorc_items` into `issue_context`. Messages are **rendered and stored** at detection (02 §5.5 `NOT NULL`), so the audit record keeps the wording that was shown even if templates improve later.

### 5.4 Registry, planning and execution

#### 5.4.1 Registration and discovery
- Each rule is one module, `rules/<family>/<fam>_<nnn>_<slug>.py`, holding one class decorated with `@register`. Family helpers live in `rules/<family>/_common.py`.
- At start-up the registry imports every module under `geovalid_pro.rules` (`pkgutil.walk_packages`). PyInstaller receives the list through a generated hidden-imports file, so discovery also works when frozen.
- Registration-time checks. A failing check breaks the build:
  - the ID matches `FAM-NNN` and the family matches its package;
  - no duplicate IDs;
  - `title_fa`/`title_en` and both messages are present, with **identical placeholder sets** in en and fa;
  - `Params` defaults lie inside their declared ranges;
  - every name in `requires` is a registered product;
  - `jorc_items` use the T1.xx codes;
  - `reference` is non-empty for every family except IMP.
- **A new rule is one new file plus the decorator** (§18). The rule catalogue (03 appendix, report appendix, XLSX) is **generated from the registry** (`geovalid profile catalogue`), so documentation cannot drift from code.

#### 5.4.2 Planning
```python
def plan(profile: "ResolvedProfile", store: "ProjectStore", registry: "Registry") -> "Plan":
    tasks, matrix = [], ExecutionMatrix()
    for rule in registry.sorted_by_id():                        # deterministic order
        cfg = profile.rule(rule.meta.rule_id)                   # enabled, params, bands, per_table, suppressions
        if not cfg.enabled:
            matrix.disabled(rule, cfg.reason); continue
        for table in store.registry().resolve(rule.meta.tables):    # generic INT-* → every interval table
            tcfg = cfg.for_table(table)
            if not tcfg.enabled:
                matrix.disabled(rule, table, tcfg.reason); continue
            if missing := rule.missing_inputs(table, store):
                matrix.not_applicable(rule, table, missing); continue
            tasks.append(RuleTask(rule, table, rule.Params(**tcfg.params), tcfg))
    products = product_registry.closure(p for t in tasks for p in t.rule.meta.requires)
    dag = graphlib.TopologicalSorter(dependency_edges(tasks, products))       # stdlib graphlib
    order = stable_layered_order(dag, key=lambda n: (n.stage_rank, n.sort_id))  # products just in time
    return Plan(order, refcounts=consumer_counts(tasks, products), matrix=matrix)
```

- **Order:** IMPORT → TABLE → CROSS → SPATIAL. Within a layer the order is by rule ID, then table.
- Products are built just in time, before their first consumer, and **released when their reference count reaches zero**. This keeps peak memory near the largest single product, not the sum of all products.
- Products can depend on products. For example, `drv_interval_master` needs `drv_trace` and `drv_assay_wide`. Cycles are rejected at registration.

#### 5.4.3 Execution and post-processing
```python
for node in plan.order:
    ctx.cancel.raise_if_cancelled()                        # cooperative checkpoints (also inside long rules)
    if node.is_product:
        products.ensure(node); continue
    key = result_cache.key(node)                           # §5.4.4
    frame = result_cache.get(key)
    if frame is None:
        frame = run_isolated(node)                         # exception → RuleFailure in matrix; run continues
        result_cache.put(key, frame)
    frame = post_process(frame, node)                      # see list below
    issue_sink.write(frame)                                # issue + issue_context, ≤ 50 k rows per transaction
    products.release_unused(node)
```

`post_process` steps, in order:
1. Validate the IssueFrame schema.
2. Severity: band, then escalate, then demote, then apply the profile override, then clamp (§5.6).
3. Profile suppressions: the issue is stored with status `ignored`, reviewer `profile:<profile_id>` and the profile's reason. **Suppressed issues are stored and listed, never dropped.**
4. Render `message_en`/`message_fa`/`suggested_fix` (§5.7).
5. Compute fingerprints (§5.8). Duplicate fingerprints from one task are merged, and `n_merged` goes into the evidence.
6. Status carry-over (02 §5.5).

The result cache stores the frame from **before** steps 2–6, so profile, review and template changes are always re-applied.

#### 5.4.4 Incremental re-run
The result-cache key of a task is:

`sha256(rule_id, rule.version, messages.version, params_json, table, {column_sha256 of every column read}, {product keys used}, engine_major)`

After a change set touching only `assay` Cu values:
- every collar, survey and lithology task is a cache hit;
- the assay tasks re-run on the Cu part only;
- products such as `drv_trace` stay valid.

Typical re-run after a review cycle is therefore well under a minute (target in §12.3). `--full` bypasses the cache, and a release run always runs in full so it is independent of cache state.

#### 5.4.5 Failure isolation
- A rule that raises is recorded as `FAILED` with its traceback in the run log. The run continues and finishes as `COMPLETED` with failures. The CLI then exits with code 6 (§11.3).
- The dashboard shows failed rules in red, and the report's rule-execution matrix lists them. A report from a run with failed rules carries a statement to that effect on the title page.
- **A release cannot be made from a run with failed rules.**

### 5.5 Vectorised implementation patterns

| Check family | Pattern | Rules (examples) |
|---|---|---|
| Overlap, containment, gaps | Stable sort `(hole_uid, from_m, to_m)`. **Running maximum** of `to_m` per hole: `run_max = g.to_m.cummax(); prev = run_max.groupby(hole).shift()`. Comparing with the previous row only would miss intervals contained in an earlier long interval. overlap = `prev − from_m > eps`; internal gap = `from_m − prev > eps`; top gap = first `from_m > tol`; bottom gap = `eoh_m − last run_max > tol`. | INT-002, INT-004, GEO run checks |
| Duplicates and conflicts | `duplicated(subset=key, keep=False)`, then `groupby(key).nunique()` over value columns to separate identical rows from conflicting ones | COL-001, SUR-002, INT-003, SMP-* |
| Orphans and membership | Exact `isin` on canonical `hole_id`. Suggestions come from a `hole_key` join (02 §1.7). | SUR-001, INT-006, COL-008/009 |
| EOH consistency | `groupby(hole).max()` per child table, merged on collar, compared with eps | COL-007, SUR-006, INT-005 |
| Near-duplicate points, spacing | `cKDTree.query_pairs(r, output_type="ndarray")` and `query(k=4)`. Pairs are classified as twin, wedge or re-drill vs true duplicate using `parent_hole_id`, `hole_type`, dates and **trace divergence at +50 m** from `drv_trace`. | COL-004, COL-015 |
| Point-in-interval, contact crossing | Composite key `k = hole_index·10⁵ + depth_m`, exact to < 1 µm at 10⁹ in float64. One global `np.searchsorted` over sorted contact boundaries replaces per-hole loops. Crossings per sample = boundaries in `(from_m + eps, to_m − eps)`. | INT-008, ASY-008, CRS-001 |
| Station-to-station change | `groupby(hole).shift()`; vectorised dogleg (02 §4.22 formula); azimuth difference wrapped to (−180°, 180°]; azimuth tests masked where both stations are steeper than −85° | SUR-010…012 |
| Spikes | Per hole, a single-station excursion that returns to trend: `Δ⁻ = a_i − a_{i−1}` and `Δ⁺ = a_{i+1} − a_i` both exceed the threshold with opposite signs, and the residual from a centred rolling median (window 5) exceeds the threshold. Correlated in CROSS stage with magnetite logging, Fe, magnetic susceptibility and EMS total-field anomaly. | SUR-013 |
| Sequences and transitions | Shifted code pairs per hole → `crosstab` → Markov transition probabilities. Forbidden pairs are found by a merge with the profile list. | LIT-003, WTH-001 |
| Copy-paste repetition | Row hash of the value columns (`pd.util.hash_pandas_object`) → sliding windows of k rows per hole (`numpy.lib.stride_tricks.sliding_window_view`) → polynomial window hash → windows seen in ≥ 2 holes → exact verification. **Low-information windows (all BDL, one constant code) are excluded**, otherwise barren intervals flood the result. | INT-009 |
| Ratio and inequality | Column arithmetic on `drv_assay_wide` with relative tolerance, skipping pairs where either value is BDL or ODL | ASY-006, user rules |
| Precision and terminal digits | Decimal counts from `*_decimals` or `n_decimals_raw`; last significant digit from the raw text; χ² against uniform per campaign, batch or lab | COL-010 evidence, ASY precision rules |
| Spatial outliers | k-NN weights from a KD-tree on composite midpoints, then vectorised local Moran's I with chunked conditional permutations and **Benjamini–Hochberg FDR**, so multiple testing does not flood SPA-001 with false positives | SPA-001 |

### 5.6 Severity: bands, escalation, demotion, override

Applied in this order:
1. **Bands.** Dual or triple thresholds on `measure`, e.g. `SUR-010 {WARNING: 3, ERROR: 6}` °/30 m and `COL-011 {WARNING: 2, ERROR: 5}` m with `direction: abs_above`. A measure below the lowest band produces no issue. **Contextual bands** select thresholds by a categorical key. Example: COL-011 thresholds by `drv_collar_method.inferred_method`, so handheld-GPS collars are judged against handheld tolerances (brief §3.3 "tunable per inferred method").
2. **Aggregate escalation** (profile). Conditions are evaluated after grouping, for example:
   - `count_per_hole >= 3 → ERROR` (repeated azimuth spikes in one hole);
   - `share_of_table >= 0.05 → CRITICAL` (a systemic problem rather than isolated errors).

   The engine computes `count_per_hole`, `count_per_table`, `share_of_table`, `count_project` and `share_of_holes`, and conditions use the safe expression language (§5.11).
3. **Demotion** by rule logic, with `demotion_reason`. Examples: a lithology–map mismatch within the contact buffer (LIT-004, brief §7.1); an azimuth change on a near-vertical interval (reported as INFO context instead of a WARNING).
4. **Profile override.** `severity: <fixed>` or `max_severity`.
5. **Clamp** to the enum.

When a severity rises above the severity at review, the issue is reopened (02 §5.5).

### 5.7 Messages (en/fa)
- Templates are `str.format` strings over the `m_*` columns, rendered by a custom `Formatter`. Placeholder type comes from the name suffix:
  - `*_m` → metres, 2 decimals;
  - `*_pct` → percent;
  - `*_deg` → degrees;
  - `*_id`, `*_code`, `hole_id`, `sample_id` → identifier.
- In fa, numbers are localised (Persian digits, `٫`, `٬`) and identifiers are wrapped in LRI/PDI isolates with Latin digits (§3.8).
- Example (INT-002):
  - en: `Interval {from_m}–{to_m} m overlaps the preceding interval (ending at {prev_to_m} m) by {overlap_m} m.`
  - fa: `بازه {from_m} تا {to_m} متر با بازه پیشین (پایان در {prev_to_m} متر) به اندازه {overlap_m} متر همپوشانی دارد.`
- `suggested_fix` comes from `fix_en`/`fix_fa`. Its machine form is `issue_context.fix_json`.
- Rendering is vectorised per template. 1 M issues × 2 languages take ~3 s.

### 5.8 Fingerprints and status persistence
- The formula, key forms and normalisation are **exactly 02 §5.5**: `sha256("gv1|rule_id|table|key|field|norm(value)")[:32]`. **Severity and thresholds are excluded.**
- Implementation: the canonical string is built as a vectorised pandas string column, then hashed with `hashlib` in a comprehension. Measured order of magnitude is ~1.5 µs per row, so 1 M issues take ~1.5 s.
- `fp_key` helpers format depths with exactly 3 decimals, so floating-point noise below 0.5 mm cannot change a fingerprint.
- Carry-over: at the start of the sink stage, the run's fingerprints are joined (DuckDB over Arrow) with the latest `issue_review` row per fingerprint. The four transitions of 02 §5.5 are then applied: carry `ignored` (reopen on escalation), carry `accepted` while its change set is DRAFT, `fixed` → `open` on regression, and absent → `fixed` by `system`.
- Bulk review writes one `issue_review` row per issue in a single transaction (02 §5.6).

### 5.9 Validation profiles

**Layers.**
- `resources/profiles/base.yaml`, then `deposit/<type>.yaml`. The nine types are `porphyry_cu`, `epithermal_au`, `vms`, `iocg_skarn_fe`, `pbzn_mvt_sedex`, `chromite`, `bauxite_laterite`, `industrial`, `coal` (02 `DEPOSIT_TYPE`).
- Then an optional company layer, then the project profile.
- Each layer names its parent in `extends: <profile>@<version>`. Inheritance is single, with depth ≤ 4; cycles are rejected.

**Merge semantics.**
- Mappings deep-merge.
- Lists **replace** the parent's list. A key suffixed `+` appends instead (`sentinels+: [-9998]`).
- `null` removes an override, reverting to the parent's value.

**Validation** (pydantic):
- every section has a model;
- each `rules.<ID>.params` block is validated against that rule's `Params` model;
- an unknown rule ID or parameter is a profile error (CLI exit 2);
- `enabled: false` without `reason` is accepted with a warning, and the rule is listed as "disabled without reason" in the appendix.

**Provenance.**
- The resolved profile keeps, for every leaf value, the file and line that set it (ruamel line info).
- `geovalid profile show --resolved --provenance` prints it.
- The report appendix lists **every threshold with its origin** (base / deposit / project), which satisfies §19 "all thresholds … reported in the appendix".

**Hashing.** `profile_sha256` is computed over the canonical JSON of the *resolved* profile, and the YAML text is embedded in the project (02 §5.10).

**Example** (keys of 02 §5.10 plus the `rules`, `suppressions`, `user_rules` and `scoring` sections defined here; parameter names are illustrative, and 03 is authoritative):
```yaml
profile: kz_west_2026            # project layer
version: 1.0.0
extends: porphyry_cu@1.2.0       # → base@1.0.0
title_en: "Kuh-Zar West — porphyry Cu-Au database audit (example)"
title_fa: "کوه‌زر غربی — ممیزی پایگاه داده مس-طلای پورفیری (نمونه)"

schema:
  depth_eps_m: 0.001
  storage: {embed_max_mb: 200}
assay:
  bdl_policy: half_dl
  sentinels+: [-9998]
  preferred_method:
    Cu: ["ALS:Cu-OG62", "ALS:ME-MS61"]
desurvey: {method: MIN_CURV, step_m: 5}

rules:
  COL-004:
    params: {near_duplicate_distance_m: 1.0, twin_max_distance_m: 10.0}
  COL-011:                                   # |ΔZ| collar − topography
    bands: {WARNING: 2.0, ERROR: 5.0}
    bands_by:
      key: drv_collar_method.inferred_method
      HANDHELD_GPS: {WARNING: 10.0, ERROR: 20.0}
  SUR-010:
    bands: {WARNING: 3.0, ERROR: 6.0}        # °/30 m
  SUR-012:
    params: {max_azimuth_change_deg: 10.0, suppress_steeper_than_dip_deg: -85.0}
  SUR-013:
    escalate:
      - {when: "count_per_hole >= 3", to: ERROR}
  INT-004:
    per_table:
      geotech_run: {params: {top_gap_tolerance_m: 3.0}}   # no core in the RC pre-collar
  INT-007:
    enabled: false
    reason: "Sampling is to geological boundaries; variable lengths are by design."
  LIT-003:
    params:
      forbidden_transitions: [[BEDROCK, OVERBURDEN], [FRESH, OXIDE]]

suppressions:                                 # stored as 'ignored', never hidden
  - rule: INT-004
    table: geotech_run
    holes: "TR-*"
    reason: "Trenches are not geotechnically logged."
    approved_by: "A.A"

user_rules:                                   # declarative only (§5.11); IDs 900–999 are reserved
  - id: ASY-901
    kind: inequality
    title_en: "Acid-soluble Cu exceeds total Cu"
    title_fa: "مس محلول در اسید بیشتر از مس کل"
    expr: "CuAS <= Cu * 1.05"
    skip_if: "is_bdl(CuAS) or is_bdl(Cu)"
    severity: WARNING
    jorc_items: [T1.06]

scoring:
  weights: {integrity: 0.30, coverage: 0.15, location: 0.15, survey: 0.15, qaqc: 0.15, recovery: 0.10}
  traffic_light: {green: 80, amber: 60}
```

### 5.10 Rule example (signature level)
```python
# geovalid_pro/rules/interval/int_002_overlap.py
from geovalid_pro.rules.base import (Rule, RuleMeta, RuleParams, Messages, TableSel, Ref,
                                     Family, Severity, Scope, P)
from geovalid_pro.rules.registry import register
from geovalid_pro.rules import keys

@register
class Int002Overlap(Rule):
    meta = RuleMeta(
        rule_id="INT-002", family=Family.INT, scope=Scope.MULTI_ROW,
        tables=TableSel(kinds=("INTERVAL", "EXT_INTERVAL"), required_fields=("hole_id", "from_m", "to_m")),
        title_en="Overlapping intervals", title_fa="همپوشانی بازه‌ها",
        description_en="Partial or full overlap of intervals within one hole, beyond the depth tolerance.",
        description_fa="همپوشانی جزئی یا کامل بازه‌ها در یک گمانه، بیش از رواداری عمقی.",
        severity=Severity.ERROR,
        reference=(Ref("Leapfrog Geo", "Overlapping intervals"),
                   Ref("Datamine Drillhole Importer", "Overlapping samples"),
                   Ref("Micromine", "Validate drillholes: overlaps")),
        jorc_items=("T1.04", "T1.01"), ni43101_items=("12",), brief_ref="§5")

    class Params(RuleParams):
        min_overlap_m: float = P(0.001, unit="m", ge=0.0, le=1.0,
                                 en="Minimum overlap reported", fa="حداقل همپوشانی گزارش‌شونده")

    messages = Messages(
        en="Interval {from_m}–{to_m} m overlaps the preceding interval (ending at {prev_to_m} m) by {overlap_m} m.",
        fa="بازه {from_m} تا {to_m} متر با بازه پیشین (پایان در {prev_to_m} متر) به اندازه {overlap_m} متر همپوشانی دارد.",
        fix_en="Correct the From/To of one of the two intervals; review the source log sheet.",
        fix_fa="مقدار «از/تا» یکی از دو بازه را اصلاح کنید؛ برگه توصیف اصلی را بازبینی کنید.")

    def check(self, ctx, p):
        df = ctx.table(columns=["row_uid", "hole_id", "hole_uid", "from_m", "to_m", "from_raw", "to_raw"])
        df = df.sort_values(["hole_uid", "from_m", "to_m", "row_uid"], kind="stable")
        g = df.groupby("hole_uid", sort=False)
        run_max = g["to_m"].cummax()
        prev_to = run_max.groupby(df["hole_uid"]).shift()      # deepest bottom of all earlier intervals
        overlap = prev_to - df["from_m"]
        hit = overlap > max(p.min_overlap_m, ctx.setting("schema.depth_eps_m"))
        # … pair each hit with the row that set prev_to (searchsorted on run_max) →
        # fp_key = keys.multi(interval_a, interval_b); row_uids = [a, b]; m_* placeholders; measure = overlap
        return issues_frame                                      # IssueFrame (§5.3)

    def propose_fix(self, issues, ctx, p):
        return None   # an overlap needs the source document; no automatic fix is proposed
```

### 5.11 Declarative user rules
The brief asks for user-defined inequality rules (§6.2) and forbidden sequences (§7). These are configured, not coded:
- **Kinds:**
  - `inequality` (wide-assay or table columns);
  - `range` (a field bounded by a categorical, e.g. density by lithology);
  - `required_if` (if a code is logged, a field is mandatory);
  - `pattern` (regex on IDs or codes);
  - `forbidden_sequence`.
- **IDs:** `FAM-901` to `FAM-999` are **reserved for project-defined rules** (a proposal to be confirmed in 03). They live in the profile, so they travel with it and are hashed into the run.
- **Expression language.** A whitelisted subset of the Python AST, evaluated vectorised over pandas Series:
  - allowed: column names, numeric literals, `+ − × ÷`, comparisons, `and/or/not`, and the functions `abs`, `log10`, `min`, `max`, `isnull`, `is_bdl`, `between`;
  - **refused:** attribute access, subscripts, lambdas, comprehensions and any other call.

  No `eval()`. The same evaluator serves escalation conditions (§5.6) and narrative conditions (§9.4).
- **Arbitrary Python rule packs** are disabled by default. An organisation may enable a rule-pack folder in settings, with each file pinned by SHA-256. This is an explicit, audited choice.

### 5.12 Quality gates per rule
A rule is merged only when all of the following hold:
1. A test module drives the synthetic generator with that rule's injector and shows **100 % recall** on the injected errors and **zero issues on the clean twin** dataset.
2. Boundary tests sit exactly at each threshold, both sides.
3. Property tests (hypothesis) cover interval-algebra rules.
4. The registration checks of §5.4.1 pass.
5. The runtime on synthetic dataset **M** is within the rule's budget (the sum over all rules must meet §12.3).
6. fa text is reviewed by a Persian-speaking geologist; the review is recorded in the catalogue.

---

## 6. Analysis layer

### 6.1 Derived-product framework
```python
# geovalid_pro/analysis/products.py — interface sketch
@product("drv_trace", version=3, persist=Persist.DISK,
         reads={"collar": ["hole_uid", "x", "y", "z", "azimuth_grid", "dip", "eoh_m", "collar_location"],
                "survey": ["hole_uid", "depth_m", "azimuth_grid", "dip", "is_accepted", "src_row"]},
         params=("desurvey.method", "desurvey.step_m", "desurvey.first_station_max_m"),
         requires=())
def build_trace(ctx: "ProductContext", *, method: str = "MIN_CURV", exclude_flagged_spikes: bool = False) -> "pa.Table": ...
```

- **Key:** `sha256(name, version, {column_sha256 of reads}, resolved params, variant kwargs, upstream product keys)`.
  - Column-level hashes (§4.1) make invalidation precise. Editing a collar comment does not invalidate the desurvey; editing a collar dip does.
- **Variants:** keyword arguments become part of the key. Examples:
  - `drv_trace(method="BAL_TAN")` for SUR-015;
  - `drv_trace(exclude_flagged_spikes=True)` is a **what-if** product that quantifies how far flagged spikes move the EOH position, **without changing any data**.
- **Cache levels:**
  - **L1:** in-memory LRU within the memory budget (§12.2);
  - **L2:** Parquet in the working cache;
  - **L3:** frozen into the `.gvp` on release.
- **Lifetime.** Products are reference-counted by the planner (§5.4.2) and evicted from L1 when no remaining task needs them.
- **Purity.** A product reads only through `ProductContext` (which records column access exactly like `RuleContext`). It writes nothing except its own return value.

### 6.2 Product catalogue

| Product (02 §4.22) | Built from | Key parameters | Main consumers | Persist |
|---|---|---|---|---|
| `drv_trace` | collar, survey | `desurvey.method`, `step_m`, first-station policy | SUR-010/015/016, COL-011 trace exits, pierce points, interval master, viewers, GIS exports | L2, L3 |
| `drv_trace_compare` | `drv_trace` × 3 methods | — | SUR-015 | L2, L3 |
| trace points (1 m resample) | `drv_trace` | `proximity_step_m` | SUR-016 | L1 only |
| `dem_surface` | DEM layer (raster, TIN, contours, points, mesh) | build method, resolution | collar sampling, trace-exit test, slope | L2 (COG / TIN Parquet) |
| `drv_collar_spatial` | collar, `dem_surface`, licence, geological map, KD-tree | layer IDs, sampling method, contact buffer | COL-005, COL-011…013, COL-015, LIT-004 | L2, L3 |
| `drv_collar_method` | collar, `drv_collar_spatial`, campaign, planned fields | evidence weights (profile) | COL-010, COL-011 contextual bands, T1.08 | L2, L3 (+ `inference` rows) |
| `drv_assay_wide` | assay, sample, lab_batch | `preferred_method`, `bdl_policy`, `repeat_policy` | ASY-*, CRS-*, GEO-004, interval master | L2, L3 |
| `drv_qaqc_crm`, `_blank`, `_pair`, `_batch` | sample, assay, crm_value, blank_value | `qaqc.*` | QAQ-*, T1.06 | L2, L3 |
| `drv_interval_master` | all interval tables, `drv_assay_wide`, `drv_trace`, hole_segment | field selection, overlap policy | CRS-*, SPA-*, contact analysis, swaths, strip logs | L2, L3 |
| `drv_composite` | `drv_interval_master` | method (BEST_FIT default), length, domain field, min coverage | SPA-001, twins, method bias, variogram preview | L2 |
| `drv_pierce_point` | `drv_trace`, surfaces | surface set | spacing at depth, cross-hole lithology consistency | L2 |
| `drv_hole_summary` | tables, issues | — | dashboard, inventory, scoring | L2, L3 |
| `drv_confidence` | issues, products | `scoring.*` | dashboard, report | L2, L3 |
| `kdtree:<point set>` | coordinate arrays | — | spatial rules and analyses | L1 only |

### 6.3 Desurvey engine
- **Methods:**
  - `MIN_CURV` (default; formulas in 02 §4.22);
  - `BAL_TAN` (ratio factor fixed at 1);
  - `TAN` (the upper-station direction is held over the course).
- **Vector form, used throughout.**
  - Tangent: `t = (sin I·sin A, sin I·cos A, −cos I)` in (E, N, up), with `I = 90° + dip` and `A = azimuth_grid`.
  - Dogleg: `β = arccos(clip(t₁·t₂, −1, 1))`.
  - Ratio factor: `RF = (2/β)·tan(β/2)`, using the series `1 + β²/12` for β < 10⁻⁴.
  - Course: `Δp = ΔMD/2·(t₁ + t₂)·RF`.
  - All holes are handled at once on concatenated station arrays. There is no per-hole loop.
- **Positions at arbitrary depth** (interval boundaries, sample midpoints) are computed **exactly on the arc**. For depth d in course [MD₁, MD₂], with `f = (d − MD₁)/ΔMD`:
  1. `t(f) = slerp(t₁, t₂, f)`;
  2. `p(d) = p₁ + (d − MD₁)/2·(t₁ + t(f))·RF(f·β)`.

  This avoids the chord error of linear interpolation between stations. Depths are located with one global `searchsorted` on the composite key (§5.5).
- **Station policy.** Every policy is recorded in the product metadata and in the method notes.
  - Only `is_accepted` stations are used.
  - Duplicate depths keep the first by `src_row`; SUR-002 reports them.
  - Collar orientation is used as station 0 when the first station is deeper than `first_station_max_m`; SUR-007 reports it.
  - The last direction is held to EOH.
  - A hole with no survey and no collar orientation gets `trace_status = ASSUMED_VERTICAL`. It is **never silent**: an issue is raised, and the hole is excluded from spacing-at-depth and proximity tests unless the profile includes it.
- **Method comparison.** The EOH position by all three methods goes into `drv_trace_compare.d_eoh_m` for SUR-015.
- **Invariants** (property tests):
  - a straight hole is reproduced exactly;
  - a constant-curvature arc is reproduced by MIN_CURV to 10⁻⁹ m;
  - along-hole length is preserved;
  - the BAL_TAN and TAN results converge to MIN_CURV as station spacing tends to 0.
- **Cost.** 5 000 holes × 20 stations: < 0.5 s. Interpolation at 2 M boundaries: ~1 s.

### 6.4 Azimuth reference handling
- `azimuth_true` and `azimuth_grid` are derived when Vb is built (02 §4.4), using `core.geomag` and `core.crs` (§3.7). A change of declination model or override is a project decision: it rebuilds Vb and **rebases** change sets (§7.5).
- The `AZ_REFERENCE` inference uses this evidence:
  - header tokens and instrument class;
  - per hole with mixed instruments (gyro + EMS), the median azimuth difference at overlapping depths compared with the model declination δ. A constant offset ≈ δ is the signature of one survey being uncorrected;
  - the offset between collar design azimuth and first station, per campaign.
- SUR-014 reports inconsistencies, with the measured offset and the model δ side by side.

### 6.5 Interval master (`drv_interval_master`)
1. **Boundaries.** The union of all from/to boundaries of the selected tables, plus 0 and EOH, per hole, snapped within `depth_eps_m` (`np.round(x/eps)·eps` on the composite key).
2. **Elementary intervals** are consecutive boundary pairs.
3. **Assignment.** For each table: `merge_asof(by="hole_uid", on="from_m", direction="backward")`, then a coverage check `to_m ≥ elem_to − eps`. Elementary intervals not covered get NULLs and `covered_<table> = false`.
4. **Overlaps** (INT-002 already reports them): the master takes the row with the smaller `from_m`, then `src_row`, and records `n_conflicts_<table>`. It never silently averages.
5. **Values are carried, not length-scaled** (02 §4.22). Assays come from `drv_assay_wide` through the sample interval. XYZ of the midpoint and both ends come from §6.3.
6. **Built in batches** of ~500 holes, written as row groups. Typical size: ~1.4 × the largest table's row count. Consumers read projected columns only.

### 6.6 Compositing (`drv_composite`)
- Methods (02 §4.22): `BEST_FIT` (default, equal lengths per domain run), `FIXED` and `DOMAIN_WHOLE`.
- Minimum coverage 50 %. The BDL policy follows the profile.
- **Unsampled intervals are missing, not zero**, unless `composite.unsampled_as_zero: true` is set explicitly. That setting is common for Au in unsampled barren gaps, and the report prints it.
- The composite-length recommendation is derived from the modal and median sample length and the proportion of samples longer than the candidate length (brief §11).

### 6.7 Statistics services (`analysis/stats`, `qaqc.py`, `geochem.py`, `logging_stats.py`)
Every service is a pure function returning a frozen dataclass. Each result carries `n`, `n_excluded` with reasons (`BDL`, `NS`, `outside domain`, …), the weighting used and the parameters. Figures, narrative and tables all read these same objects, so a number in the text equals the number in the figure.

| Service | Content |
|---|---|
| Descriptive | Weighted (length) and unweighted: n, n missing, n < DL, min, P5, P25, median, mean, P75, P95, P99, max, SD, CV, skewness, kurtosis, geometric mean. Weighted quantiles by cumulative-weight interpolation. |
| Distributions | Log-probability plotting positions (Hazen). **Gaussian-mixture decomposition** of log₁₀ values (k ≤ 4 by BIC) for population breaks and mixed-unit detection. ECDF, KDE (binned FFT KDE for n > 50 k). |
| Outliers and top-cut | Tukey fences on logs, MAD, log-probability breaks, MinCovDet for multivariate outliers. Top-cut by CV, decile analysis (Parrish), metal-at-risk (Parker, seeded simulation) and the cumulative metal curve. Always labelled **suggestion only**. |
| Correlation | Pearson on logs, Spearman, and **CLR** after multiplicative replacement of BDL values. Hierarchical clustering (average linkage on 1 − \|r\|). PCA by SVD of CLR data (biplot). |
| Tests | ANOVA (statsmodels), Kruskal–Wallis, KS, χ² + Cramér's V, Cohen's κ, Wilcoxon, paired t |
| QA/QC | Shewhart limits (±2SD/±3SD), Westgard rules (1₃ₛ, 2₂ₛ, R₄ₛ, 4₁ₛ, 10ₓ), bias %, mislabelled-CRM detection (nearest certified value), blank thresholds and carry-over, HARD / ranked HARD, MPD, Thompson–Howarth, RMA with bootstrap CI |
| Geochemistry | Oxide ↔ element factors (02 §4.8), Fe_total consistency, Cu–S stoichiometry, oxide totals, Ishikawa AI, CCPI, molar K/Al and Na/Al, ratio stability |
| Logging | Code inventories (count and metres), Shannon diversity, Markov transition matrices, logger-effect χ², contingency tables, contact analysis (grade vs signed distance from contact, hard/soft boundary test) |
| Spatial statistics | Declustering (cell-size sweep, declustered vs naive mean), swaths, variogram preview (pairs capped at 5 × 10⁷ by seeded subsample; labelled informative only) |

### 6.8 Spatial services (`analysis/spatial`)
- **KD-tree service.** `cKDTree` cached by point-set hash (L1): nearest neighbours 1–3, pair queries, k-NN weights.
- **DEM.**
  - Raster: windowed read and bilinear sampling (nodata-aware). TIN: barycentric sampling.
  - Slope and aspect by Horn's method on grids, or by triangle normals on TINs.
  - Surface metadata (source, resolution, vertical CRS, vintage, `interp_rmse_m`, share of flat triangles) goes to `spatial_layer` (02 §4.21).
- **Voronoi.** `shapely.voronoi_polygons`, clipped to the licence or the convex hull plus a buffer. Quadrat counts. Kernel density on a grid, clipped to the boundary.
- **Point pattern.**
  - Clark–Evans R with Donnelly edge correction.
  - Ripley's K/L with border correction inside the licence, with 99 seeded CSR envelopes.
  - **Grid detection:** NN-vector azimuth histogram (mod 180°) gives the dominant line directions. Spacing is the mode of NN distances along and across them. Drill fences come from clustering the collars' projections perpendicular to the dominant line direction.
- **Autocorrelation.** Local Moran's I and Getis–Ord Gi* on composite midpoints, with k-NN or distance-band weights (row-standardised), 999 conditional permutations and BH-FDR. Validated against `esda` as a test oracle.
- **Trace geometry.**
  - **Proximity:** KD-tree on 1 m trace points within r. Pairs from the same hole, and parent–daughter pairs above the kick-off depth (wedges legitimately share their upper trace), are excluded. Candidate pairs are refined by segment–segment distance.
  - **Exits above topography:** trace points with `z > z_topo + tol` below the collar zone.
  - **Pierce points** with horizontal planes, DEM-offset surfaces and mineralised-zone midpoints.
- **Overlay.** Collar in licence, distance to the licence edge, map unit and distance to the nearest map contact (shapely 2 vectorised).

### 6.9 Inference services and the evidence model
```python
@dataclass(frozen=True)
class Evidence:
    code: str                                  # "HDR_TOKEN", "MAGNITUDE_PRIOR", "PAIRED_RATIO", "TERMINAL_DIGIT" …
    text_en: str; text_fa: str                 # rendered for GUI cards and the report appendix
    observed: dict[str, float | int | str]     # the numbers the user sees (median, p99, ratio, χ², p …)
    log_odds: dict[str, float]                 # contribution to each alternative
    reliability: float = 1.0                   # e.g. precision_source FLOAT_REPR → 0.4
    group: str = "column"                      # "column" | "hole" | "campaign" | "project"

@dataclass
class InferenceResult:                         # persisted as one `inference` row (02 §5.3)
    kind: str; scope_table: str | None; scope_field: str | None; scope_key: str
    alternatives: list[tuple[str, float]]      # (value, posterior), sorted
    evidence: list[Evidence]
    status: str = "PROPOSED"                   # PROPOSED → CONFIRMED / OVERRIDDEN / REJECTED by a person

def combine(prior: dict[str, float], evidence: list[Evidence]) -> list[tuple[str, float]]:
    """s_k = ln π_k + Σ_e r_e · log_odds_e[k];  P_k = softmax(s)_k.  Transparent: every term is displayed."""
```

- **Decided once per column, table or campaign** (02 §6), never cell by cell.
- **Critical kinds** must be confirmed by a person before a release (gate §7.6): `DEPTH_UNIT`, `ANALYTE_UNIT`, `CRS`, `UTM_ZONE`, `XY_SWAP`, `Z_DATUM`, `DIP_CONVENTION`, `AZ_REFERENCE`. The other kinds may stand as PROPOSED, and the report counts them (02 §1.9).
- **Analyte unit evidence:**
  - header and unit-row tokens;
  - magnitude against analyte priors (crustal abundance and typical mineralised ranges per deposit type, in `resources/dictionaries/analyte_priors.yaml`);
  - the paired-column ratio, e.g. Cu_ICP [ppm] vs Cu_AAS: a median ratio ≈ 10 000 means % vs ppm;
  - DL signature (`<0.01`, granularity);
  - the method catalogue (e.g. ME-MS61 reports Cu in ppm);
  - Cu–S stoichiometric plausibility;
  - GMM bimodality of log values separated by ≈ 3 or 4 decades, which signals mixed units (ASY-004).
- Depth unit, coordinate format, zone, swap, dip convention and percentage scale use the evidence lists of 02 N09–N14.

### 6.10 Collar survey method: weights-of-evidence classifier
**Classes:**
- `SURVEY_GRADE` covers RTK_GNSS, DGPS and TOTAL_STATION of 02 `COLLAR_SURVEY_METHOD`, because numeric evidence cannot tell them apart;
- `HANDHELD_GPS`;
- `PLANNED`;
- `DIGITISED`;
- `UNKNOWN`.

**Scoring.** `combine()` (§6.9), with expert-set log-odds weights in the profile (`inference.collar_method.weights`).
- They are **not trained**. They are calibrated on synthetic data with known methods and on any client collars of documented method.
- `UNKNOWN` is returned when the top posterior is < 0.5 or fewer than two independent evidence groups contribute.

| # | Evidence (brief §3.2) | Computation | Default log-odds (illustrative) |
|---|---|---|---|
| E1 | Declared method | `collar.collar_survey_method` | +2.5 toward the declared class. A contradiction with E2–E10 is reported by COL-010 ("declared RTK, evidence indicates handheld"). |
| E2 | XY precision | `x_decimals`, `y_decimals` × reliability by `precision_source` (TEXT 1.0, EXCEL_FORMAT 0.8, FLOAT_REPR 0.4) | ≥ 2 decimals: SURVEY_GRADE +2.0, HANDHELD −1.5, PLANNED −2.0. 0 decimals: HANDHELD +1.0, PLANNED +1.0, DIGITISED +0.5, SURVEY_GRADE −2.0. |
| E3 | Z precision | `z_decimals` | as E2, half weight |
| E4 | Terminal digits (campaign group) | χ² of last digits against uniform; excess of 0/5 at p < 0.01 | HANDHELD +1.0, DIGITISED +1.0 |
| E5 | Grid regularity | X and Y both multiples of 25/50/100 m (checked against a random-coincidence expectation) | PLANNED +2.5 |
| E6 | Design orientation and EOH | Azimuth on a 0/45/90° set, dip exactly −45/−50/−60/−90, round EOH | PLANNED +1.0 |
| E7 | Equals planned coordinates | `x = planned_x` and `y = planned_y` exactly | PLANNED +3.0 |
| E8 | ΔZ behaviour | Robust scatter (MAD) of ΔZ **after removing the campaign median offset**. The offset itself (datum) is COL-012 and is not used as method evidence. | MAD ≤ 1 m: SURVEY_GRADE +1.5. MAD 3–10 m: HANDHELD +1.5. \|ΔZ\| < 0.2 m with MAD < 0.2 m (Z draped from DEM): DIGITISED +2.0. |
| E9 | Repeated identical Z | Share of collars sharing exact Z within a campaign | DIGITISED +1.0 (also reported by COL-013) |
| E10 | Re-survey / twin jitter | Horizontal difference between two coordinate sets of the same hole, or of twins with surveyed pads | < 0.1 m: SURVEY_GRADE +1.5. 2–10 m: HANDHELD +1.5. |
| E11 | Campaign pattern | Change-point in precision regime by campaign, contractor or date | Splits groups; no direct weight |

**Outputs:**
- `drv_collar_method` (inferred method, confidence %, evidence JSON with each term) and an `inference` row of kind `COLLAR_METHOD` (02);
- an **evidence waterfall** per collar in the GUI;
- a map coloured by method and a campaign summary table;
- a generated recommendation, for example: "Re-survey 37 collars of campaign PH1-2014 with DGPS before resource estimation (JORC T1.08)".

### 6.11 Version-comparison engine (VER)
- DuckDB full outer joins on natural keys per table (02 §1.7). Categories:
  - added or removed holes;
  - collars moved (distance, azimuth of the shift: a constant ≈ 175 m N–S shift flags ED50(ED77) vs WGS 84, 02 §6.5);
  - EOH changes; survey stations added, removed or changed;
  - intervals with a moved boundary, a split or a merge;
  - value changes (absolute and relative);
  - **code renames**, detected as a near-bijective mapping (≥ 95 % of shared intervals).
- "Database vs software export" reads the export back through its preset mapping template, then diffs.
- Outputs: VER issues, a summary and a detailed diff (XLSX) and a change map.

---

## 7. Change management

### 7.1 Layers
The layers are those of 02 §1.2: raw snapshot V0 (immutable) → canonical base Vb (deterministic) → working version Vw = Vb ⊕ applied change sets → release Vr (frozen). Two kinds of decision exist, and they never mix:
- **Representation decisions:** mapping, units, CRS, dip convention, declination, code synonyms. These are inference or mapping records. Changing one rebuilds Vb and rebases the change sets.
- **Value corrections:** a wrong EOH, a mistyped depth, a datum shift. These are change sets.

### 7.2 Change-set lifecycle
```
 issue → (reviewer: Accept fix / Edit value / Bulk) ──► DRAFT ──apply──► APPLIED ──revert──► REVERTED
                                                       │  ▲                │                   (via a new REVERT set)
                                     QUndoStack edits ─┘  │                └─► new WORKING version Vw'
                                     conflicts on apply ──┘ (stays DRAFT, conflict list shown)
```
- One DRAFT change set per review session by default. The reviewer may split it by theme (e.g. "Datum shift campaign 2014").
- The mandatory `reason` (02 `change_set.reason`) is requested at apply time, pre-filled from the rule's fix text.
- **Fix kinds compile to the 02 operations** (`SET`, `INSERT`, `VOID`, `UNVOID`, `RELINK_HOLE`):

| Fix kind | Compiles to | Typical source |
|---|---|---|
| Set value | `SET` | COL-007 (EOH to max child depth), manual edit |
| Void row | `VOID` | INT-003 exact duplicate |
| Merge consecutive identical intervals | `VOID` × n + `INSERT` (`derived_from`) | LIT-002 |
| Split interval at contact | `VOID` + `INSERT` × 2 | Reviewer-driven only |
| Add collar station | `INSERT` survey at depth 0 from collar orientation | SUR-007 |
| Datum shift / drape to topography | `SET z` × n (origin `DATUM_SHIFT`, parameters in `reason` and `new_value`) | COL-011/012 |
| Dip sign flip for one hole | `SET dip` × stations | SUR-005, when the per-hole inference is rejected |
| Relink orphan | `RELINK_HOLE` after `hole_alias` confirmation | SUR-001, INT-006 |

### 7.3 Applying a change set
1. **Base check.** If `base_version_id` ≠ current Vw, the set is rebased on Vw first (§7.5).
2. **Optimistic check** (02 E10). Every `SET`/`VOID` must find `old_value` equal to the current value. Any mismatch → the whole set is refused and listed.
3. **Copy-on-write.** Only the touched tables and parts (§4.1) are rewritten as new blobs. Blobs are written first: they are content-addressed, so an orphan after a crash is harmless and is garbage-collected. Then, in **one SQLite transaction** (`synchronous=FULL`): new `dataset_version` (WORKING, parent = previous Vw), manifests, `change_set.status = APPLIED`, and `audit_log` `CHANGE_SET_APPLIED`.
4. **Issues.** Linked issues stay `accepted` until the next run. Then the run either confirms them `fixed` or reopens them with "fix applied, issue persists" (02 §5.5).
5. An **incremental re-run** is offered immediately (§5.4.4).

### 7.4 Undo
- **Level 1 (draft):** a GUI `QUndoStack` over the DRAFT set's changes. Every edit is persisted to the draft immediately, so undo state survives a crash (§13.3).
- **Level 2 (applied):** **revert = a new `REVERT` change set** with the inverse changes (02 §5.7). History is never deleted, and Vw moves forward. "Restore Vw to version X" reverts the intervening sets in reverse order as one operation.

### 7.5 Rebase
Rebasing (02 §9) happens when a remapping, an inference change or a new client delivery produces a new Vb:
- each applied change is re-targeted by `natural_key`;
- outcomes are **reapplied**, **already fixed upstream** (no-op, recorded) or **conflict** (listed for review, never dropped);
- the rebase is itself a `REBASE` change set, so the audit trail shows it.

### 7.6 Releases and release gates
A `RELEASE` is created only when **all** of the following hold. Each failed gate is listed with a link to the cause.
1. The latest run on this Vw is **complete and full**: not incremental, no `FAILED` rules.
2. **No unconfirmed critical inference** (§6.9).
3. **No open or accepted CRITICAL issue**, unless each is `ignored` with a reason by a named reviewer. Waived criticals are printed in the executive summary.
4. The audit-log hash chain verifies (02 §5.8).
5. All external sources re-verify by SHA-256.
6. The profile is embedded and hashed.

On release:
- Vw is frozen (`is_frozen`);
- products used by reports and exports are copied into the container (L3);
- the `recipe_sha256` is computed and the label recorded.

Every export and final report cites `version_id`, `recipe_sha256`, `profile_sha256` and `run_id`. **Draft reports** (A18) may be produced from Vw, watermarked "DRAFT — working version, not a release" on every page. **Exports are never produced from Vw.**

### 7.7 Audit trail
- The `audit_log` (02 §5.8) receives every project event. The chain is verified on every open, and a break is CRITICAL.
- Identity is the OS login plus the display name from settings. There is **no authentication**, which the report's audit appendix states.
- The audit trail, change log (`change` ⨝ `change_set`) and review history export to XLSX/CSV with the cleaned database (02 §9.6).

### 7.8 "Never silently change data": guarantees and their enforcement

| # | Guarantee | Mechanism | Test |
|---|---|---|---|
| G1 | Source bytes are never modified | Sources are read from temporary copies or read-only handles. SHA-256 at import, re-verified on open and at release. Export paths that resolve to a source path are refused. | Hashes before and after a full workflow are equal |
| G2 | The raw snapshot and releases are immutable | Frozen versions are read-only in `ProjectStore` (02 E11) | A write attempt raises |
| G3 | The canonical base is a deterministic function of its recipe | Stable sorts, fixed row groups, no wall-clock values in data | A rebuild is byte-identical |
| G4 | Rules and products cannot change data | Contexts expose read-only, Copy-on-Write frames and have no write API. After each run the engine asserts that the version's manifest hashes are unchanged. | Mutation attempts in test rules are caught |
| G5 | Every data change is a change set with who/when/old/new/why/issue | 02 schema `NOT NULL` columns, CHECKs and the optimistic apply | Schema tests |
| G6 | No conclusion rests silently on an unconfirmed inference | PROPOSED inferences raise issues and are counted in the executive summary; release gate 2 | Report lint |
| G7 | History is append-only | SQLite triggers `RAISE(ABORT)` on `UPDATE`/`DELETE` of `change`, `issue_review` and `audit_log` (and of `change_set` rows once `APPLIED`, except the status transition to `REVERTED`) | Trigger tests |
| G8 | The cleaned database never overwrites the original | Exports go to a new, versioned folder named by `version_id` | Path tests |
| G9 | Suppressions and disabled rules are visible | Stored as `ignored` with reasons; listed in the rule-execution matrix and the appendix | Report lint |

---

## 8. Confidence scoring and JORC / NI 43-101 mapping

### 8.1 Hole-level components
Each component is a **base metric** (what the data are) multiplied by an **issue factor** (what is wrong with them). Issues are partitioned by family, so no issue is counted twice.

| Component c | Base metric `b` (0–100) | Issue families feeding `P` | Default weight ω |
|---|---|---|---|
| Location (L) | Expected value over the collar-method posterior: Σ P_k·v_k, with v = SURVEY_GRADE 100, HANDHELD_GPS 50, UNKNOWN 40, DIGITISED 30, PLANNED 10 | COL location rules (002, 004–006, 010–013) | 0.20 |
| Survey (S) | Instrument class (gyro/NS gyro 100, MEMS gyro 95, EMS multishot 85, single-shot/camera 75, acid tube 40, design-only 10) × spacing factor min(1, 30 m / median station spacing), floored at 0.5 | SUR | 0.15 |
| Integrity (I) | 100 | Other COL rules, INT, IMP, SMP, hole-level CRS | 0.20 |
| Logging (G) | Length-weighted coverage of the logging tables the profile marks as expected (lithology, alteration, mineralisation, weathering, structure) | LIT, ALT, MIN, WTH, STR, DEN, MAG | 0.15 |
| Assay and QA/QC (Q) | Share of the hole's assayed metres in batches passing CRM and blank checks. **No QA/QC → 0.** | ASY, QAQ | 0.20 |
| Recovery (R) | Median CR (core) or mass recovery (RC), mapped ≥ 95 % → 100, 85 % → 80, 70 % → 50, linear between | GEO | 0.10 |

```
P_c,h  = Σ_{i ∈ issues(c, h)}  w_sev(i) · s(i) / n(i)
           w_sev : CRITICAL 20 · ERROR 5 · WARNING 1 · INFO 0            (profile)
           s     : open 1 · accepted 1 · ignored 0 · fixed 0            (ignored needs a reason; counted separately)
           n     : 1 for collar/survey issues; max(1, L_h / 100 m) for interval-borne issues (density per 100 m)
C_c,h  = b_c,h · exp(−P_c,h / τ_c)          τ_c default 10  →  1 WARNING ≈ ×0.90, 1 ERROR ≈ ×0.61, 1 CRITICAL ≈ ×0.14
S_h    = Σ_c ω_c · C_c,h / Σ_c ω_c          over components that apply; an expected but absent component scores 0
Cap    : any open or accepted CRITICAL on the hole → S_h ≤ 40
```

### 8.2 Table and project aggregation
- **Table score:** `T_t = coverage_t · 100 · exp(−P_t / (τ · max(1, L_t / 1 km)))`. `P_t` sums the issues of table t; `L_t` is its logged length.
- **Project Data Confidence Index:** `DCI = Σ_h W_h·S_h / Σ_h W_h`.
  - `W_h` = hole length by default.
  - Alternatively `scoring.weighting: mineralised_metres` weights by metres inside logged mineralisation or above a profile cut-off. That focuses the index on the data that will drive an estimate.
- **Project caps.** An open project-level CRITICAL caps the DCI at 40, regardless of the average. Examples: QAQ-001 "no QA/QC", systemic COL-006 CRS error, broken audit chain.
- **Traffic lights:** green ≥ 80, amber 60–79, red < 60 (profile).
- **Storage:** `drv_confidence` (02 §4.22), with every component and term in `components` JSON.

### 8.3 JORC 2012 Table 1, Section 1: item assessment
```
item score = min(E_i, F_i)
  E_i : item-specific evidence scorecard (metrics below → 0–100 via profile breakpoints)
  F_i : 100 · exp(−P_i / τ_i),  P_i over issues whose rule lists item i in jorc_items, normalised per 10 holes
status: Supported ≥ 80 · Partially supported 60–79 · Not supported < 60 · Not assessable (no evidence in the database)
```

| Item | Evidence metrics `E_i` | Main rules |
|---|---|---|
| **T1.01** Sampling techniques | Sample-register completeness; `sample_method` coverage; sample-length statistics; share of samples crossing contacts | SMP-*, INT-007, INT-008 |
| **T1.02** Drilling techniques | `drilling_method`, `core_size`, `hole_segment` completeness; method mixing by domain; orientation-tool coverage (structure quality) | COL (method fields), CRS-002 |
| **T1.03** Drill sample recovery | CR/RQD coverage; recovery distribution; **recovery–grade test** result; RC mass recovery; wet-sample share | GEO-001…004, SMP-* |
| **T1.04** Logging | Logging coverage vs EOH; dictionary conformance; logger effect; quantitative vs qualitative fields | LIT-*, ALT-*, MIN-*, WTH-*, INT-* |
| **T1.05** Sub-sampling and preparation | Split type (half/quarter core, riffle/cone); duplicate precision **by stage** (field / coarse / pulp); sample mass vs theoretical | QAQ-004, SMP-* |
| **T1.06** Quality of assay data and laboratory tests | Insertion rates vs targets; CRM bias and failure rates; blank contamination; DL suitability; lab accreditation; method class vs commodity (total vs partial) | QAQ-*, ASY-001…005 |
| **T1.07** Verification of sampling and assaying | Twin-hole and umpire results; **adjustments to assay data**: the count and nature of applied change sets touching assay values (an explicit Table 1 criterion); primary-data documentation (source hashes, audit chain) | CRS twins, QAQ umpire, change log |
| **T1.08** Location of data points | Collar-method distribution and confidence; ΔZ statistics; declared CRS/datum consistency; survey instrument mix; topographic control (DEM source, resolution, RMSE, vintage) | COL-002…013, SUR-* |
| **T1.09** Data spacing and distribution | NN spacing, spacing at depth (pierce points), Clark–Evans, declustering effect, compositing applied, indicative spacing table (clearly labelled) | COL-015, SPA-* |
| **T1.10** Orientation of data vs structure | Hole azimuth/dip distribution vs the dominant structural or mineralisation trend (from structure data or the profile); angle-to-mineralisation statistics | STR-*, SUR-* |
| **T1.11** Sample security | Dispatch and custody coverage; seal and condition fields; LNR counts | SMP-* (chain of custody) |
| **T1.12** Audits or reviews | This run and its predecessors (history); user-recorded prior audits; VER comparisons. Mostly **Partially / Not assessable from the database**, and the report says so. | VER-* |

### 8.4 NI 43-101
- **Item 11** (Sample preparation, analyses and security) is assessed from T1.05, T1.06 and T1.11, with T1.01 as context.
- **Item 12** (Data verification) is assessed from T1.07 and T1.08, plus the tool's own verification log: what was checked, how many records, which rules were disabled, limitations.
- The report states that QP site verification, independent sampling and visual core checks are outside the tool's scope.

### 8.5 Indicative fit-for-purpose statement
A profile-editable decision table (illustrative defaults):

| Use | Conditions |
|---|---|
| Exploration targeting | DCI ≥ 50 and T1.08 not "Not supported" |
| Supports **Inferred** | DCI ≥ 65; T1.06 and T1.08 at least "Partially supported"; QA/QC exists; no open CRITICAL |
| Supports **Indicated** | DCI ≥ 80; T1.03, T1.05, T1.06, T1.07, T1.08 and T1.09 "Supported"; twin or umpire evidence present |

The statement is always printed with: "Indicative only. Not a Competent Person / Qualified Person opinion. Final acceptance of data for public reporting remains with the CP/QP" (brief §13, §19).

### 8.6 Transparency and sensitivity
- Every score in the dashboard drills down to its components, terms and issues.
- The report prints the weights, τ values and caps.
- **Weight sensitivity:** 1 000 seeded Dirichlet draws around the default weights (≈ ±25 %) plus τ × 0.5…1.5. The report gives the 5th–95th percentile, e.g. "DCI 71 (67–74)". A conclusion that flips within that range is flagged as weight-sensitive.

---

## 9. Reporting pipeline

### 9.1 Pipeline and principles
```
 run results (issues · drv_* · stats objects §6.7 · drv_confidence)
   │
   ├─► report.findings ──► Finding set (typed values · rule IDs · T1.xx · provenance)         language-free
   │        ├─► report.narrative ── phrasebooks fa/en ──► paragraphs (en + fa) · actions       both languages
   │        └─► report.sections ── one builder per §14.1 chapter and appendix ──► RDM          both languages
   │
   ├─► plots.registry ──► figure set ──► plots.render (process pool, cache) ──► PNG 300 dpi + SVG per language
   │
   └─► RDM ──► report.numbering ──► report.lint ──┬─► docx_builder ─────────────────► report.docx
                                                  ├─► html_builder (print) ──► pdf.py ──► report.pdf
                                                  ├─► html_builder (dashboard) ──────► dashboard.html
                                                  └─► io.writers.issue_log ──────────► issues.xlsx · issues.csv
```

1. **Compute once, render many.** Findings, figure data and numbering are computed once per report job. The fa, en and bi outputs of one release therefore carry identical numbers and identical figure and table numbers: Figure 3-7 is the same figure in every language, so an English-reading CP/QP can cross-reference a Persian report.
2. **Every number has one source.** Narrative, figure annotations and tables read the same frozen statistics objects (§6.7). The report layer never recomputes a statistic.
3. **Final reports come from a release** (A18, §7.6). Draft reports from Vw carry the watermark on every page.
4. **No placeholder text.** A section without data prints a specific *not assessable* statement: what is missing and why it matters (brief §14.1). Lint enforces it (§9.10).

### 9.2 Report Document Model (RDM)
```python
# geovalid_pro/report/model.py — interface sketch
Lang = Literal["en", "fa"]; Mode = Literal["en", "fa", "bi"]

@dataclass(frozen=True)
class I18n:                                   # every user-facing string exists in both languages
    en: str; fa: str

@dataclass(frozen=True)
class Span:                                   # inline run inside a paragraph
    text: I18n
    kind: Literal["plain", "id", "number", "term", "emph", "ref"] = "plain"   # id/number → LTR isolate in fa
    finding: str | None = None                # provenance, e.g. "collar.dz_summary:median_dz_m"
    target: str | None = None                 # anchor for kind="ref" (figure, table, section, issue)

@dataclass(frozen=True)
class Para:        spans: tuple[Span, ...]; style: str = "Body"   # style names exist in the DOCX template and print.css
@dataclass(frozen=True)
class Heading:     level: int; text: I18n; anchor: str
@dataclass(frozen=True)
class FigureBlock: key: str; anchor: str; size: "SizeClass"; caption: I18n; source: I18n
@dataclass(frozen=True)
class TableBlock:
    key: str; anchor: str; caption: I18n; columns: tuple["ColumnSpec", ...]; data: "pa.Table"
    highlight: tuple["Highlight", ...] = (); landscape: bool = False; max_rows: int = 60
@dataclass(frozen=True)
class Callout:     kind: Literal["key_findings", "limitation", "disclaimer", "not_assessable"]; body: tuple["Block", ...]
@dataclass(frozen=True)
class Section:     heading: Heading; blocks: tuple["Block", ...]; orientation: Literal["portrait", "landscape"] = "portrait"

@dataclass(frozen=True)
class Document:
    meta: "ReportMeta"              # project, release/version, recipe/profile/run hashes, mode, branding, draft flag
    front: tuple[Section, ...]      # title page, disclaimer, TOC, executive summary
    chapters: tuple[Section, ...]   # §14.1 chapters 2–13
    appendices: tuple[Section, ...] # issue list, rule catalogue + thresholds, dictionaries, method notes, glossary,
                                    # rule-execution matrix, audit summary
```
- `ColumnSpec` carries the canonical and display units, the number format (decimals or significant figures by quantity kind), alignment and a bilingual header with the unit in brackets (brief §15).
- The RDM holds **both languages**; the builder selects by mode. One RDM serves fa, en and bi.
- Builders are pure functions of the RDM plus rendered figure files: `DocxBuilder.build(doc, mode) → Path`, `HtmlBuilder.print(doc, mode)`, `HtmlBuilder.dashboard(doc, mode, data)`. The Typst contingency of §3.2 would be one more builder over the same RDM.

### 9.3 Figure and table registry
```python
# geovalid_pro/plots/registry.py — interface sketch
@figure("collar.dz_map", chapter=3, order=70, size=Size.FULL_PORTRAIT,
        requires=("drv_collar_spatial", "drv_collar_method"),
        when="n_dem_sampled >= 5",                                  # safe expression (§5.11) over FigData fields
        caption_en="Collar elevation residual ΔZ = Z_collar − Z_topo against {dem_name}; diverging scale "
                   "centred on 0 m. n = {n} ({n_excluded} excluded: {excluded_reasons}).",
        caption_fa="باقیمانده ارتفاع دهانه گمانه ΔZ = Z دهانه − Z توپوگرافی نسبت به {dem_name}؛ مقیاس رنگی "
                   "واگرا با مرکز صفر متر. n = {n} ({n_excluded} مورد کنار گذاشته شده: {excluded_reasons}).",
        jorc_items=("T1.08",), version=1)
def collar_dz_map(data: "FigData", style: "Style", lang: Lang) -> "matplotlib.figure.Figure": ...
```

| Aspect | Decision |
|---|---|
| Selection | A figure is included when its `requires` products exist and `when` holds. Numbering is assigned **after** selection, so it has no gaps. |
| Numbering | Per chapter: Figure 3-7 / «شکل ۳-۷», Table 6-2 / «جدول ۶-۲». Order is (chapter, `order`, instance key), which is deterministic. Appendix items are numbered A-1, B-1, … |
| Multi-instance figures | `instances=` expands a figure per analyte, domain or campaign (e.g. a log-probability plot per element). Instances are numbered 6-4a, 6-4b, …, so chapter numbering stays stable when the element list changes. |
| Per-hole figures | The report includes only the holes the findings point to (top-issue holes, twins, representative holes; default ≤ 12 per chapter). The full set (strip logs, dip/azimuth vs depth for every hole) is an optional **hole atlas** PDF (`--atlas`), one page per hole, from the same render pool. |
| Captions | Templates over `FigData` fields. Lint requires `n`, `n_excluded` and a source line (table, release, DEM name) in every data caption (brief §15). |
| Size classes | `FULL_PORTRAIT` 160 × 200 mm, `HALF` 160 × 95 mm, `THIRD` 160 × 62 mm, `LANDSCAPE` 247 × 150 mm, `STRIP` 160 × 230 mm (A4, 25 mm margins). Fonts are set in points at final size; figures are never rescaled in the document. |
| Files | `figures/fig_03-07_collar-dz-map_fa.png` (300 dpi) and `.svg`, one set per language |
| Cache | Key = `sha256(figure key, figure version, FigData hash, style version, lang, size)`. A re-run that does not change a figure's data reuses it. |
| Tables | `@table` registry with the same selection, numbering and caption rules. Body tables are capped at `max_rows` (default 60); full listings go to an appendix (cap 500 rows) and always to the XLSX outputs. A 10 000-page PDF issue list is never produced. |

Every figure is also available in the GUI (§10.6) through the same builder function, so a GUI chart and its report figure cannot disagree.

### 9.4 Narrative generation: deterministic phrasebook engine
**No LLM is used, and none is needed.** The narrative is produced fully offline by a deterministic template engine; the same findings give the same text, byte for byte. Phrasebook entries are written natively in Persian and English by geologists (not machine-translated) and are versioned with the software. `phrasebook_sha256` is recorded in the report manifest.

**Findings.** `report.findings` turns results into typed facts:
```python
@dataclass(frozen=True)
class Finding:
    key: str                                  # "collar.dz_summary"
    chapter: int                              # §14.1 chapter
    values: Mapping[str, "Quantity | str | int | float | bool"]   # Quantity = value + unit + kind (grade, depth, pct, angle…)
    severity: Severity | None                 # strongest related issue, if any
    rule_ids: tuple[str, ...] = (); jorc_items: tuple[str, ...] = ()
    figures: tuple[str, ...] = (); tables: tuple[str, ...] = ()
    provenance: Mapping[str, str] = field(default_factory=dict)  # value name → product key / stats-object id / run_id
```

**Phrasebook entry** (`report/narrative/phrasebooks/collar.yaml`):
```yaml
- id: collar.dz.datum_offset.ellipsoidal
  finding: collar.dz_summary
  when: "abs_median_dz_m >= offset_warn_m and mad_dz_m < 0.5 * abs_median_dz_m and abs(median_dz_m - geoid_n_m) <= 1.0"
  priority: 90                                   # among matching entries the highest wins
  observe:
    en: "Collar elevations lie a median {abs_median_dz_m} m {above_below} the {dem_name} surface (MAD {mad_dz_m} m; n = {n}, {n_excluded} excluded)."
    fa: "تراز دهانه گمانه‌ها به‌طور میانه {abs_median_dz_m} متر {above_below} سطح {dem_name} است (MAD برابر {mad_dz_m} متر؛ n = {n}، {n_excluded} مورد کنار گذاشته شده)."
  interpret:
    en: >-
      An offset this uniform is a vertical-datum problem, not GPS noise. It equals the geoid undulation at the project
      centroid (N = {geoid_n_m} m, {geoid_model}), so the collar Z are most probably ellipsoidal heights from GNSS
      processed without a geoid model. Every RL-dependent product (level plans, pierce points, surfaces built from
      collars) inherits this {abs_median_dz_m} m bias.
    fa: >-
      جابه‌جایی با این میزان یکنواختی ناشی از مبنای ارتفاعی است، نه نوفه GPS. این مقدار با ارتفاع ژئوئید در مرکز محدوده
      (N = {geoid_n_m} متر، {geoid_model}) برابر است؛ بنابراین ارتفاع دهانه‌ها به احتمال زیاد ارتفاع بیضوی حاصل از GNSS
      بدون اعمال مدل ژئوئید است. همه محصولات وابسته به تراز (نقشه‌های تراز، نقاط برخورد، سطوح ساخته‌شده از دهانه‌ها)
      این سوگیری {abs_median_dz_m} متری را به ارث می‌برند.
  act:
    en: "Confirm the vertical datum with the survey contractor, then apply one datum-shift change set (COL-012) instead of draping collars individually."
    fa: "مبنای ارتفاعی را با پیمانکار نقشه‌برداری تأیید کنید و سپس به‌جای انطباق تک‌تک دهانه‌ها بر توپوگرافی، یک مجموعه تغییرات «جابه‌جایی مبنا» (COL-012) اعمال کنید."
    action: {code: CONFIRM_VERTICAL_DATUM, priority: P1, scope: project}
  labels:
    above_below: {pos: {en: above, fa: "بالاتر از"}, neg: {en: below, fa: "پایین‌تر از"}}
  cite: [fig.collar.dz_hist, fig.collar.dz_map, tab.collar.dz_by_campaign]
```

Engine rules:
- **Three slots: observe → interpret → act.** This turns brief §19 ("explain *why* an issue matters … and *what to do*") into structure. Lint fails a finding of severity ≥ WARNING whose selected entry has an empty `interpret` or `act` slot.
- **Selection.** For each finding, the entries whose `when` holds are ranked by `priority`, then `id`, and the first wins. Conditions use the safe expression evaluator of §5.11 in scalar mode. Every finding family ships a fallback entry, so a finding that matches nothing is a lint error, never a silent omission.
- **Thresholds are quoted with their origin**, e.g. "above the 5 m ERROR threshold (project profile kz_west_2026)". The reader always sees which number drove a statement.
- **Number formatting by quantity kind:** depths and ΔZ to 0.1 m in prose; grades to the analyte's display significant figures in its display unit (02 §1.8); percentages to 0 or 1 decimal; counts with thousands separators. fa uses Persian digits, `٫` and `٬` (§3.8). Each number span keeps its `finding:value` provenance, which the HTML carries as a `data-src` attribute.
- **Plurals and Persian conventions.** en uses `{n|hole|holes}` selectors. In Persian a counted noun stays singular («۳۷ گمانه»), so fa templates need no plural selectors. A build-time lint flags fa entries with missing zero-width non-joiners in common affixes («می شود» → «می‌شود», «گمانه ها» → «گمانه‌ها»).
- **Order.** Paragraphs follow the chapter's section order; within a section, by severity, then priority. Two findings with the same `cause` key share one interpretation instead of repeating it.

**Executive summary** (chapter 1) is assembled, not written separately:
- the DCI with its sensitivity range (§8.6) and traffic light;
- key findings: the highest-priority `interpret` sentence of each chapter with severity ≥ WARNING;
- the **top 10 critical issues**, aggregated by rule × table (ten distinct problems, not ten rows of one rule), ranked by severity, then affected metres inside logged mineralisation, then affected holes, then rule ID;
- waived CRITICAL issues with reviewer and reason (§7.6), unconfirmed inferences (02 §1.9), failed and disabled rules;
- the fit-for-purpose statement with its disclaimer (§8.5).

**Recommendations and action plan** (chapter 13) are compiled from the `act.action` records:
- priority classes: **P1** before any resource estimate; **P2** before the next release; **P3** practice improvement;
- each action states why (its interpret sentence), its scope (holes, metres, batches), its JORC items and an **effort estimate** from the profile's effort model, printed as a range (×0.7 to ×1.5) and labelled indicative:
```yaml
report:
  effort_model:                            # person-days
    RESURVEY_COLLAR_DGPS:   {unit: collar,  per_unit: 0.04, fixed: 2.0}
    REASSAY_BATCH:          {unit: batch,   per_unit: 0.5,  fixed: 1.0}
    RELOG_INTERVALS:        {unit: 100 m,   per_unit: 0.3,  fixed: 0.5}
    CONFIRM_VERTICAL_DATUM: {unit: project, per_unit: 1.0,  fixed: 0.0}
```

The CP/QP disclaimer (brief §19) is a fixed block on the reverse of the title page and directly above the fit-for-purpose statement, in each active language.

### 9.5 Language modes
| Element | `fa` | `en` | `bi` (decision) |
|---|---|---|---|
| Body narrative | fa | en | **Primary language** (`report.bi_primary`, default fa) |
| Chapter key-findings box | fa | en | **Both** |
| Executive summary, action plan, disclaimer | fa | en | **Both, in full** (primary first) |
| Headings, figure and table captions, table headers | fa | en | **Both** (secondary on the next line, secondary style) |
| Text inside figures | fa | en | Primary language |
| Glossary appendix | fa/en | fa/en | fa/en |
| Page direction | RTL | LTR | Primary language's; secondary paragraphs carry their own direction |
| Digits | Persian in prose and tables; Latin in IDs and coordinates (§3.8) | Latin | By paragraph language |

**Decision for `bi`.** A fully interleaved bilingual body doubles the page count and makes a 150-page report hard to read in either language. This design gives an English-speaking reviewer everything needed to navigate and audit a Persian report (every heading, caption and table header, each chapter's key findings, the executive summary and the action plan in both languages), with identical figure numbers across modes (§9.1). A complete second-language report costs only rendering time, because findings and figures are computed once: `--lang fa,en` produces both in one job. A fully parallel text, if required, is one more builder mode over the same RDM, not a redesign (Q1, §16).

### 9.6 DOCX builder (`report/docx_builder.py`)
- **Template-driven.** python-docx opens the Word-authored `reference_fa.dotx` or `reference_en.dotx`. Paragraph, character, table and caption styles, multilevel heading numbering and the header/footer layout live in the template, so the client restyles the report in Word without code changes. Branding (logo, "Arad/A.A" placeholder) comes from `project.branding` (02 §4.1).
- **RTL mechanics** as §3.8: `w:bidi` paragraphs, `w:rtl` runs, complex-script fonts and sizes, `w:bidiVisual` tables, `w:sectPr/w:bidi`. RDM spans of kind `id` and `number` become separate LTR runs.
- **Figures** are inserted as 300-dpi PNG at the exact size-class width, with bilingual alt text.
- **Fields.** Captions are chapter-numbered `SEQ` fields whose cached results are **pre-filled with the RDM numbers**, so they are correct even if the user declines Word's field update. Cross-references are `REF` fields to bookmarks. The TOC is a field updated on open (`w:updateFields`, §3.8).
- **Tables** use the template's table style: zebra rows; header row repeated on each page (`w:tblHeader`); rows never split across pages (`w:cantSplit`); units in headers; failures highlighted by cell shading from `Highlight` rules (e.g. CRM results outside ±3SD). Wide tables and maps go into landscape sections.
- **Page numbers** are `PAGE`/`NUMPAGES` fields. In fa documents they rely on Word's digit substitution for `fa-IR` runs; S-03 verifies this, and the fallback is Latin page numbers.
- **Stable output.** Core properties (author, created, modified) are set to the release values and parts are written in a fixed order, so the same release yields a byte-identical DOCX (tested).

### 9.7 HTML: print document and interactive dashboard (`report/html_builder.py`)
Both HTML outputs are rendered from the RDM with shared Jinja2 block partials (`templates/_blocks/*.j2`: paragraph, figure, table, callout), so the PDF and the dashboard present the same text, numbers and captions.

**Print HTML** (input to the PDF, §3.2):
- static: inline SVG figures (PNG for raster-heavy maps whose SVG would exceed 5 MB), no JavaScript;
- CSS print subset: `break-inside: avoid` on figures and table rows; `thead` repeated on each page (native in Chromium); widow and orphan control;
- landscape sections use CSS named pages (`page: landscape`) if S-01 confirms the pinned Chromium honours them. Otherwise the renderer prints the portrait and landscape runs as separate PDFs and pypdf concatenates them in order. In both cases page numbers and the outline are applied afterwards (§3.2 step 3).

**Dashboard HTML** (brief §14 item 5):
- **One self-contained file** that works from a USB stick or an e-mail attachment: fonts as WOFF2 data URIs, `plotly.min.js` embedded once (§3.8), data in `<script type="application/json">` blocks and a small vanilla `dashboard.js`. Nothing is fetched, not even local files (browsers block `fetch()` under `file://`).
- Content: DCI and component gauges; the JORC Table 1 matrix; issue counts by table × severity; a collar map coloured by score or inferred method; the key interactive figures of each chapter; and an **issue explorer** (filter, sort, search) over the 50 000 highest-ranked issues (configurable). Beyond that limit the dashboard holds the aggregated pivots and points to the complete XLSX/CSV issue log. Size budget: ≤ 40 MB at dataset L (§11.6).
- **Hardening.** Jinja2 autoescaping is on, so a hole ID such as `<script>` in client data renders as text. A Content-Security-Policy meta tag (`default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src data:; font-src data:`) makes outbound requests impossible even when the file is opened in a browser.

### 9.8 PDF
The renderer and its contingency are defined in §3.2. In addition:
- metadata: title, author (from settings), subject = release label and `version_id`, keywords = rule-catalogue and profile hashes; creation and modification dates set to the release time;
- PDF outline from the headings; internal links for the TOC, cross-references and issue references;
- **PDF/A is not produced.** Chromium does not emit PDF/A, and the usual converter (Ghostscript) is AGPL, which the licence policy bans (§3.10). If archival PDF/A is mandatory, a permissively licensed conversion path with veraPDF validation becomes a separate spike (Q9, §16).

### 9.9 Issue log and tabular outputs (`io/writers/issue_log.py`)
- **issues.xlsx** (XlsxWriter, `constant_memory`):
  - `README`: run metadata, filters applied, severity legend (fa/en);
  - `Issues`: all §1.3 fields plus `fingerprint`, `run_id` and JORC items; auto-filter, frozen header, severity colours;
  - pivot sheets by table × severity, by rule, by hole (top 500), by JORC item and by status.

  Beyond 1 048 575 issues the `Issues` sheet continues as `Issues_2`, …; the CSV is always one file.
- **issues.csv**: UTF-8 **with BOM**, so Excel opens Persian text correctly on double-click.
- **Formula-injection guard.** XlsxWriter runs with `strings_to_formulas=False`. In the CSV, a *text* cell starting with `=`, `+`, `-` or `@` that does not parse as a number is prefixed with `'`. This applies to the issue log only, never to the cleaned database, whose values must remain exactly as stored (02 §9.6).
- Every report table is also written to `tables.xlsx`, one sheet per table named by its number (`T06-02`), at full precision.

### 9.10 Report lint, manifest and reproducibility
`report/lint.py` runs on the RDM before any builder. A final report with lint errors is not written. A draft report is written with a visible "lint findings" page.

| Check | Error when |
|---|---|
| Placeholders | An unresolved `{…}`, `None`, `nan` or `inf`; an empty section; "TBD"-like text |
| References | A figure or table not referenced in the text; a reference to a missing anchor |
| Traceability | A number span without provenance |
| Interpretation | A finding ≥ WARNING without `interpret` and `act` text (§9.4) |
| Captions | Missing `n`, `n_excluded` or source line |
| Language parity | A string missing in an active language; Latin digits in fa prose numbers |
| Disclosure | Missing CP/QP disclaimer, rule-execution matrix (§5.1) or threshold appendix with provenance (§5.9) |
| Offline | Any `http(s)://`, `//cdn` or external `src`/`href` in HTML; any external relationship in the DOCX other than a plain hyperlink |

Outputs go to a new folder `<output>/<release label>_<mode>_<yyyymmdd-hhmm>/`: `report.docx`, `report.pdf`, `dashboard.html`, `figures/`, `tables.xlsx`, `issues.xlsx`, `issues.csv`, `profile.yaml` (resolved, with provenance), `run_metadata.json` (02 §5.9 fields and input hashes) and **`report_manifest.json`**. The manifest holds `run_id`, `version_id`, the recipe, profile, parameters and rule-catalogue hashes, the phrasebook, template, style and font hashes, the software version, and the SHA-256 of every output file.
- DOCX, PDF, HTML and the manifest are stored in the `.gvp` as `REPORT` blobs, and the figures of release reports as `FIGURE` blobs (02 §5.11). `audit_log` receives `REPORT_WRITTEN` with the manifest hash.
- **Reproducibility.** Regenerating a release report with the same software version yields identical text and numbers. DOCX and HTML are byte-identical (tested). PDFs are compared by extracted text, because Chromium's internal object order is not guaranteed to be stable.
- The title page prints the release label, `version_id`, the first 12 hex digits of `recipe_sha256` and the run date. This **release anchor** ties the issued document to one exact state of the project (§13.2).

### 9.11 Report job and timing
Report generation is a worker job (§1.4): findings → narrative → figure rendering in the process pool (≤ 4 processes, cached by data hash) → DOCX → print HTML → PDF (offscreen Qt WebEngine, two passes) → dashboard → issue log. Targets for dataset L, one language and ~150 figures: ≤ 4 min cold; ≤ 90 s when only the narrative or styling changed (§12.3).

---

## 10. GUI architecture

### 10.1 Application shell
- **Boot order** (`gui/app.py`): offline guard (§13.1) → logging and crash handler → fonts → settings (language) → `QTranslator`s (application `.qm` and Qt's `qtbase_fa.qm`) → layout direction → main window. At start-up the GUI process imports only Qt, pyqtgraph, `api`, pyarrow and duckdb. matplotlib loads with the first chart. scipy, scikit-learn, geopandas and rasterio serve the worker and are never imported at GUI start-up. Target cold start: ≤ 4 s (§12.3).
- **Main window.** A `QMainWindow` with a central workspace and dockable panels: Project (tables, layers, versions, runs), Workflow (§10.2), Issues (§10.4), Inspector (record in context), Map, Section, Strip log, Charts, Jobs/Log. Layouts are saved per user (`saveState` in QSettings), with three presets: Import, Review, Report.
- **Selection bus** (`gui/main_window.py`): one `QObject` with the signals `holeSelected(str)`, `issueSelected(int)`, `rowSelected(str, int)` (table, `row_uid`) and `extentRequested(QRectF)`. Every view publishes and subscribes. Clicking an issue centres the map on the collar, opens the hole's strip log at the interval, draws a section through the hole along its azimuth and fills the Inspector. Each of these is computed in `TaskPool` and painted when ready.
- **Banners:** *read-only* when the project is opened read-only (§4.4); *working version* when the user views Vw with change sets applied since the last release.

### 10.2 Workflow (the wizard of brief §16)
The §16 sequence is a **non-modal stepper**, not a modal `QWizard`. A real audit loops through review → fix → re-run several times, and a modal wizard would trap the user in that loop. Each step's state is derived from the project, so the stepper is always resumable and shows ✓ / ⚠ / ✗ per step.

| Step | View | Key interactions | API |
|---|---|---|---|
| 1 Create project | Form | Name fa/en, deposit type (selects the default profile), commodities, report language, branding | `api.project.create` |
| 2 Import files | Drop zone + file list | Drag files or folders. Per-file sniff preview (encoding, delimiter, header rows, sheets, Excel date system) with overrides. Access tier shown (§3.5). | `api.importing` (add sources, preview) |
| 3 Map fields & units | Mapping grid | Source column ↔ canonical field with score and evidence tooltip; unit per column; table type; "accept all above confidence"; mapping templates | `api.importing` (propose/confirm mapping) |
| 3b Decide inferences | Evidence cards | One card per inference (depth unit, analyte units, dip convention, azimuth reference, …) with its evidence waterfall (§6.9). Critical kinds are marked *required before release*. | `api.importing` (decide inferences) |
| 4 Set CRS | CRS panel + preview map | Offline EPSG search (proj.db); zone suggestion from coordinates; X/Y-swap and lat/long detections; local grid; vertical datum | same |
| 5 Topo / map / boundary | Layer list + map | Layer metadata: source, resolution, vertical CRS, vintage, RMSE, share of flat triangles (§6.8) | same |
| 6 Choose profile | Profile editor (§10.9) | Deposit profile, diff against base, threshold forms | `api.validation` |
| 7 Run | Job view | Stage list, progress, ETA, cancel | worker job `validate` |
| 8 Review | Review panel (§10.4) | Filter, inspect, bulk actions | `api.review` |
| 9 Fix / annotate | Change-set panel | Draft, undo, apply with reason | `api.review` |
| 10 Re-run | Job view | Incremental by default, full on request (§5.4.4) | worker job `validate` |
| 11 Export & report | Release + outputs | Release-gate checklist with links to the causes (§7.6); outputs; language mode | worker jobs `release`, `report`, `export` |

### 10.3 Dashboard
- Issue counts by table × severity (heat grid) and by family; new, fixed and reopened issues since the previous run.
- DCI gauge and component bars (custom `QPainter` widgets, A13), with the sensitivity range (§8.6).
- JORC Table 1 matrix (T1.01–T1.12) as traffic lights, plus NI 43-101 Items 11 and 12.
- Mini-map of hole scores; distribution of inferred collar-survey methods.
- Run health: rule-execution matrix summary (failed, disabled, not applicable), unconfirmed inferences, release-gate status.
- Every element is a link that filters the review panel.

### 10.4 Review panel
- **Layout:** a rule summary list (rule, title in the UI language, counts by status) next to the issue table; the Inspector dock shows the selected issue.
- **Filter bar:** severity, family, rule, table, hole pattern (glob), status, JORC item, campaign, text search on messages, *new since baseline*. Filters compile to one DuckDB query over the issue snapshot (§3.4) that returns a row permutation (§10.8): ≤ 300 ms at 1 M issues.
- **Record in context** (Inspector):
  - the offending row with ±5 neighbouring rows of the same hole from the canonical table;
  - raw and canonical values side by side (`*_raw` twins), with the normalisation-log entries that touched the cell;
  - the rule's evidence as a small table or chart (e.g. dogleg values of the adjacent stations);
  - the fix proposal as an old → new diff;
  - related holes (twins, crossing traces) as links;
  - the review history of the fingerprint.
- **Bulk actions:** *Accept fix*; *Ignore* (mandatory reason, with per-rule presets such as "genuine high grade, confirmed against the laboratory certificate"); *Edit value* (a dialog that creates a draft change with its reason); *Reset to open*. Each action writes its `issue_review` rows in one transaction (02 §5.6). There is no Save button: every decision is committed at once (§13.3).
- **Change-set panel:** DRAFT sets and their changes, a `QUndoStack` per set (§7.4), conflicts found on apply, *Apply* (reason pre-filled), *Revert* for applied sets.
- **Keyboard review:** `J`/`K` next/previous, `A` accept, `I` ignore, `E` edit, `Space` toggles the Inspector, `Ctrl+Z`/`Ctrl+Y` within the draft. Reviewing thousands of similar issues is a keyboard task.

### 10.5 Map, section and strip-log viewers (pyqtgraph)
| Viewer | Content | Rendering strategy |
|---|---|---|
| **Map (plan)** | Collars (symbol by inferred method or hole type; colour by any field, score or issue severity), traces, DEM hillshade, licence, geological map, issue markers | Aspect locked at 1:1 (`setAspectLocked`); coordinates in the project CRS with a lat/long readout. **All traces in one `PlotCurveItem`** with a `connect` array: one draw call for 5 000 holes. Collars and issue markers in a pixel-mode `ScatterPlotItem`. DEM as an `ImageItem` from a three-level pyramid. Polygons as `QPainterPath`s pre-simplified per zoom band. Labels only above a zoom threshold. Scale bar, north arrow (grid north, convergence noted) and grid ticks. |
| **Section** | Traces projected within a ± corridor; interval bands along the traces (any table or assay, from `drv_interval_master`); topographic profile; issue markers | Defined by a drawn line, a detected drill fence (§6.8) or *through this hole along its azimuth*. **Vertical exaggeration defaults to 1:1** and is printed on the view whenever it differs. |
| **Strip log** | Depth tracks: lithology, alteration (type + intensity), mineralisation, weathering, assays (log scale, BDL marked), CR/RQD, density, magnetic susceptibility, survey dip/azimuth with dogleg | Shared depth axis; track sets configurable and saved per project; issues drawn as hatched bands on the affected track |
| **3D** (optional) | Traces as tubes, DEM surface, licence, issues as glyphs | `pyvistaqt.QtInteractor` in a dock; imported lazily; separate installer component (§14.3). When it is absent, the menu entry says how to add it. |

- Picking in any viewer publishes to the selection bus.
- **Level of detail:** `setClipToView(True)` and automatic down-sampling on dense curves. Above ~200 k visible markers the map shows a binned density image until the user zooms in. S-08 validates the frame rates (§15).
- Viewers export PNG/SVG through the same furniture module as the report figures (`plots/furniture.py`).

### 10.6 Charts
- matplotlib `FigureCanvasQTAgg` hosts the **same figure builders** as the report (§9.3), called with the UI language.
- Data are prepared in `TaskPool`; drawing happens on the main thread (painting, §1.4). Charts with more than 50 k points use hexbin or rasterised artists, keeping a redraw ≤ 300 ms.
- The matplotlib navigation toolbar is kept. *Export figure* writes 300-dpi PNG + SVG with the report caption.

### 10.7 Background work: `TaskPool` and `JobRunner`
```python
# geovalid_pro/gui/workers — interface sketch
class TaskSignals(QObject):
    progress = Signal(int, int, str)      # done, total, message (UI language)
    result   = Signal(object, int)        # immutable payload (Arrow table, frozen dataclass), generation
    error    = Signal(object)             # ErrorInfo(kind, message_en, message_fa, log_ref)
    finished = Signal()

class Task(QRunnable):
    def __init__(self, fn: Callable[[CancelToken, ProgressSink], Any], *, topic: str, generation: int): ...
    def run(self) -> None: ...            # opens its own read-only SQLite connection and DuckDB cursor

class TaskPool:                           # QThreadPool with ≤ 4 threads (§1.4)
    def submit(self, fn, *, topic: str) -> "TaskHandle": ...   # a newer task on the same topic supersedes older ones

class JobRunner(QObject):                 # long jobs in the worker subprocess
    stage    = Signal(str, int, int)      # stage key, done, total
    log      = Signal(dict)
    finished = Signal(object)             # JobResult(exit_code, run_id, outputs)
    def start(self, job: "JobSpec") -> None: ...                # QProcess: geovalid.exe worker --job <job.json>
    def cancel(self, grace_s: float = 10.0) -> None: ...
```
- **Thread rules.** Worker threads never touch widgets or models. Results reach the main thread only through queued signals, and they are immutable (Arrow tables, frozen dataclasses). Each thread opens its own SQLite connection and DuckDB cursor; connections are never shared.
- **Supersession.** Each `submit` on a topic (e.g. `inspector`, `strip_log`) increments that topic's generation. Results of an older generation are dropped and its cancel token is set, so clicking quickly through issues never paints stale context.
- **Cancellation.**
  - Tasks: cooperative `CancelToken` checks inside loops.
  - Jobs: `cancel()` writes `{"t": "cancel"}` to the worker's stdin. The worker stops at the next checkpoint (§5.4.3), rolls back its open transaction, marks the run `CANCELLED` and exits with code 130 (§11.3). After the grace period, `QProcess.kill()` performs a hard cancel. This is safe because the worker writes in short transactions and blobs are content-addressed (§7.3); the next open marks the run as interrupted (§13.3).
- **Progress.** The worker emits NDJSON events (§11.5). The job view shows stages, progress and an ETA computed from the durations of the same stages in the project's previous runs.
- **One writing job per project** (§1.4). Further jobs (e.g. *Report* after *Run*) wait in the Jobs dock. Read-only tasks continue during a job, and the views reload the issue snapshot and products when it finishes.

### 10.8 Model/view for million-row tables
```python
class ArrowTableModel(QAbstractTableModel):
    """Read-only model over a pyarrow.Table (memory-mapped from the cache) with an optional row permutation."""
    def __init__(self, table: "pa.Table", columns: Sequence["ColumnSpec"], fmt: "Formatter"): ...
    def rowCount(self, parent=QModelIndex()) -> int: ...       # len(perm) or table.num_rows
    def columnCount(self, parent=QModelIndex()) -> int: ...
    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any: ...  # served from the block cache
    def headerData(self, section: int, orientation, role: int = Qt.DisplayRole) -> Any: ...
    def set_permutation(self, perm: "np.ndarray | None") -> None: ...           # int32; begin/endResetModel
    def set_overlay(self, overlay: Mapping[tuple[int, str], Any]) -> None: ...   # draft values, live statuses

class IssueTableModel(ArrowTableModel): ...    # Parquet issue snapshot (§1.4) + live review-status overlay
```
- **No copies.** The table stays in Arrow, memory-mapped from the cache. `data()` reads from a **block cache**: the first access to a row formats its block of 256 rows × visible columns once (localised numbers, labels) and keeps it in an LRU of ~200 blocks. A repaint of 50 rows × 15 columns costs well under 1 ms.
- **Sorting and filtering happen outside Qt.** DuckDB (or Arrow compute) runs them in `TaskPool` and returns an `int32` permutation, which the model swaps in. **`QSortFilterProxyModel` is not used**: it calls `data()` for every row, which costs seconds of Python at 1 M rows. Selection is preserved across permutations by key (`issue_id`, `row_uid`).
- **Fixed geometry.** Fixed row height (`QHeaderView.ResizeMode.Fixed`); column widths estimated from a 1 000-row sample, never from `resizeColumnsToContents` over the whole table.
- **Roles.** Display: formatted value. ToolTip: raw value and normalisation note. Foreground and Background: severity and draft-change marking. `UserRole`: the record key. Numeric columns use tabular figures and absolute right alignment in both languages.
- **No editing in grids.** Grids are read-only. *Edit value* opens a dialog that creates a draft change with its reason (§7.2). The model then shows the draft value through the overlay, in italics with a marker, without touching the data.
- **Clipboard** copies canonical values with Latin digits, tab-separated, so pasting into Excel or a modelling package is lossless.
- S-07 validates these figures at 1 M issues (§15).

### 10.9 Settings, profile and dictionary editors
- **Profile editor.** Forms are generated from the JSON Schema of each rule's `Params` (§5.2), so units, ranges, bilingual labels and defaults come from the code and the editor cannot drift from the rules. Each value shows its provenance (base / deposit / project) and can be reset to the parent's value. Saving uses ruamel round-trip, which preserves the client's comments. An invalid value is refused in the form, not at run time.
- **Dictionary editors** (codes, synonyms, map-unit ↔ lithology correlation, CRM values) edit SQLite reference tables. Every edit is logged as `REFERENCE_EDITED` (02 §5.8).
- **Application settings:** UI language, report defaults, reviewer display name, memory budget, cache location and size cap, backup retention, digit style in data grids.

### 10.10 Internationalisation and RTL
- **Two string sources, no duplication.**
  - UI chrome strings use `self.tr()`. `pyside6-lupdate` extracts them into `i18n/ts/geovalid_fa.ts`; they are translated in Qt Linguist against the glossary and compiled by `pyside6-lrelease` into `.qm` at build time.
  - Engine strings (rule titles, messages, enum and field labels, glossary) come from rule metadata and `i18n/labels/*.yaml`, and are never in `.ts`.
  - CI fails a release build on unfinished `.ts` entries or on mismatched `%1`/`%n` placeholders.
- **RTL mirroring.** In fa, `QGuiApplication.setLayoutDirection(Qt.RightToLeft)`. Menus, docks, forms, table column order and scroll bars mirror automatically. Directional icons (arrows, undo/redo, indent) have mirrored variants.
- **Never mirrored** (explicitly `Qt.LeftToRight`): map, section, strip log, 3D view and charts (east stays on the right, depth increases downwards, axes keep their mathematical orientation); coordinate and numeric inputs; ID fields; file paths; expression and YAML editors.
- **Dates.** Jalali display in fa through `QCalendar(QCalendar.System.Jalali)`, Gregorian in en, ISO in tooltips. Storage is always Gregorian (02 §6.3).
- **Digits.** fa labels and prose use Persian digits. Data grids default to Latin digits (setting); the clipboard always uses Latin digits.
- **A language change takes effect on restart.** Live re-translation of every widget, together with a change of layout direction and saved dock states, is a large test surface for little user benefit.
- **Fonts:** Vazirmatn in fa, Inter in en (§3.8).

### 10.11 Display, accessibility and robustness
- Qt 6 high-DPI scaling with `PassThrough` rounding, so laptops at 125 % and 150 % scaling render sharply.
- Minimum window 1280 × 720. The Review layout stays usable at 1366 × 768, common on field-office laptops.
- Severity is never shown by colour alone: an icon shape and text accompany it, and palettes are colour-blind safe (brief §15).
- Wizard, review panel and dialogs are fully keyboard-operable.
- An exception in a slot is caught by the global handler. The user sees a bilingual error dialog with the crash-bundle option (§13.3), and the application continues.

### 10.12 GUI testing
- pytest-qt with `QT_QPA_PLATFORM=offscreen`: wizard flows on synthetic S; review actions writing the correct `issue_review` rows; cancellation and supersession.
- Golden screenshots in fa and en of the key views (dashboard, review panel, mapping grid, evidence cards), compared with a tolerance, so RTL regressions are caught visually.
- Model tests on 1 M synthetic issues count `data()` calls per repaint and fail above budget.
- Packaging CI runs `geovalid-pro.exe --self-test` on the frozen build (§14.6): it opens the main window offscreen, loads synthetic S, renders a map and a chart, and exits with 0.

---

## 11. Command-line interface

### 11.1 Principles
- `geovalid` is a thin `click` application over `geovalid_pro.api`. It is the same code path the GUI's worker uses (A1), so a batch result is the result the GUI would show.
- **Non-interactive by default.** The CLI never prompts unless `--interactive` is given and stdin is a terminal. Decisions a person makes in the GUI (mapping confirmation, inference decisions) come from files (§11.4); the audit trail records the file and its hash.
- **Machine-readable.** `--json` prints one JSON document on stdout. Progress and logs go to stderr. Exit codes are stable (§11.3).
- CLI messages default to English (`--lang fa` is available), because Windows consoles render Persian RTL poorly. Reports and issue logs do not depend on this setting.
- Output is UTF-8 on all platforms (`sys.stdout.reconfigure(encoding="utf-8")`).

### 11.2 Commands
Global options: `--project/-p PATH`, `--json`, `--quiet/-q`, `--verbose/-v`, `--log-file PATH`, `--progress {auto,bar,ndjson,none}`, `--lang {en,fa}`, `--memory-budget SIZE`, `--threads N`, `--version`.

| Command | Purpose | Key options |
|---|---|---|
| `run` | End-to-end batch: optional import → build Vb → full validation → score → optional release → report → optional export | `--profile`, `--source PATH…`, `--mapping-template`, `--decisions`, `--accept-proposed-mapping`, `--release LABEL`, `--report {fa,en,bi}[,…]`, `--format docx,pdf,html`, `--export TARGET…`, `--out DIR`, `--fail-on`, `--baseline` |
| `validate` | Validation run on the working version; prints the summary | `--profile`, `--rules "COL-*,SUR-010"`, `--tables assay`, `--full`, `--fail-on`, `--baseline`, `--junit FILE`, `--issues FILE.csv` |
| `report` | Report from a release, or from Vw with `--draft` (watermarked) | `--release LABEL` \| `--draft`, `--lang`, `--format`, `--atlas`, `--out` |
| `export` | Software, GIS, cleaned-database and issue-log exports, **from a release only** (A18) | `--release`, `--to {leapfrog,datamine,micromine,surpac,vulcan,generic,gis,cleaned,issues}`, `--export-profile`, `--out` |
| `diff` | VER comparison: two versions, two projects, or a version against a software export | `--from`, `--to`, `--other PROJECT.gvp`, `--against-export DIR --preset leapfrog`, `--out diff.xlsx`, `--fail-on-change` |
| `profile` | `list`; `show NAME [--resolved] [--provenance]`; `validate FILE`; `init --extends porphyry_cu`; `diff A B`; `catalogue [--format md,xlsx,yaml] [--lang]` | — |
| `gen-synthetic` | Synthetic database with injected errors and a ground-truth manifest (§11.6) | `--size {S,M,L,XL}`, `--seed`, `--deposit`, `--inject {all,none,RULE_IDS}`, `--rate`, `--format {gvp,csv,xlsx,sqlite}`, `--out` |
| `project` | `create`, `info`, `verify` (§13.2), `release`, `history`, `backup`, `migrate`, `unlock` (stale lock on this host only, §4.4) | — |
| `worker` | Internal: runs one job for the GUI (§11.5); hidden from help | `--job FILE` |

The brief's example works as written:
```
geovalid run --project x.gvp --profile porphyry_cu.yaml --report fa
```
Without `--release`, this validates, scores and writes a **draft** report, and says so on stderr. A final report needs `--release LABEL`, which must first pass the release gates (§7.6). `--export` without `--release` is a usage error (exit 2), because exports never come from a working version.

### 11.3 Exit codes
| Code | Name | Meaning |
|---|---|---|
| 0 | `OK` | Completed; no issue at or above `--fail-on` |
| 1 | `FINDINGS` | Completed; at least one issue at or above `--fail-on` (with `--baseline`: at least one *new* such issue) |
| 2 | `USAGE` | Invalid arguments, profile, decisions file or export profile (e.g. an unknown rule ID or parameter, §5.9) |
| 3 | `INPUT` | A source is unreadable; mapping is incomplete for a required field; an external file is missing or fails its hash (02 §8) |
| 4 | `PROJECT` | Project missing, locked by another instance, read-only, written by a newer schema, or failing integrity or audit-chain verification on open |
| 5 | `GATE` | A release gate or the report lint failed; the failed gates are listed |
| 6 | `RULE_FAILURE` | Completed, but at least one rule `FAILED` (§5.4.5): results are incomplete |
| 7 | `OFFLINE_VIOLATION` | The offline guard blocked a network attempt (§13.1); treated as a defect |
| 70 | `INTERNAL` | Unexpected error; a crash bundle was written (§13.3) |
| 130 | `CANCELLED` | Interrupted (Ctrl+C or cancel from the GUI); the run is marked `CANCELLED` |

- When several conditions apply, the most fundamental wins: **2 > 4 > 3 > 70 > 7 > 6 > 5 > 1 > 0**. A run with failed rules and findings exits 6, because its findings are incomplete.
- `--fail-on {CRITICAL,ERROR,WARNING,INFO,never}`; the default is `CRITICAL`. Issues `ignored` with a reason never count.
- **Ratchet:** `--baseline <release label | run_id>` counts only fingerprints absent from the baseline. A new client delivery then fails CI only if it introduces new problems, not because of known and documented ones.

### 11.4 Non-interactive decisions
```yaml
# decisions.yaml — applied as CONFIRMED inferences; decided_by and the file hash go to audit_log
decided_by: "A.A"
mapping_templates: [templates/acquire_kz_west.yaml]
inferences:
  - {kind: CRS,            value: 32639}
  - {kind: DEPTH_UNIT,     table: "*",    value: M}
  - {kind: DIP_CONVENTION, value: NEGATIVE_DOWN}
  - {kind: AZ_REFERENCE,   table: survey, campaign: PH1-2014, value: MAG}
  - {kind: ANALYTE_UNIT,   table: assay,  field: Au_FA, value: ppm}
```
- Without a decisions file, `run` proceeds with provisional top-ranked values exactly as the GUI does (02 §1.9), and a release attempt then fails gate 2 (exit 5). Batch use can never pass a gate by accident.
- `--accept-proposed-mapping` accepts mapping candidates above the confidence threshold. Required fields that remain unmatched still exit 3.

### 11.5 Worker protocol (`geovalid worker`)
- The GUI writes a job manifest (`job.json`: job kind, project path, parameters, `job_id`) and starts `geovalid.exe worker --job job.json`.
- **stdout carries NDJSON events**, one per line, flushed immediately:
```json
{"t":"stage","job":"…","stage":"rules.INT","done":14,"total":42,"ts":"…"}
{"t":"progress","job":"…","done":312000,"total":1050000,"msg_en":"INT-002 lithology","msg_fa":"INT-002 سنگ‌شناسی"}
{"t":"log","level":"WARNING","logger":"io.readers.access","msg":"…"}
{"t":"heartbeat","rss_mb":3120,"ts":"…"}
{"t":"result","exit":0,"run_id":"…","outputs":[{"path":"…","sha256":"…"}]}
```
- **stdin** accepts `{"t":"cancel"}`.
- A dedicated thread sends a heartbeat every 2 s. If none arrives for 60 s, the GUI marks the job unresponsive and offers a hard cancel; it never kills the worker on its own.
- `--progress ndjson` makes any CLI command emit the same events on stderr, for CI wrappers.

### 11.6 Synthetic databases (`gen-synthetic`)
| Size | Holes | Metres | Interval rows (all interval tables) | Survey stations | Samples | Assay determinations (long) | Use |
|---|---|---|---|---|---|---|---|
| S | 50 | 10 k | 10 k | 1 k | 3 k | 120 k | Unit and rule tests |
| M | 1 000 | 200 k | 210 k | 20 k | 60 k | 2.4 M | Rule budgets (§5.12); CI on every pull request |
| **L** | **5 000** | **1 000 k** | **1.05 M** | **100 k** | **300 k** | **12 M** | Brief §16 target; nightly benchmark (§12) |
| XL | 10 000 | 2 500 k | 2.6 M | 200 k | 750 k | 30 M | Stress test; no timing target |

- **L composition:** lithology 150 k, alteration 150 k (+ 250 k observation rows), mineralisation 100 k, weathering 25 k, geotech runs 330 k and samples 300 k (10 % QC) interval rows, plus 160 k point rows (density, magnetic susceptibility, structure); 40 analytes.
- The generator first builds geologically coherent data: a porphyry or epithermal model with lithology domains, grade shells and an oxidation profile, realistic survey drift, and collar methods that differ by campaign. It then injects errors at a controlled rate. `ground_truth.json` lists every injection (rule ID, table, record key, expected fingerprint); the rule tests of §5.12 measure recall and false positives against it.
- CSV/XLSX outputs have deliberately messy headers, encodings and Persian header names, so the import path is exercised as well.

### 11.7 CI example
```yaml
# client-side CI on a new database delivery (any runner with the CLI installed)
- run: >
    geovalid run -p kz_west.gvp --source deliveries/2026-11/ --mapping-template templates/acquire_kz_west.yaml
    --decisions decisions.yaml --profile kz_west.yaml --baseline "Release MRE 2026-06" --fail-on ERROR
    --junit out/validation.xml --json > out/summary.json
```
The JUnit XML has one test suite per family and one test case per rule × table. A test case fails when it holds issues at or above `--fail-on` (the first 100 are listed). CI dashboards then show, for example, "SUR-010 survey: 12 new ERRORs" without custom tooling.

---

## 12. Performance plan

### 12.1 Reference workload and machine
- **Workload:** synthetic **L** (§11.6): 5 000 holes, 1 000 km drilled, 1.05 M interval rows, 100 k survey stations, 300 k samples, 12 M assay determinations; a 5 m DEM over 10 × 10 km (4 M cells) or a 1 M-triangle TIN; a 1:25 000 geological map with 2 000 polygons; ≈ 400 k composites at 2 m. The `.gvp` is ≈ 1.5–2.5 GB with embedded sources.
- **Reference laptop** (the "normal laptop" of brief §16): Windows 11 x64; 4 performance cores / 8 threads at ≥ 2.5 GHz base (Core i5-1240P or Ryzen 5 7530U class); **16 GB RAM**; NVMe SSD; no discrete GPU.
- **Minimum machine:** 8 GB RAM, 4 cores, SSD. Every function works; targets relax to 2×, and the memory budget scales (§12.2).
- Spinning disks and network drives are outside the targets (§4.4).

### 12.2 Memory budget
- **Worker budget** `B = clamp(0.5 × physical RAM, 3 GB, 12 GB)`: 8 GB on the reference laptop, 4 GB on the minimum machine. It can be overridden in settings or with `--memory-budget`.
- **GUI process:** ≤ 1.5 GB at dataset L (memory-mapped 1 M-issue snapshot, viewers, block caches).

| Consumer (worker, B = 8 GB) | Allowance | Control |
|---|---|---|
| Interpreter and native libraries | 0.6 GB | Fixed |
| Active task working set (projected columns + temporaries) | ≤ 1.5 GB | Mandatory column projection (§4.3); per-analyte assay parts (§4.1); hole-batched execution (below) |
| L1 product cache | ≤ 2.0 GB | LRU + reference counts (§5.4.2, §6.1); spill to L2 |
| DuckDB | ≤ min(25 % of RAM, B − memory in use) | `memory_limit`; spill to `temp_directory` in the cache (§3.4) |
| Issue buffers (sink, fingerprints, messages) | ≤ 0.5 GB | 50 k-row batches |
| Headroom (allocator fragmentation, BLAS buffers) | remainder, ≥ 1.4 GB | — |

- **Monitor.** A psutil thread samples RSS every 500 ms. At 85 % of B the L1 cache is evicted to L2 and `gc.collect()` runs.
- **Chunking.** Before each task the executor estimates its working set (`rows × projected bytes × rule multiplier`, default multiplier 4). A hole-grouped rule or product whose estimate exceeds the remaining budget runs in **batches of 500 holes**. Every hole-grouped rule declares `chunkable=True` and is tested to give identical output in chunked mode.
- At 100 % of B with nothing left to evict, the job stops with a clear message (task, estimate, budget) instead of driving Windows into paging. The run is marked `FAILED` (exit 6); nothing is corrupted.
- **Expected peak at L: ≈ 4–5 GB**, dominated by `drv_interval_master` (~750 k rows × ~80 columns ≈ 0.5 GB) held together with `drv_assay_wide` and the spatial products.

### 12.3 Benchmark targets
Reference laptop, dataset L, warm OS file cache. *Cold* means empty product and result caches.

| Operation | Target | Hard limit (CI gate) |
|---|---|---|
| GUI cold start to main window (installed build) | ≤ 4 s | 8 s |
| Open project L to dashboard: cache present / first open (blob extraction and hash verification) | ≤ 5 s / ≤ 20 s | 10 s / 45 s |
| Import + normalise + build Vb from CSV (≈ 1.2 GB of text) | ≤ 3 min | 5 min |
| Same from XLSX workbooks | ≤ 6 min | 10 min |
| **Full validation, all rules, cold caches** | **≤ 150 s** | **180 s** |
| Incremental re-run after a typical review change set (one table, ≤ 1 000 changes) | ≤ 45 s | 90 s |
| Desurvey, 5 000 holes, all three methods | ≤ 3 s | 6 s |
| Local Moran's I, 400 k composites, k = 8, one analyte (two-stage inference, §12.4) | ≤ 5 s | 10 s |
| Report, one language, ~150 figures, DOCX + PDF + HTML: cold / figures cached | ≤ 4 min / ≤ 90 s | 6 min / 3 min |
| Leapfrog CSV export set | ≤ 30 s | 60 s |
| Version diff of two L versions | ≤ 60 s | 120 s |
| Issue filter or sort, 1 M issues (GUI) | ≤ 300 ms | 1 s |
| Issue click → Inspector, strip log and map updated | ≤ 200 ms | 500 ms |
| Map pan/zoom, 5 000 traces + 100 k markers | ≥ 30 fps | 15 fps |
| Peak worker RSS during full validation | ≤ 5 GB | 6 GB |

The incremental worst case is an edit of assay values, which cascades through `drv_assay_wide`, `drv_interval_master`, composites and the spatial rules. Collar-only and logging edits typically re-run in ≤ 15 s.

**Budget for full validation (L, ≤ 150 s).** Each rule has its own budget, measured on M and extrapolated (§5.12). The budgets must sum to the target:

| Step | s | Step | s |
|---|---|---|---|
| Load and project columns | 5 | IMP, COL, SUR rules | 10 |
| `drv_trace` + `drv_trace_compare` | 3 | INT rules (6 tables + extensions) | 15 |
| `drv_collar_spatial` (DEM sampling, overlays, KD-tree) | 3 | ASY rules (40 analytes) | 12 |
| `drv_collar_method` | 2 | QAQ rules | 5 |
| `drv_assay_wide` (DuckDB pivot, 12 M rows) | 10 | LIT, GEO, ALT, MIN, WTH, DEN, MAG, STR, SMP rules | 15 |
| `drv_qaqc_*` | 5 | CRS and SPA rules (Moran's I for 3 commodities, trace proximity, contacts) | 25 |
| `drv_interval_master` | 12 | Post-processing: bands, messages, fingerprints, carry-over (~200 k issues) | 5 |
| `drv_composite` | 5 | Issue sink (SQLite + Parquet snapshot); scoring with sensitivity | 10 |
| | | **Total** | **142** |

The rule-execution matrix (§5.1) records each task's runtime and peak memory, so a rule that is slow on a particular client database is visible in the report appendix.

### 12.4 Techniques
| Technique | Applied to |
|---|---|
| Vectorised kernels; no per-row Python | All rules and products (§5.5, §6.3) |
| Mandatory column projection; Arrow-backed strings; categoricals for codes | All reads (§4.3) |
| One Parquet part per analyte; row-group pruning by hole and analyte | Assay rules, change-set apply, incremental runs (§4.1) |
| Column-hash result cache and product cache | Incremental re-runs (§5.4.4, §6.1) |
| Column-wise rebuild of wide products: `drv_assay_wide` and `drv_interval_master` rebuild only the analyte columns whose part hashes changed | Incremental re-runs after assay edits |
| Just-in-time products with reference counting | Peak memory (§5.4.2) |
| DuckDB out-of-core joins and pivots | Wide assay table, QA/QC joins, diffs, issue aggregation (§3.4) |
| One global `searchsorted` on composite keys | Point-in-interval, contacts, trace interpolation (§5.5, §6.3) |
| KD-trees cached by point-set hash | Spacing, near duplicates, proximity, spatial weights (§6.8) |
| **Two-stage local Moran's I:** analytical randomisation z-scores for every location, then 999 conditional permutations only for candidates with \|z\| ≥ 1.5; BH-FDR over the combined p-values. Every reported SPA-001 issue therefore carries a permutation p-value, at ~5 % of the full permutation cost. | SPA-001 (refines §6.8) |
| Chunked, seeded permutations | Ripley envelopes, Moran candidates (§6.8) |
| Process pool and data-hash cache for figures | Reports (§9.3) |
| Bulk SQLite inserts (`executemany`, 50 k rows per transaction, indexes built after bulk load) | Issue sink, import |
| Memory-mapped Parquet and permutation-based model/view | Review panel (§10.8) |

### 12.5 Benchmark governance
- `tests/bench` (pytest-benchmark) covers the §12.3 table on S, M and L.
- **Nightly on a dedicated reference laptop** (self-hosted runner, Windows 11, 16 GB). Hosted CI runners have variable CPUs and noisy neighbours, so they run M only, against a loose 2× gate.
- A regression of more than 20 % against the rolling median of the last 10 nightly runs fails the build. A hard-limit breach blocks a release.
- py-spy flame graphs and memory high-water marks are archived for each nightly run.
- XL runs weekly for scaling trends. It has no timing target, only the requirement to finish within the memory budget.

---

## 13. Security, robustness and the offline guarantee

### 13.1 Offline guarantee
**Statement.** GEOVALID PRO makes no network connection at any time: no telemetry, no update check, no licence activation, no CDN, no map tiles, no online CRS or geoid grids, no crash upload. This is enforced in layers and proven in CI (A16).

| Layer | Mechanism |
|---|---|
| Code | ruff `banned-api` and import-linter forbid `urllib.request`, `http.client`, `ftplib`, `smtplib`, `requests`, `httpx`, `aiohttp`, direct `socket` use (outside `core/offline.py`) and `webbrowser` (outside the local-file opener in `gui/app.py`) anywhere in `geovalid_pro` |
| Python sockets | `core.offline.install_guard()` runs first in every process (GUI, CLI, worker, figure-pool processes). It wraps `socket.socket.connect`/`connect_ex`, `socket.create_connection` and `socket.getaddrinfo`, so any `AF_INET`/`AF_INET6` use raises `OfflineViolation` and is logged with its stack. `AF_UNIX` and Windows named pipes (used by multiprocessing) are unaffected. |
| PROJ / pyproj | `PROJ_NETWORK=OFF`, `pyproj.network.set_network_enabled(False)`, `PROJ_DATA` pointing at the bundled data; geoid grids are bundled (`resources/geoid`, §2.1) |
| GDAL (pyogrio, rasterio) | `io` refuses paths with `/vsicurl/`, `/vsis3/`, `/vsigs/`, `/vsiaz/`, `http(s)://` or `ftp://` before GDAL sees them. `GDAL_HTTP_*` variables are cleared and `CPL_VSIL_CURL_ALLOWED_EXTENSIONS` is set to an impossible value. Where present, the **LIBKML driver is skipped** (`GDAL_SKIP=LIBKML`), because KML `NetworkLink` elements could be followed; the plain KML driver does not fetch. |
| DuckDB | Extension auto-install and auto-load off; extension directory set to an empty read-only folder; configuration locked (§3.4). `httpfs` can never load. |
| Qt WebEngine | `QWebEngineUrlRequestInterceptor` allows only `file:`, `data:` and `qrc:`. JavaScript is off in the print profile. Chromium flags: `--disable-background-networking --disable-component-update --dns-prefetch-disable --no-pings`. Off-the-record profile with no persistent storage. |
| Outputs | Report lint forbids external references in HTML and DOCX (§9.10); the dashboard carries a strict CSP (§9.7) |
| Help | The user manual (fa/en) is bundled and opens locally in the QtPdf viewer |

**Proof in CI.**
- Unit test: in each process type, the guard raises on `socket.create_connection(("example.org", 80))`.
- **No-network job:** the full workflow (generate L → import → validate → report fa, en and bi → all exports → diff) runs on Linux in a container started with `--network none`, and on the installed Windows build behind an outbound-deny firewall rule for the install folder (`New-NetFirewallRule -Direction Outbound -Action Block`). The job asserts zero `OfflineViolation` log entries and results identical to a run with the network available.

### 13.2 File integrity and hashing
- **SHA-256 everywhere**, streamed in 8 MiB blocks (OpenSSL-backed `hashlib`, ~1–2 GB/s on CPUs with SHA extensions):
  - sources: hashed at import; re-verified on open (external sources) and at release (gate 5, §7.6);
  - blobs: content-addressed and verified when extracted to the cache (§4.2);
  - runs: every input listed with its hash in `run_input` (02 §5.9);
  - outputs: every file of a report or export listed in its manifest (§9.10), and `REPORT_WRITTEN`/`EXPORT_WRITTEN` logged with the manifest hash.
- **`geovalid project verify`** (GUI: *Project → Verify integrity*) runs `PRAGMA integrity_check` and checks every blob hash, every manifest, the audit-log chain and the external sources. It exits 0 or 4.
- **What the hash chain proves, and what it does not.** The `audit_log` chain (02 §5.8) detects accidental corruption and naive edits. Anyone with SQLite and this specification could rebuild a consistent chain, so on its own it does not resist a knowledgeable actor. The **release anchor** closes that gap: label, `version_id`, `recipe_sha256` and the `entry_hash` of the release event are printed on the report title page and written to the manifest (§9.10). Once a report is issued, any later alteration of that release is shown by comparing the project with the anchor in the issued document. Digital signatures (PKI) are not in scope for v1 (Q6, §16).

### 13.3 Crash safety and autosave
- **No unsaved state exists.** Every decision (mapping, inference, review status, draft change, profile edit) is committed to the `.gvp` immediately in a short SQLite transaction, so review work has no Save command. *Save as* is a `VACUUM INTO` snapshot (§4.1). UI state (layout, filters, last selection) lives in QSettings per user and project.
- **Atomic writes.** Blobs are written first, then manifests and status in one transaction (§7.3); `synchronous=FULL` is used around change-set apply, release, rebase and migration. Exported files are written as `*.partial` and renamed when complete.
- **Recovery after an unclean shutdown.** On open, a lock left by a dead process on this host (§4.4) triggers recovery:
  1. SQLite replays the WAL, then `PRAGMA quick_check` runs;
  2. runs still `RUNNING` become `FAILED` with the note "interrupted";
  3. orphan blobs are garbage-collected and stale `*.partial` files are removed.

  The dashboard keeps showing the last `COMPLETED` run; a partial run is never presented as current.
- **Rolling backups** by `VACUUM INTO` into `<project>.gvp.backups/`: on open when the newest backup is older than 24 h, and before every migration, release and rebase. The last 3 are kept (setting). Backups are full copies, so for large projects the backup folder can be placed on another disk.
- **A worker crash** (a native fault in GDAL, the ACE driver or Chromium) affects only its job. The GUI sees the exit code or the missing heartbeat, marks the job failed and keeps all review work.
- **Crash bundle.** `faulthandler` is enabled in every process and writes to the log. `sys.excepthook`, `threading.excepthook` and a Qt message handler route all errors to logging. After a crash the user can create a zip containing logs, the run manifest, software and dependency versions and platform details, but **no project data**. The user can inspect it and send it by their own means; nothing is sent automatically.
- **Disk space.** Import, release, report and backup compare free space with an estimate first, and refuse with a clear message rather than failing midway.

### 13.4 Logging
- Python `logging`, configured in `core/log.py`. Handlers: rotating JSON-lines files (10 MB × 10) in `%LOCALAPPDATA%\geovalid_pro\logs\` (`gui.log`, `cli.log`, `worker-<job_id>.log`); stderr for the CLI; the job-event stream for the GUI (§11.5).
- Fields: `ts` (UTC), `level`, `logger`, `process`, `thread`, `job_id`, `run_id`, `rule_id`, `msg`, structured `extra`.
- Library output is captured: `logging.captureWarnings(True)`; GDAL/CPL errors through the pyogrio and rasterio error handlers; Qt messages through `qInstallMessageHandler`.
- **Run log inside the project.** A run's WARNING-and-above records, rule tracebacks (§5.4.5) and per-task timings are stored with the run as a zstd JSON-lines blob. This needs one more blob kind, `RUN_LOG`, in 02 §5.11 (change request to the schema).
- **Confidentiality.** Data values are not logged at INFO or above. DEBUG logging with values is available only in an explicit diagnostic mode, which a banner shows while it is on.

### 13.5 Untrusted inputs
Client files, `.gvp` projects received from other users and profiles are all treated as untrusted. **Opening any of them must not execute code.**

| Input | Protection |
|---|---|
| XML-based formats (XLSX, KML, DOCX templates) | defusedxml; entity expansion disabled |
| ZIP containers (XLSX, KMZ, DOCX) | Limits on total uncompressed size and compression ratio (zip-bomb guard); member paths containing `..` or absolute paths are refused |
| Excel | Formulas are never evaluated: calamine reads cached values, and a formula cell without a cached value raises an `IMP-*` WARNING. VBA in `.xlsm`/`.xls` is never executed or loaded. |
| CSV and text | Field-size and line-length limits; bytes are never decoded with silent `errors="ignore"` (02 N01) |
| `.gvp` from another user | `PRAGMA trusted_schema=OFF`; `SQLITE_DBCONFIG_DEFENSIVE` (`Connection.setconfig`, Python ≥ 3.12); extension loading disabled. The schema is compared with the expected DDL for its `user_version`; unexpected triggers, views or tables force a read-only open with a warning. **No pickle anywhere** in project data, cache or job files: Parquet, JSON and SQLite only. |
| Profiles (YAML) | ruamel safe loading, so no Python object tags; unknown keys rejected (§5.9); expressions through the AST whitelist (§5.11), never `eval` |
| Rule packs (Python) | Disabled by default; enabled per organisation, each file pinned by SHA-256 (§5.11) |
| Templates | User-editable Jinja2 templates run in `SandboxedEnvironment` with autoescaping |
| SQL sources | Read-only `SELECT`; table names quoted as identifiers; parameters bound; passwords never stored (§3.9) |
| Access databases | Opened from a temporary copy (§3.5) |

### 13.6 Confidentiality and identity
- Exploration data are commercially sensitive. No data leave the machine (§13.1), logs exclude values (§13.4) and crash bundles exclude data (§13.3).
- **At-rest encryption is not built into v1.** The recommended control is full-disk encryption (BitLocker) on workstations and backup disks. Built-in encryption (SQLCipher) would add a native dependency and a key-management problem (Q7, §16).
- Identity is the OS login plus a display name; there is no authentication (§7.7).

---

## 14. Packaging and distribution

### 14.1 Decision: PyInstaller one-dir (A15)
| Criterion | **PyInstaller 6, one-dir** (chosen) | Nuitka (standalone) | PyInstaller one-file | Embedded Python + wheels / conda constructor |
|---|---|---|---|---|
| PySide6 + Qt WebEngine | Maintained hooks (QtWebEngineProcess, resources, ICU) | Supported plug-in; more configuration | Same hooks | Works (PyPI wheels) |
| Scientific/GIS stack (numpy, scipy, pyarrow, two GDALs, pyproj data, matplotlib) | Community hooks cover all of it | Usually works; compile problems need per-package flags | Same | Works unchanged |
| Build time, full stack | 5–10 min | 45–90 min (C compilation of the stack) | 5–10 min | ~5 min |
| Start-up | ~2–4 s (DLL loading dominates) | ~10–20 % faster | +10–30 s: unpacks ~1 GB to `%TEMP%` at every start | ~3–5 s |
| LGPL replaceability | Separate DLLs | Separate DLLs | Libraries hidden in an archive | Separate DLLs |
| Antivirus false positives | Low with a self-built, signed bootloader | Low | **High** (self-extracting pattern) | Low |
| Source protection | Weak (bytecode archive) | Moderate (compiled C) | Weak | None |

**Decision.** PyInstaller one-dir. It has the most mature hooks for exactly this stack, it builds in minutes (essential when packaging runs on every merge from Phase 1), and it keeps the LGPL libraries replaceable. Nuitka's advantages (somewhat faster start-up, harder decompilation) do not justify a 45–90-minute build and a second set of packaging problems. One-file is rejected for start-up time, antivirus behaviour and LGPL compliance. **Source protection is not a goal**; if the client requires it, Nuitka can be evaluated later for `geovalid_pro` alone (Q10, §16).

### 14.2 Bundle layout
```
GEOVALID PRO\
├── geovalid-pro.exe      GUI (windowed subsystem)
├── geovalid.exe          CLI and worker (console subsystem)
├── _internal\            shared by both executables: python312.dll, Qt and native DLLs, packages
│   ├── PySide6\          Qt6*.dll, QtWebEngineProcess.exe, resources\, translations\ (en, fa only)
│   ├── geovalid_pro\resources\   fonts, geomag, geoid, profiles, dictionaries, js, report templates
│   └── …
├── manual\               user manual fa/en (PDF, built by the report pipeline itself)
└── licences\             third-party notices, OFL and LGPL texts with source pointers, SBOM (CycloneDX)
```
- **Two executables in one `COLLECT`.** A windowed executable cannot serve a console, and a console executable shows a window when started by a GUI. The GUI therefore launches workers as `geovalid.exe worker`; QProcess creates them with `CREATE_NO_WINDOW` (Qt's behaviour when the parent has no console), which S-10 verifies.
- **Build-time preparation:**
  - compiled `.qm` translations and `.qrc` resources;
  - the matplotlib font cache, pre-built with the bundled fonts;
  - the hidden-imports list, generated from the rule and product registries (§5.4.1);
  - exclusion of unused Qt modules (Qt3D, Quick, Multimedia, Bluetooth, Positioning, SerialPort, …) and of all GPL-only modules (§3.10); exclusion of package test suites; WebEngine locales trimmed to `en-US` and `fa`.
- The PyInstaller **bootloader is built from source** in CI instead of using the prebuilt one, which antivirus heuristics often flag.

### 14.3 Installer (Inno Setup 6.3)
- **Per-user installation without administrator rights by default** (`PrivilegesRequired=lowest`, into `%LOCALAPPDATA%\Programs\GEOVALID PRO`), with an all-users option for IT (`PrivilegesRequiredOverridesAllowed=dialog commandline`, into Program Files). Exploration geologists often have no local administrator rights.
- `ArchitecturesAllowed=x64compatible` and `ArchitecturesInstallIn64BitMode=x64compatible`; `MinVersion=10.0.19045` (Windows 10 22H2) and Windows 11. Windows on ARM installs under x64 emulation but is not tested or supported.
- LZMA2 solid compression.

| Component | Default | Size | Notes |
|---|---|---|---|
| Core application | Required | ~1.1 GB unpacked | GUI, CLI, engine, fonts, geomag and geoid data, profiles, manual |
| Visual C++ 2015–2022 x64 runtime | Only if missing | ~25 MB | The redistributable needs administrator rights. In a per-user install it is skipped, and the app-local CRT DLLs shipped in `_internal` are used. |
| 3D viewer (pyvista, pyvistaqt, vtk) | Off | ~230 MB unpacked | Imported lazily (§2.2) |
| Microsoft Access Database Engine x64 | Off | ~80 MB installer | Offered only when no 32-bit Office is detected (registry `Bitness`/`Platform` values): with 32-bit Office the x64 engine cannot be installed alongside, and tier 2 is used (§3.5). Bundling depends on confirming Microsoft's redistribution terms (Q4, §16). |
| Sample project (synthetic M) and tutorial | On | ~150 MB | Generated at build time by `gen-synthetic` |

- **Integration:** `.gvp` file association and icon (per-user under `HKCU\Software\Classes`); Start-menu entries for the GUI, the manual (fa and en) and a "GEOVALID command prompt" with `geovalid` on `PATH`; an optional "Add CLI to PATH" task.
- **Silent install** for IT: `/VERYSILENT /SUPPRESSMSGBOXES /COMPONENTS=…`. The installer can be wrapped as an Intune Win32 app. An MSI (WiX) is produced only if the client's IT requires one (Q5, §16).
- **Uninstall** removes the application, never user projects, backups or exports. An optional checkbox also clears the cache and logs.
- **Side-by-side major versions.** The Inno `AppId` contains the major version, so 1.x and 2.x can be installed together. A Competent Person can then reproduce a release with the exact software version that produced it (`software_version` in `run`, 02 §5.9). Every released installer is archived with its SHA-256 for at least 10 years.

### 14.4 Code signing
- **Authenticode** (SHA-256 digest, RFC 3161 timestamp) on both executables, the installer and the uninstaller (Inno `SignTool` directive). Unsigned third-party DLLs and `.pyd` files are signed as well, which reduces antivirus heuristics.
- **Certificate:** an organisation-validated (OV) code-signing certificate. Since 2023 the private key must be held on certified hardware (token or HSM), so CI signs through a cloud HSM or signing service, or on a self-hosted build machine with the token attached. An EV certificate no longer bypasses SmartScreen reputation, so OV is sufficient; reputation builds with distribution.
- **The signing identity is a client decision** (Q3, §16). Certificate authorities and signing services serve only eligible organisations and jurisdictions. If no public certificate can be obtained for the publishing entity, the fallback is an internal code-signing certificate that the client's IT deploys as a trusted publisher (Group Policy or Intune), plus published SHA-256 checksums of every artefact.
- Distribution inside the client organisation (USB, internal share, Intune) avoids most SmartScreen prompts, which apply to downloaded files carrying Mark-of-the-Web.

### 14.5 Size estimate
| Part | Unpacked (MB) |
|---|---|
| Python 3.12 runtime and stdlib | 40 |
| Qt / PySide6 (Essentials + WebEngine + Pdf + Svg, trimmed) | 300 |
| numpy, scipy (with OpenBLAS) | 120 |
| pyarrow (trimmed) | 100 |
| Two GDALs (pyogrio, rasterio), pyproj with `proj.db`, shapely/GEOS | 165 |
| pandas, statsmodels, scikit-learn | 140 |
| duckdb | 50 |
| matplotlib, plotly (+ `plotly.min.js`), pyqtgraph, mplstereonet | 110 |
| Readers and writers (calamine, openpyxl, xlrd, lxml, python-docx, XlsxWriter, laspy/lazrs, ezdxf, trimesh, pypdf) | 50 |
| Fonts, geomag and geoid data (Iran clip), profiles, dictionaries, templates | 25 |
| Manual and licences | 15 |
| **Core total** | **≈ 1.1 GB** |
| **Installer (LZMA2)** | **≈ 380–450 MB** (+ ~80 MB with the 3D component) |

S-10 measures the real figures. The budget is ≤ 1.3 GB unpacked for the core.

### 14.6 Build pipeline (CI)
| Job | Runner | Content |
|---|---|---|
| `lint-test` | `ubuntu-24.04` and `windows-2025` | `uv sync --frozen` (hash-pinned); ruff, mypy, import-linter (§2.2), licence audit (§3.10); unit, rule (synthetic S and M) and property tests; GUI tests offscreen |
| `build-win` | `windows-2025`, pinned explicitly rather than the moving `windows-latest` label | Build the bootloader; compile `.qm`/`.qrc`; generate hidden imports; run PyInstaller from the committed spec. **Frozen smoke tests:** `geovalid --version`, `gen-synthetic --size S`, `run` end-to-end including fa and en PDF offscreen, `geovalid-pro.exe --self-test`. Then sign, build the manual, compile the Inno Setup installer, sign it, and produce the SBOM (cyclonedx-py), third-party notices and `SHA256SUMS`. |
| `install-test` | Clean **Windows 10 22H2 and Windows 11** VMs (self-hosted or cloud), not only Server images | Silent per-user install; packaging tests run from the installed location, including a project under a path with spaces and Persian characters (`C:\Users\…\Documents\پروژه کوه‌زر\`); Microsoft Defender scan; uninstall check |
| `no-network` | Linux container with `--network none`; Windows VM with an outbound block | §13.1 proof |
| `bench` (nightly) | Self-hosted reference laptop | §12.5 |
| `linux-headless` | `ubuntu-24.04` | A `geovalid_pro` wheel with the locked requirements, for headless CI use; an optional OCI image with all dependencies, usable offline once pulled. No Linux GUI package. |

- **Traceable, not bit-reproducible.** PyInstaller output embeds timestamps, so a build is identified by `build_id` (commit + build date) and `dependency_lock_sha256` (02 §5.9), not claimed to be byte-identical.
- **Packaging from Phase 1** (A15). Every phase deliverable is an installer, so the riskiest integration problems (WebEngine, two GDALs, Persian paths, antivirus, console windows) surface in the first weeks rather than in Phase 5.

### 14.7 Versions, migration and updates
- Semantic versioning. A change to a rule's logic bumps that rule's `version` (§5.2), and release notes list rule-catalogue changes, so users know which issues may change after an upgrade.
- **Project migrations are forward-only.** Each is preceded by a backup (§13.3) and logged as `SCHEMA_MIGRATED`. A project written by a newer version opens read-only in an older one (CLI exit 4).
- **No automatic updates** (offline). Updates are new installers, distributed by the client's IT.

---

## 15. Spike register
A spike is a time-boxed experiment that settles one technical risk before the work that depends on it starts. Each spike has an acceptance test and a fallback, so a failed spike changes the plan, not the architecture. Scheduling is in `04_phase_plan.md`.

| ID | Question | Days | Acceptance | Fallback |
|---|---|---|---|---|
| S-01 | Qt WebEngine `printToPdf` for Persian reports, headless on Windows and Linux | 4 | A 40-page fa/en/bi sample (tables, SVG, mixed runs) with shaping confirmed by a Persian reader; offscreen in CI; two-pass TOC; header/footer overlay; named pages tested | Typst backend over the RDM (§3.2) |
| S-02 | Vazirmatn + reshaper + bidi in matplotlib | 2 | Every presentation form the reshaper emits renders; multi-line labels, legends, tick labels, mixed fa/en | Pre-shaped text paths per glyph run |
| S-03 | RTL DOCX in Word 2016/2019/365 and LibreOffice | 3 | bidi paragraphs and tables, captions, `SEQ`/`REF` fields, embedded fonts on a PC without Vazirmatn, Persian page numbers | Latin page numbers; fonts declared as a requirement |
| S-04 | access-parser (tier 2) against ACE (tier 1) | 3 | Cell-by-cell equality on the client corpus (Jet 3, Jet 4, ACE; cp1256) | Tier 3 guided export |
| S-05 | Datamine `.dm` reader | 4 | 100 % cell equality on ≥ 10 files with CSV twins (§3.6) | CSV export |
| S-06 | Micromine `.DAT` reader | 3 | As S-05 | Text/CSV export |
| S-07 | Model/view at 1 M rows | 3 | Scroll ≥ 50 fps; filter/sort ≤ 300 ms; RTL layout correct; ≤ 600 MB for the snapshot | Window-limited model over paged DuckDB queries |
| S-08 | pyqtgraph viewers at scale | 3 | 5 000 traces + 100 k markers at ≥ 30 fps pan/zoom; picking ≤ 50 ms; section projection ≤ 200 ms | Density-image rendering at more zoom levels; OpenGL viewport |
| S-09 | End-to-end performance baseline | 4 | Prototype products and representative rules on L within 1.3 × the §12.3 budget; peak RSS ≤ 6 GB | Re-budget; move specific steps into DuckDB |
| S-10 | Full-stack freeze and installer | 4 | One-dir build of the full stack; per-user install on clean Windows 10 and 11; no console window; Persian paths; Defender clean; size within §14.5 | Adjust hooks; separate windowless worker executable |
| S-11 | Client corpus intake | 3 + client time | ≥ 3 anonymised real databases profiled (formats, encodings, header languages, Access versions, Excel quirks); mapping dictionaries seeded; regression golden set frozen (brief §18) | Synthetic-only regression until data are supplied |
| S-12 | Two GDALs side by side; Unicode paths | 2 | All drivers listed in §3.3 work on both stacks; Persian file paths; KMZ through `/vsizip/` | Build environment from conda-forge, where pyogrio and rasterio link one shared GDAL |

---

## 16. Open questions for the client (architecture)
1. **Q1 Bilingual report.** Is `bi` acceptable as designed in §9.5 (primary-language body; bilingual headings, captions, table headers, key-findings boxes, executive summary and action plan; a full second-language report on request)? Or is a fully parallel text required?
2. **Q2 Hardware.** Is a 16 GB, 4-core laptop with an SSD representative of the team's machines (§12.1)? Are 8 GB machines in use, and are 2× longer run times acceptable on them?
3. **Q3 Signing identity.** Which legal entity publishes and signs GEOVALID PRO, and can it obtain an OV code-signing certificate? If not, can client IT deploy an internal certificate (§14.4)?
4. **Q4 Access databases.** What share of client data arrives as MDB/ACCDB? Is Office 32-bit or 64-bit on the fleet? May the ACE engine be bundled (after review of its licence), or will IT install it (§3.5, §14.3)?
5. **Q5 Deployment.** Is a per-user installation acceptable? Does IT require an MSI or Intune package (§14.3)?
6. **Q6 Report authenticity.** Is the release anchor printed in each report sufficient (§13.2), or are digitally signed PDFs required (certificate and PKI needed)?
7. **Q7 Encryption.** Is full-disk encryption (BitLocker) sufficient, or must project files be encrypted by the application (§13.6)?
8. **Q8 Concurrent review.** Is one writer per project sufficient (§4.4), or must several reviewers work on one project at the same time? The latter needs a review-package export/merge workflow, which would be planned after Phase 5.
9. **Q9 PDF/A.** Is PDF/A required for archival or regulatory submission (§9.8)?
10. **Q10 Licensing and protection.** Is copy protection, an offline licence file or source protection required? None is planned (§13.1, §14.1).
11. **Q11 Hole atlas.** Should the per-hole atlas be a default output or produced on request (§9.3)?
12. **Q12 House style.** Will the client supply a Word house template (styles, logo, Arad/A.A branding) to become `reference_fa.dotx`/`reference_en.dotx` (§9.6)?
13. **Q13 Proprietary samples.** Can the client provide ≥ 10 Datamine `.dm` and ≥ 10 Micromine `.DAT` files, each with its CSV export, and ≥ 3 anonymised real databases for S-05, S-06 and S-11 (§15)?
