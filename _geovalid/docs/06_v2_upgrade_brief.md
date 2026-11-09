> **Applied to GEOVALID PRO (owner instruction, 2026-11-09).** This brief was written for the single-file, standard-library
> GEOVALID v1.1. The owner asked for its features to be added to **GEOVALID PRO** instead, keeping GEOVALID PRO's libraries
> (pandas, numpy, scipy, matplotlib, PySide6, openpyxl, PyYAML). How each constraint is applied is recorded in
> `07_v2_gap_analysis.md` §1 and `PROGRESS.md`. The text below is the brief as received.

# GEOVALID v2.0 — Upgrade Brief (for Claude Code)

## 0. How to use this brief
- You are upgrading an existing, working application. **Only `GEOVALID.py` is developed in this project.**
- Read this whole brief, plus `CLAUDE.md`, before touching any code. Re-read the relevant sections at the start of every new session.
- Work strictly in the phases and checkpoints of Section 4.
- Keep `docs/PROGRESS.md` up to date so work can resume cleanly in a new session or after context compaction. It should list:
  - the current phase;
  - what is done and what is pending;
  - decisions made;
  - open questions.
- Run Phase 0 in **plan mode**: read and analyse only, no edits to `GEOVALID.py`.
- The project folder is a git repository. Commit after each phase I approve, with a message like `Phase N: <summary>`. Never rewrite history.
- Where this brief conflicts with the existing code's proven behaviour, stop and ask me rather than guessing.

---

## 1. Role and context
Act as a senior Python engineer with a mineral exploration and resource estimation background. You know drillhole databases (collar, survey, interval tables), desurveying, QA/QC, and the data-verification requirements of the JORC Code, NI 43-101, SEC S-K 1300 and the CIM guidelines.

**GEOVALID** is my standalone, offline Windows application for validating exploration drillhole databases. Current version: v1.1. What it already does:
- Validates collar, survey and interval tables.
- Coverage/gap analysis: intervals that stop short of end-of-hole, plus top and internal gaps. This is its key differentiator.
- Version comparison. It uses a three-stage interval diff: (1) exact key match, (2) overlap clustering for re-segmented intervals, (3) true additions and removals. It also reconciles grades with "all holes" and "common holes" roll-ups, shown in a full GUI tab.

**GEOQAQC** is my separate QA/QC application. In this project it is **reference material only**. It is used solely to learn its input file format (Owner Requirement R1) and, where useful, to port code into GEOVALID. **Never modify anything in `reference/`.**

**Goal of this upgrade.** Turn GEOVALID into a best-in-class, vendor-neutral, offline pre-modelling data gate. It should produce evidence a Qualified Person can cite in the data-verification sections of JORC Table 1, NI 43-101 Item 12 and S-K 1300.

---

## 2. Project layout

```
GEOVALID.py                  ← the ONLY shipped file you modify
CLAUDE.md                    ← standing rules
docs/GEOVALID_v2_brief.md    ← this brief
docs/PROGRESS.md             ← you create and maintain it
reference/                   ← READ-ONLY
   GEOQAQC.py                ← option A: GEOQAQC source (preferred)
   qaqc_samples/             ← option B: sample input files in GEOQAQC format
test_data/                   ← optional real data, READ-ONLY
tests/                       ← you create: unit tests + synthetic data generator
```

If `reference/` contains neither option A nor option B, stop at Phase 0 and ask me.

---

## 3. Non-negotiable constraints
1. **Python standard library only.** No third-party packages of any kind: no numpy, pandas, GDAL, rasterio, shapely, pyproj, matplotlib or PyYAML. If a feature seems to need one, implement it in pure Python or tell me it is not feasible. Do not `pip install` anything.
2. **Single-file build.** The shipped application remains `GEOVALID.py`, one file. Tests, generators and documentation live in separate files because they are not shipped.
3. **Python compatibility.** It must run on Python 3.14. Avoid removed or deprecated modules such as `imghdr` and `cgi`. Avoid dynamic imports that would break packaging into a Windows `.exe`.
4. **Fully offline.** No network calls.
5. **Do not touch the licensing system.** The RSA signature, machine fingerprint and licence check code must remain functionally identical.
6. **Explicit over implicit.** Never silently infer, merge, convert or substitute data. Surface ambiguities to the user. In particular:
   - no automatic hole-ID merging;
   - no automatic unit conversion;
   - no automatic below-detection substitution;
   - no suffix-stripping to infer duplicate parents.
7. **Never modify input data files.** All fixes are flag-only by default. A fix class may be applied only after explicit user approval. Applying a fix writes a corrected copy plus a fix log, and the fix log is included in the evidence pack.
8. **Visual identity.** Keep the existing dark theme with amber accents, and the existing layout conventions.
9. **Backward compatibility.** Existing features, results, saved settings and project files must continue to work. The version-comparison module must give identical results on existing data (regression test required).
10. **Reuse before writing.**
    - Use the existing safe AST-based expression engine for user rules.
    - For charts, use GEOVALID's own chart code if it exists. If it does not and `reference/GEOQAQC.py` exists, port GEOQAQC's pure-tkinter chart engine into GEOVALID. Only write a new minimal engine if neither exists.
11. **Real-data robustness.** Handle all of the following:
    - empty cells, whitespace-only cells, text in numeric fields;
    - mixed-case IDs;
    - comma decimal separators;
    - UTF-8 with or without BOM, cp1252 and cp1256 (Persian/Arabic Windows) encodings;
    - auto-detected delimiters;
    - `0` versus blank versus missing codes, kept distinct.

---

## 4. Working method and checkpoints

### Phase 0 — Discovery (plan mode; no edits to GEOVALID.py)
1. Read the entire `GEOVALID.py`. Summarise its architecture: data model, loaders, checks, GUI tabs, report outputs, comparison module, settings storage, and how the app is currently packaged.
2. Produce a **gap table**: every rule in Section 7, marked *Exists / Partial / Missing* in the current code, with function names.
3. Extract the QA/QC input format from `reference/` and write `docs/QAQC_FORMAT.md` (see R1).
4. Propose the internal module structure, meaning section headers inside the single file, and a list of risks.
5. Create `docs/PROGRESS.md`.
6. **Checkpoint: show me items 2–4 and wait for my approval.**

### Phases 1–3 — Implementation
Implement in priority order: P1, then P2, then P3 (Section 7). After each phase:
- run the full test suite (`python -m unittest discover tests`), including regression tests;
- update `docs/PROGRESS.md`;
- report what was built, test results, timings and known limitations;
- **checkpoint: wait for my approval.** Once approved, commit and only then move to the next phase.

### General rules
- Make minimal, surgical changes to working code. Keep existing function names and signatures stable.
- Add clear section headers and docstrings. Every rule function has a docstring stating its logic, thresholds and standards references.
- Run long operations in a worker thread with a progress bar. Use `threading`, a queue and `after()` polling so the GUI never freezes.
- If a task in this brief turns out to be infeasible or much larger than expected, say so at the checkpoint and propose an alternative.

---

## 5. Core architecture additions (Phase 1 foundation)

### 5.1 Issue model
Every check emits records with these fields:
- `rule_id`
- `category` (A–J, see Section 7)
- `severity`
- `table`
- `hole_id`
- `source_file`
- `source_row`: the 1-based row number in the original file, so the user can find it
- `field`
- `value`
- `message`
- `suggested_fix`
- `fix_class`: null if not auto-fixable
- `standards_refs`: list of clause tags

### 5.2 Severity levels
- **Critical**: blocks use for estimation.
- **Major**: must be resolved or justified.
- **Minor**: should be reviewed.
- **Info**: context or statistics.

Every rule's default severity is user-editable.

### 5.3 Rule registry
A central registry holds, for each rule:
- ID
- name
- category
- description
- default severity
- parameters with defaults
- enabled flag
- standards references
- the function itself

The GUI, reports, profiles and `RULE_CATALOGUE.md` are all generated from this registry.

### 5.4 Global numeric tolerance
Use one configurable depth tolerance for interval comparisons (default 0.001 m). Overlaps and gaps smaller than the tolerance are reported separately as **precision artefacts** (Minor), never mixed in with real overlaps and gaps.

### 5.5 Dataset fingerprinting
- SHA-256 hash of every input file.
- A per-hole canonical hash: hash of the sorted, normalised records of that hole across all tables.
- Both go into every report and into the version-comparison snapshots.

### 5.6 Fix policy
Every fix class is listed and described in the GUI. A fix is applied only after explicit approval for that class. Output is a corrected copy plus `fix_log` (rule, row, old value, new value, timestamp, user).

---

## 6. Owner requirements (mandatory)

### R1 — QA/QC and laboratory input must use the GEOQAQC file format
The QA/QC and lab-certificate input file for GEOVALID must be **exactly the same file format GEOQAQC uses**. A user prepares the file once and uses it in both applications without any editing.

**1. Extract the format** and document it in `docs/QAQC_FORMAT.md`:
- accepted file types, delimiter and encoding handling, header detection;
- required and optional columns and their canonical names;
- the column-mapping UI and any saved mapping profiles;
- the sample-type field and **all its short codes** (CRM, blank, field/coarse/pulp duplicates, and so on);
- the explicit parent-ID field for duplicates, which must have **no suffix-stripping**;
- CRM ID, batch, certificate, lab and method fields;
- unit handling, below-detection and over-limit conventions;
- the separate check/umpire file.

Where it comes from depends on what is in `reference/`:
- **Option A (`GEOQAQC.py` present).** Read the source to get the format.
- **Option B (only sample files present).** Infer the format from the samples. List every assumption, especially the sample-type codes, and **ask me to confirm them before implementing**.

**2. Implement.**
- With option A, port the GEOQAQC parsing and column-mapping functions into `GEOVALID.py` by copying them. Preserve their behaviour exactly, and mark them with a comment naming the GEOQAQC source version.
- With option B, implement a parser to the confirmed specification.
- Justify any divergence to me.

**3. Acceptance test.** Every file in `reference/qaqc_samples/`, or any file GEOQAQC accepts, loads into GEOVALID without editing. Sample counts by sample type must match GEOQAQC's (option A) or the counts I confirm (option B).

**4. Use this loader for:**
- the reconciliation rules (REC, Section 7);
- QC-insert-aware sample-sequence checks, so CRMs, blanks and duplicates inserted into the sample stream do not create false "missing sample ID" gaps.

### R2 — Topography must be accepted in many formats
Implement pure-Python readers, auto-detected by extension and magic bytes, with a manual override. Each reader reports what it read: extent, resolution or point/triangle count, nodata, and CRS information if present. Unsupported variants fail with a clear message, never a silent wrong result.

**Gridded DEMs**
- ESRI ASCII grid (`.asc`).
- Surfer grid: ASCII `DSAA`, Surfer 6 binary `DSBB`, Surfer 7 `DSRB`.
- ESRI BIL/BIP/BSQ/FLT with `.hdr`.
- GeoTIFF:
  - stripped and tiled layouts;
  - uncompressed, Deflate (`zlib`), LZW (implement the decoder) and PackBits compression;
  - horizontal predictor (2) and floating-point predictor (3);
  - int16, int32, float32 and float64 data;
  - geo-referencing from ModelPixelScale/ModelTiepoint/ModelTransformation and EPSG from GeoKeys;
  - nodata from GDAL_NODATA (tag 42113).
  
  Optionally support BigTIFF. JPEG-compressed TIFF is unsupported and must say so.
- SRTM `.hgt`.
- Regular XYZ grid text.

**Point data**
- CSV/TXT XYZ point clouds with any delimiter and optional header.
- DXF `POINT` entities.

**Surfaces, meshes and contours**
- DXF: `3DFACE`, polyface `POLYLINE`, and contour `LWPOLYLINE`/`POLYLINE` with elevation.
- Surpac string (`.str`) plus DTM (`.dtm`).
- OBJ.
- STL, ASCII and binary.
- PLY, ASCII and binary.
- Shapefile `PolylineZ`/`PointZ` contours and points.
- KML/KMZ with altitudes.

Proprietary binary formats (Vulcan `.00t`, Datamine `.dm`) are excluded unless a public specification exists. Tell me what you find.

**Evaluation strategy**

Only evaluate elevation at the locations needed: collar XY and points along desurveyed traces. Never build a full-area TIN.
- **Grids.** Use bilinear interpolation. Use **windowed reading**: decode only the strips or tiles that contain the query points, so large DEMs (e.g. 20,000 × 20,000 float32) never load fully into memory.
- **TIN meshes.** Use a spatial grid index, then point-in-triangle search and barycentric interpolation.
- **Points and contours.** Gather nearby points using a spatial index. Build a local Delaunay triangulation (Bowyer–Watson) around each query point and interpolate barycentrically. Report the distance to the nearest data point. If it exceeds a threshold, the result is "topography not supported here", not an interpolated guess.

**Coordinates**
- Implement WGS84 geographic ↔ UTM (any zone, both hemispheres) in pure Python. Use the Krüger series to millimetre accuracy, because KML/KMZ and SRTM data are geographic while collars are usually in UTM.
- Datum shifts other than WGS84 are not supported. Warn when a non-WGS84 datum is declared.
- Note in the report that SRTM heights are geoid-referenced (EGM96).

**Sanity checks before any comparison**
- Topography extent vs collar extent.
- No overlap → likely CRS, zone or swapped E/N problem.
- Constant horizontal offset → possible false-easting or zone issue.
- Elevation ratio ≈ 3.28 → feet vs metres.
- Collars outside the topography extent → "not checked" (Info), never a pass.

---

## 7. Feature specifications and rule catalogue

Default thresholds are configurable. Each rule must state its standards references (tags defined in Section 8.2).

### P1 — Phase 1

**F1. Survey QA pack (category C)**

Inclination convention. Use inclination I from vertical, derived from dip according to a user-set convention (negative-down or positive-down). Azimuth A must handle 0/360 wrap-around in every difference calculation.

Dogleg angle between stations 1 and 2:

`β = arccos( cos(I₂−I₁) − sin I₁ · sin I₂ · (1 − cos(A₂−A₁)) )`

Dogleg severity: `DLS = β · 30 / ΔMD` (°/30 m).

| ID | Check | Default severity / threshold |
|---|---|---|
| SRV-01 | Missing 0 m station. Report what the desurvey will assume (collar orientation or first station). | Minor |
| SRV-02 | Dip or azimuth out of range. | Critical |
| SRV-03 | Dip sign inconsistent with the convention, or mixed within one hole. | Major |
| SRV-04 | Duplicate depths: identical values / conflicting values. | Minor / Major |
| SRV-05 | Out-of-sequence depths. | Major |
| SRV-06 | Survey station beyond EOH. | Major |
| SRV-07 | Collar azimuth/dip vs first station mismatch. | Major; > 5° dip or > 10° azimuth |
| SRV-08 | Dogleg severity. | Minor > 3°/30 m; Major > 6°/30 m |
| SRV-09 | **Neighbour-inconsistent station.** Station i deviates from the direction interpolated between i−1 and i+1 by more than 2°, while i−1 and i+1 agree within 1°/30 m. Likely a typo or magnetic interference. | Major |
| SRV-10 | Station spacing too large. | Minor; > 50 m |
| SRV-11 | Near-vertical holes (I < 3°): suppress azimuth-based flags and report that suppression was applied. | Info |
| SRV-12 | North reference declared (magnetic/true/grid). If both magnetic and corrected azimuths exist, check their difference against the user-entered declination ± grid convergence. | Major if inconsistent |
| SRV-13 | Magnetic interference indicators, if a magnetic-field or instrument-type field exists: field-strength deviation from a user-entered expected value, or azimuth swings while dip is stable on magnetic instruments. | Minor |
| SRV-14 | **Desurvey sensitivity.** Compute EOH XYZ by tangent, balanced tangent and minimum curvature (`RF = (2/β)·tan(β/2)`, with RF = 1 as β → 0) and report the maximum positional difference. | Info; Minor > 2 m |
| SRV-15 | Single-station or no-survey holes longer than a threshold (straight-line assumption). | Info; > 100 m |

**F2. Severity-ranked reporting and evidence pack.** See Section 8.

**F3. Hole-ID normalisation (category A)**

| ID | Check | Default severity |
|---|---|---|
| SCH-05 | Build a normalised key (upper-case; strip spaces, `-`, `_`, `.`; optional leading-zero normalisation of numeric parts). Report groups of distinct raw IDs that share a key, e.g. `DH-01`, `DH01`, `dh 01`. **Suggest only.** The user approves merges through a mapping table, which is saved, applied and logged. | Major |
| SCH-04b | For orphan IDs, suggest the closest collar IDs using `difflib` similarity. Suggestion only. | — |

**F4. Schema, collar and interval completeness (categories A, B, D)**

Keep and integrate the existing checks into the registry. Add the missing ones.

| ID | Check | Default severity / threshold |
|---|---|---|
| SCH-01 | Required tables or fields missing, or not mapped. | Critical |
| SCH-02 | Type violations, e.g. text in numeric fields. | Major |
| SCH-03 | Duplicate primary keys (collar: hole; survey: hole + depth; interval: hole + from + to). | Critical |
| SCH-04 | Orphans in both directions: downhole records without a collar (Critical); collars without survey or interval data (Minor). | Critical / Minor |
| SCH-06 | Blank vs zero vs missing-code ambiguity in the same field. | Minor |
| COL-01 | Null, zero or dummy coordinates (−99, −999, 0, user list). | Critical |
| COL-02 | Duplicate collar locations, distinct IDs. | Major; within 1.0 m |
| COL-03 | Swapped easting/northing, by dataset statistics and UTM plausibility. | Critical |
| COL-04 | CRS plausibility: outside the declared zone range; mixed coordinate systems (spatial clusters offset by a large constant). | Major |
| COL-07 | Max depth vs deepest survey or interval: data beyond EOH is Critical; short coverage uses the existing gap logic. | Critical |
| COL-08 | Dates and drill type: end before start, future dates, unknown drill-type codes. | Minor |
| INT-01 | From ≥ To. | Critical |
| INT-02 | Zero-length interval. | Major |
| INT-03 | Overlaps (Critical); precision artefacts below tolerance (Minor). | Critical / Minor |
| INT-04 | Top, internal and bottom gaps (existing coverage logic — keep it as the reference implementation). | — |
| INT-05 | Interval beyond EOH. | Critical |
| INT-06 | Sample-length anomalies, by drill type. | Minor; < 0.1 m or > 6 m |
| INT-07 | Duplicate sample IDs (Critical); missing or out-of-sequence sample IDs, QC-insert-aware via R1 (Minor). | Critical / Minor |

**F5. Value validation (category E)**

| ID | Check | Default severity |
|---|---|---|
| VAL-01 | Inventory and consistency of below-detection codes (`<x`, negatives, BDL, ND, text codes) per field and per batch. | Minor |
| VAL-02 | Over-limit codes (`>x`, OL, `+`) and unresolved over-limits with no ore-grade re-assay present. | Major |
| VAL-03 | **Unit detection and mixed units.** Use header tokens (ppm, ppb, %, pct, g/t, gpt, opt) and statistics (batch-median log10 shifts of about 3 or 4 suggest ppb/ppm/% mixing). Never convert automatically. | Major |
| VAL-04 | Mixed labs, methods or detection limits within one field, when such fields exist. | Minor |
| VAL-05 | Physically impossible values: any % value above 100; the sum of all elements expressed as % (ppm/10⁴, ppb/10⁷) above 100. | Critical |
| VAL-06 | Mineral-stoichiometric caps, user-configurable, by dominant mineral. Defaults (wt%): Cu 79.9 (chalcocite), Pb 86.6 (galena), Zn 67.1 (sphalerite), Fe 72.4 (magnetite), S 53.4 (pyrite), Mo 59.9 (molybdenite), Ba 58.8 (barite). | Major |
| VAL-07 | Major-oxide total (with LOI) outside 97–102 %. | Major |
| VAL-08 | Code-list violations against a user-loaded code dictionary (lithology, alteration, weathering and so on). | Major |
| VAL-09 | Downhole spikes: value > 10× both neighbours and above the field's 95th percentile. | Info |
| VAL-10 | Repeated-value runs: ≥ 5 consecutive identical values above detection (possible copy-paste). | Minor |

### P2 — Phase 2

**F6. Version comparison extension (category I)**

Keep the three-stage diff exactly as it is. Add the following:
- **Change classification** for each change: hole added/deleted; collar moved (ΔXYZ); survey changed (with resulting ΔEOH position); interval added/removed; re-segmented (geometry changed); re-assayed (same geometry, value changed); code changed (categorical); metadata changed.
- **Metal-weighted deltas.** Σ(length × grade) per element, per hole and in total, alongside the existing grade reconciliation.
- **Per-hole hashes** (5.5), so unchanged holes are skipped and reported as unchanged.
- **Accepted snapshots.** The user can mark a dataset version as "accepted", with reviewer name, date and a note. This writes a JSON manifest containing file hashes, per-hole hashes, rule-profile hash and app version.
- **VER-01 (Critical).** Any change to a hole that was locked in the last accepted snapshot.
- **Change-log export** for the evidence pack. This addresses the CIM requirement to detect unintended changes between data versions.

**F7. Laboratory and QA/QC reconciliation (category G) — uses the R1 loader**

| ID | Check | Default severity |
|---|---|---|
| REC-01 | Sample in the lab file but not in the database, and vice versa. | Major |
| REC-02 | Value mismatch. Tolerance = max(0.5 × detection limit, 0.1 % relative) after normalising number formats. | Major |
| REC-03 | Unit or scale mismatch (ratio ≈ 10³ or 10⁴). | Major |
| REC-04 | Below-detection coding mismatch between lab and database. | Minor |
| REC-05 | Multiple results for one sample (re-assays): report all of them, and which one is in the database. Never choose. | Info |
| REC-06 | QC samples (by GEOQAQC sample-type codes) found in the primary assay table, or expected QC samples missing. | Major |
| REC-07 | **Random verification audit.** Select N % of samples with a seeded, reproducible random generator. Export a checklist for manual comparison against original logs or certificates. Import the results back. Include the audit in the evidence pack. | — |

**F8. Cross-table consistency (category F)**

| ID | Check | Default severity |
|---|---|---|
| XTB-01 | Interval logged as mineralised (user-defined codes) with no assay coverage. | Major |
| XTB-02 | Recovery > 100 % (5 % tolerance), or recovered length > interval length. | Major |
| XTB-03 | RQD > recovery. | Major |
| XTB-04 | Density outside a user range table by lithology. | Major |
| XTB-05 | Coverage mismatch between tables per hole (e.g. lithology vs assay). | Minor |
| XTB-06 | Weathering-profile inversion (e.g. oxide logged below fresh). | Info |
| XTB-07 | High grade inside barren-logged lithology. | Info |

**F9. Topography and licence boundary (categories B and H) — uses R2**

| ID | Check | Default severity / threshold |
|---|---|---|
| COL-06 | Collar Z vs topography: Δz = collar Z − topography Z. Exempt holes marked underground or trench through an explicit field the user selects. Optionally pick the topography by date (pre-mining vs current). | Minor > 2 m; Major > 5 m |
| COL-06b | **Systematic offset.** Median Δz beyond 3 m with a tight spread (IQR < 2 m) suggests a vertical-datum mismatch (ellipsoidal vs orthometric heights). | Major |
| COL-05 | Collar outside the licence boundary, with configurable buffer tolerance. Boundary formats: KML/KMZ, Shapefile polygons (read `.prj` for info), GeoJSON, DXF closed polylines, CSV vertex lists. Handle multipart polygons and holes; use ray casting. | Major |
| SPA-01 | Desurveyed trace emerges above the topography below the collar (likely survey error). | Major |

### P3 — Phase 3

**F10. Rule profiles and headless mode (category J)**
- Rule profiles saved as JSON (not YAML, which is not in the standard library). A profile holds enabled rules, thresholds, severities, code dictionaries, column mappings and the ID-merge table. Profiles are versioned, and the profile hash appears in reports.
- Headless mode, e.g. `GEOVALID.exe --cli --project ... --profile ... --out ...`, for batch runs.
  - Exit codes: 0 = no Major/Critical; 1 = Major present; 2 = Critical present.
  - Windowed executables may have no console, so always write a log file. Tell me whether a separate console build is needed.

**F11. Spatial checks, twins and drill-type bias (category H)**

| ID | Check | Default severity / threshold |
|---|---|---|
| SPA-02 | Hole clash: minimum 3D segment-to-segment distance between desurveyed traces, using a spatial index. | Major; < 1 m |
| SPA-03 | Twin candidates: collars close together and traces near-parallel. | Info; collars < 10 m, traces within 10° |
| SPA-04 | Twin comparison: match by depth or elevation window. Report mean difference, QQ data and a paired test per element. | Info |
| SPA-05 | **Drill-type bias** (e.g. RC vs diamond vs aircore): composite to a user length, pair nearest neighbours within a distance, then report mean ratio, QQ plot and Wilcoxon signed-rank. Implement the statistics inside GEOVALID; porting them from `reference/GEOQAQC.py` is allowed if present. | Info |

**F12. Optional anomaly assist (category E). Off by default, explainable, suggestion-only.**
- Code-mapping suggestions: raw log codes → dictionary codes, using `difflib` and token-set similarity.
- Multivariate anomaly score: robust Mahalanobis distance on centred log-ratio transformed elements, in pure Python. Report the top contributing elements for each flagged sample. Severity: Info only.

---

## 8. Reports and evidence pack

### 8.1 Issue outputs
- Issues exported as CSV and JSON.
- A **self-contained HTML report**: inline CSS, no external resources, print-friendly, with a light print style.
- Contents:
  - summary by severity and category;
  - per-rule pass/fail with counts;
  - per-hole status;
  - an issue browser with filters;
  - thresholds used;
  - dataset fingerprints;
  - app version and rule-profile hash.

### 8.2 Standards mapping
Each rule carries one or more of these clause tags:
- `JORC-T1-S1-Verification`: "Verification of sampling and assaying" — twinned holes; documentation of primary data, entry, verification and storage; adjustments to assay data.
- `JORC-T1-S1-Location`: "Location of data points".
- `JORC-T1-S3-DBIntegrity`: "Database integrity" — corruption by transcription or keying errors; data validation procedures used.
- `NI43101-F1-Item12`: Data Verification — procedures, limitations, QP opinion.
- `SK1300-601b96-iii-B-9`: data verification — procedures, limitations, QP opinion on adequacy.
- `CIM2019-4.2`: detecting unintended changes; documenting edits; archiving the estimation database; storing units as received.
- `CIM2019-4.5`: collar and deviation accuracy; internal consistency of logs; factual errors, completeness, suitability; examination of certificates.
- `CIM2019-6.2`: unsampled intervals; below-detection and over-limit values; mixed methods; negative values; special characters.

### 8.3 Data Verification Evidence Pack (HTML + JSON)
A one-click export, structured by the clauses above. For each clause it lists the checks run, results, open issues, fixes applied (from the fix log), version-diff summary, QA/QC-file reconciliation summary and random-audit results.

It ends with three **empty, clearly labelled sections for the QP to write**: "Procedures applied", "Limitations", "Opinion on adequacy". The tool must never write an opinion.

Document the JSON structure as a versioned schema in `docs/EVIDENCE_SCHEMA.md`.

---

## 9. GUI requirements
- Add new tabs or sections, consistent with the existing style: **Survey QA**, **Values**, **Cross-table**, **Lab & QA/QC Reconciliation**, **Topography & Boundary**, **Spatial (Clash / Twins / Bias)**, **Rules & Profiles**, **Evidence Pack**. Existing tabs stay unchanged.
- A central **Issue Browser**:
  - filter by severity, category, rule and hole;
  - double-click shows the source file and row;
  - export the filtered view.
- Charts (see constraint 10):
  - Δz histogram and collar Δz map;
  - downhole DLS plot;
  - twin and bias QQ plots;
  - version-diff metal-delta bar chart.
- Every threshold is editable in the GUI and saved in the profile.

---

## 10. Testing and acceptance criteria
1. Test suite using `unittest` in `tests/`. **Every rule needs at least one positive test (error detected) and one negative test (clean data passes).**
2. A synthetic data generator in `tests/` that produces collar, survey, assay, lithology, density, a lab/QA-QC file in GEOQAQC format, and topography in **every supported format**, with seeded errors.
3. **Topography reader accuracy.** Generate a planar surface `z = a·x + b·y + c` in every format. Bilinear and barycentric interpolation must reproduce it within 1e-6, independent of format. Also test nodata, tiled and stripped GeoTIFF, all compressions, both predictors, and windowed reading.
4. UTM ↔ WGS84 round-trip error < 1 mm across zones and both hemispheres.
5. **Regressions:**
   - existing v1.1 checks give identical results on existing test data;
   - the three-stage comparison gives identical output;
   - the licence check is unchanged.
6. R1 acceptance test as defined in Section 6.
7. Performance:
   - report timings for 10,000 holes and 1,000,000 interval rows (target: full P1 validation in under ~5 minutes on a typical laptop);
   - a large GeoTIFF must not exceed modest memory, thanks to windowed reading;
   - optimise hot loops: sort once, group by hole, use spatial indexes.
8. If `test_data/` contains real data, run the suite on it and report any new edge cases found.

---

## 11. Deliverables
1. Updated `GEOVALID.py`, version **v2.0**.
2. `CHANGELOG.md`
3. `docs/RULE_CATALOGUE.md`: every rule with ID, category, description, logic, default severity, thresholds and standards tags. Generate it from the registry, not by hand.
4. `docs/QAQC_FORMAT.md` (R1) and `docs/EVIDENCE_SCHEMA.md`.
5. The test suite and synthetic data generator in `tests/`.
6. Short user notes for the new features.
7. Confirmation that the app can still be packaged into a Windows `.exe` with my existing workflow. Ask me which workflow I use if it is not documented in the repository.

---

## 12. Out of scope
- **Any change to GEOQAQC or to anything in `reference/`.**
- Network or cloud features.
- Modelling or estimation algorithms. Compositing is only allowed as a pre-step for SPA-05.
- Reading proprietary binary formats without a public specification.
- Any LLM or AI dependency.
