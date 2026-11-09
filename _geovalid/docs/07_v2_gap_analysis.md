# GEOVALID PRO — v2 upgrade: gap analysis and plan (Phase 0)

| | |
|---|---|
| Date | 2026-11-09 |
| Baseline | GEOVALID PRO 0.2.0 (commit `9f90392`): 76 rules running (71 registered + 5 import-stage) of the 229-rule catalogue `03` |
| Brief | `06_v2_upgrade_brief.md` (written for GEOVALID v1.1, applied to GEOVALID PRO by owner instruction) |
| Target | GEOVALID PRO **1.0.0** after P1–P3 (0.3.0 after P1, 0.4.0 after P2) |

## 1. How the brief's constraints apply to GEOVALID PRO

| Brief § | Constraint | Applied as |
|---|---|---|
| 3.1 | Standard library only | **Replaced by owner instruction:** GEOVALID PRO keeps pandas, numpy, scipy, matplotlib, PySide6, openpyxl, xlrd, PyYAML, charset-normalizer. No further packages are added; topography formats are read with our own code on top of numpy/zlib (no GDAL, rasterio, shapely, pyproj). |
| 3.2 | Single file | Not applicable: GEOVALID PRO is a package built into one portable Windows folder (`GEOVALID.exe` + `geovalid-cli.exe`). |
| 3.3 | Python 3.14 | The Windows build stays on Python 3.12, because the pinned scientific wheels are released for it. The code avoids removed modules and dynamic imports. |
| 3.4 | Offline | Applies (unchanged). |
| 3.5 | Licensing code | Not applicable: GEOVALID PRO has no licensing system. |
| 3.6 | Explicit over implicit | Applies. Already the rule in GEOVALID PRO ("never changes data"). Hole-ID merges, unit conversions, BDL substitution and parent inference stay suggestions. |
| 3.7 | Never modify inputs; fixes flag-only | Applies. P1 adds fix classes: a corrected copy plus `fix_log.csv`, only after approval per class. |
| 3.8 | Visual identity | GEOVALID PRO's Obsidian & Gold theme already is "dark with amber accents"; kept. |
| 3.9 | Backward compatibility | Applies: existing rules, results, YAML profiles and outputs keep working; the recall and clean-twin gates stay as regression tests. |
| 3.10 | Reuse | Reuse GEOVALID PRO's chart library (`report/charts.py`) and rule engine. The "safe AST expression engine for user rules" does not exist in GEOVALID PRO; user rules are out of this upgrade unless requested. |
| 3.11 | Real-data robustness | Already covered by the import layer (encodings incl. cp1256, delimiters, Persian digits, `٫`, decimal comma, blank vs 0); kept. |
| 5.2 | Severity names | Critical = `CRITICAL`, Major = `ERROR`, Minor = `WARNING`, Info = `INFO`. Labels in the GUI and reports show both names. |
| 5.3 | Rule IDs | GEOVALID PRO keeps its catalogue IDs (`03_rule_catalogue.md`). Each brief ID (SRV-08, VAL-06, …) is stored as an **alias** in the registry and shown in the Rule Catalogue, the GUI and reports. Brief rules with no catalogue entry receive new catalogue IDs. |
| 6 / R1 | GEOQAQC file format | **Open:** GEOQAQC's source or sample files are not available in this session. Needed before the P2 reconciliation work (see §5). |
| 7 / F6 | "Keep the three-stage diff exactly" | GEOVALID PRO has no version comparison yet; P2 builds the three-stage diff to the brief's description. |

## 2. Brief categories A–J ↔ GEOVALID PRO rule families

| Cat. | Brief meaning | GEOVALID PRO families |
|---|---|---|
| A | Schema, IDs | IMP, COL-003, SMP-001 |
| B | Collar | COL |
| C | Survey | SUR (except SUR-016) |
| D | Intervals, sample sequence | INT, SMP |
| E | Values | ASY, LIT, ALT, STR, MAG |
| F | Cross-table | GEO, DEN, WTH, CRS-001, CRS-008, ASY-008, INT-011 |
| G | Lab and QA/QC reconciliation | QAQ, ASY-009, ASY-020, SMP-004, new REC rules |
| H | Spatial, topography, boundary | COL-005, COL-011, COL-012, SUR-016, SPA, CRS-002, CRS-006 |
| I | Versions | VER |
| J | Profiles, process | profile and run-level findings |

## 3. Gap table — every rule of brief §7

Status: **E** exists, **P** partial, **M** missing. Function names are in `geovalid_pro/rules/<family>.py` as `<family>_<nnn>` (e.g. `sur_010`).

### P1

| Brief | Check | GEOVALID PRO | Status | What is missing / plan |
|---|---|---|---|---|
| SRV-01 | Missing 0 m station; state desurvey assumption | SUR-007 `sur_007` | P | Fires only when the first station is deeper than 30 m. Add: any missing 0 m station → Minor, stating "collar orientation" or "first station" assumption. |
| SRV-02 | Dip/azimuth out of range | SUR-003, SUR-004 | E | Brief severity Critical: raise default to CRITICAL. |
| SRV-03 | Dip sign inconsistent / mixed in a hole | SUR-005 | E | Add a user-set convention parameter (negative-down / positive-down / auto). |
| SRV-04 | Duplicate depths identical / conflicting | SUR-002 | E | Severities to Minor (identical) / Major (conflicting). |
| SRV-05 | Out-of-sequence depths | SUR-017 | E | — |
| SRV-06 | Station beyond EOH | SUR-006 | E | — |
| SRV-07 | Collar az/dip vs first station (> 5° dip, > 10° az) | SUR-023 | M | New. |
| SRV-08 | Dogleg severity 3 / 6 °/30 m | SUR-010 | E | Brief formula `β = arccos(cos(I₂−I₁) − sin I₁ sin I₂ (1 − cos(A₂−A₁)))` — verify identical to `dogleg_deg`; Minor/Major. |
| SRV-09 | Neighbour-inconsistent station | SUR-013 | P | Today: azimuth spikes only. Extend to the 3-D direction test (i deviates > 2° from the i−1…i+1 interpolation while i−1 and i+1 agree within 1°/30 m). |
| SRV-10 | Station spacing > 50 m | SUR-008 | E | — |
| SRV-11 | Near-vertical (I < 3°) suppression reported | SUR-012 (partial) | P | Suppression applied in SUR-012 only, not reported. Apply to all azimuth-based rules and report it as INFO. |
| SRV-12 | North reference, declination, grid convergence | SUR-014 | M | New: needs north-reference / magnetic + corrected azimuth fields and project declination & convergence parameters. |
| SRV-13 | Magnetic interference indicators | SUR-027 | M | New: field-strength deviation; azimuth swing with stable dip on magnetic instruments. |
| SRV-14 | Desurvey sensitivity (tangent, balanced tangent, min. curvature) | SUR-015 | P | Today: min. curvature vs tangent. Add balanced tangent; report max positional difference; Minor > 2 m. |
| SRV-15 | Single-station / no-survey holes > 100 m | SUR-009, COL-019 | P | Add a length-thresholded INFO for straight-line assumption. |
| SCH-05 | Normalised hole-ID key groups; approve merges via a mapping table | COL-003 | P | COL-003 covers collar near-duplicates. Add cross-table grouping, the mapping table (save, apply, log) as a fix class. |
| SCH-04b | Closest-collar suggestion for orphans (difflib) | SUR-001, INT-006 | P | Today: exact folded-key hint. Add difflib suggestions. |
| SCH-01 | Required tables/fields missing or unmapped | IMP-010 | E | — |
| SCH-02 | Type violations | IMP-005 | E | — |
| SCH-03 | Duplicate primary keys | COL-001, SUR-002, INT-003 | E | — |
| SCH-04 | Orphans both directions | SUR-001, INT-006, COL-008, COL-009 | E | Severities: downhole orphans Critical, collars without data Minor. |
| SCH-06 | Blank vs zero vs missing-code ambiguity in one field | ASY-014 (assays only) | P | Generalise to every numeric field (new IMP-006 implementation). |
| COL-01 | Null, zero, dummy coordinates (−99, −999, 0, user list) | COL-002 | P | Add the sentinel list and zero test for X/Y; brief severity Critical. |
| COL-02 | Duplicate collar locations within 1 m | COL-004 | E | — |
| COL-03 | Swapped E/N | COL-006 | E | — |
| COL-04 | CRS plausibility; mixed coordinate systems | IMP-012, COL-006 | P | Add declared-zone range test and offset-cluster detection. |
| COL-07 | Data beyond EOH | COL-007 | E | Brief severity Critical. |
| COL-08 | Dates, drill-type codes | COL-014 | P | Dates exist. Add unknown drill-type codes (dictionary). |
| INT-01 | From ≥ To | INT-001 | E | Brief Critical. |
| INT-02 | Zero-length | INT-001 | E | Split zero length (Major) from From > To (Critical). |
| INT-03 | Overlaps; precision artefacts below tolerance | INT-002 | P | Micro-overlaps today INFO with 0.01 m. Use the global tolerance (§5.4) and report artefacts separately as Minor. |
| INT-04 | Gaps | INT-004 | E | Reference implementation, kept. |
| INT-05 | Interval beyond EOH | INT-005 | E | Brief Critical. |
| INT-06 | Sample length anomalies by drill type (< 0.1, > 6 m) | INT-007 | P | Add per-drill-type thresholds. |
| INT-07 | Duplicate sample IDs; sample-ID sequence QC-insert aware | SMP-001, SMP-002 | M | New. QC-insert awareness uses the R1 loader (P2); P1 uses GEOVALID PRO's current QC classification. |
| VAL-01 | BDL code inventory per field and batch | ASY-002, ASY-012 | P | Add per-batch inventory. |
| VAL-02 | Over-limit codes unresolved | ASY-005 | E | — |
| VAL-03 | Unit detection and mixed units | ASY-001, ASY-004 | E | — |
| VAL-04 | Mixed labs, methods, DLs in one field | ASY-010, ASY-019 | M | New (where lab/method/DL fields exist). |
| VAL-05 | > 100 %; Σ elements > 100 % | ASY-003 | P | Check the Σ all elements test is implemented; brief Critical. |
| VAL-06 | Stoichiometric caps by dominant mineral | — | M | New catalogue rule **ASY-028**. |
| VAL-07 | Major-oxide total 97–102 % | ASY-015 (98–101 %) | E | Thresholds configurable; brief defaults. |
| VAL-08 | Code-list violations vs a user code dictionary | LIT-001, INT-015 | P | Add a code dictionary (lithology, alteration, weathering, drill type, …) and INT-015. |
| VAL-09 | Downhole spikes > 10× both neighbours and > P95 | — | M | New catalogue rule **ASY-029**. |
| VAL-10 | Repeated-value runs ≥ 5 above DL | INT-009 (block copy) | P | New catalogue rule **ASY-030** for runs within one column. |

### P2

| Brief | Check | GEOVALID PRO | Status | Plan |
|---|---|---|---|---|
| F6 | Three-stage interval diff, grade reconciliation, change classes, metal deltas, per-hole hashes, accepted snapshots, change log | VER-001…008 | M | New module `versions/`. |
| VER-01 | Change to a hole locked in the accepted snapshot | — | M | New catalogue rule **VER-009** (Critical). |
| REC-01 | Sample in lab file not in DB and vice versa | SMP-004 | M | Needs R1 loader. |
| REC-02 | Value mismatch (tolerance max(0.5·DL, 0.1 %)) | ASY-020 | M | Needs R1 loader. |
| REC-03 | Unit/scale mismatch (×10³, ×10⁴) | ASY-020 (c) | M | — |
| REC-04 | BDL coding mismatch | ASY-020 (d) | M | — |
| REC-05 | Multiple results per sample | ASY-009 | M | Report all, never choose. |
| REC-06 | QC samples in the primary table / expected QC missing | CRS-008 | M | — |
| REC-07 | Random verification audit (seeded), export/import checklist | — | M | New workflow. |
| XTB-01 | Mineralised logged, no assays | ASY-008 | M | — |
| XTB-02 | Recovery > 100 % (5 %), recovered > interval | GEO-001 | E | Add recovered-length test. |
| XTB-03 | RQD > recovery | GEO-002 | E | — |
| XTB-04 | Density outside a user range by lithology | DEN-001 | P | Add the range table by lithology. |
| XTB-05 | Coverage mismatch between tables | INT-011 | M | — |
| XTB-06 | Weathering inversion | WTH-001 | M | — |
| XTB-07 | High grade in barren lithology | CRS-001 | M | — |
| COL-06 | Collar Z vs topography; exemptions; topography by date | COL-011 | P | Add underground/trench exemption field and dated topographies. |
| COL-06b | Systematic offset (median > 3 m, IQR < 2 m) | COL-012 | E | Align to the brief's test. |
| COL-05 | Licence boundary: KML/KMZ, SHP, GeoJSON, DXF, CSV, multipart, holes | COL-005 | P | Today CSV vertex list only. |
| SPA-01 | Trace above topography | SUR-016 (b) | E | Needs the R2 readers for all formats. |
| R2 | Topography readers (GeoTIFF incl. LZW/Deflate/PackBits/predictors/tiles, Surfer, BIL/FLT, HGT, XYZ, DXF, STR/DTM, OBJ, STL, PLY, SHP, KML/KMZ), windowed reading, local Delaunay, WGS84↔UTM | `io/spatial_inputs.py` (ASC, XYZ→TIN) | P | New package `io/topo/`. |

### P3

| Brief | Check | GEOVALID PRO | Status | Plan |
|---|---|---|---|---|
| F10 | JSON rule profiles (enabled, thresholds, severities, dictionaries, mappings, ID-merge table), profile hash, headless `--cli --project --profile --out`, exit codes, log file | YAML profile, `geovalid-cli.exe run` with exit codes 0–3 | P | Add JSON profiles, project files, log file. A separate console exe already exists. |
| SPA-02 | Hole clash < 1 m | SUR-016 (a) | E | Report minimum 3-D segment distance. |
| SPA-03 | Twin candidates | COL-004 (TWIN) | P | Add trace parallelism. |
| SPA-04 | Twin comparison | CRS-006 | M | — |
| SPA-05 | Drill-type bias (composite, pair, QQ, Wilcoxon) | CRS-002 | M | — |
| F12 | Code-mapping suggestions; robust Mahalanobis on CLR | ASY-025 (partly) | M | Off by default, INFO only. |

### Architecture (§5) and outputs (§8–9)

| Item | Status | Plan (phase) |
|---|---|---|
| 5.1 issue fields `category`, `source_file`, `fix_class`, `standards_refs` | P (has rule, severity, table, hole, field, value, messages, fix text, `src_row`) | P1 |
| 5.2 user-editable severity per rule | M | P1 (profile `severity_overrides`, GUI) |
| 5.3 registry with name, category, description, params, enabled, refs; catalogue generated from it | P (catalogue → `rules_meta.json`) | P1 (`docs/RULE_CATALOGUE.md` generated) |
| 5.4 global tolerance; precision artefacts separate | P (`depth_eps_m` exists) | P1 |
| 5.5 file SHA-256; per-hole canonical hash | P (file hashes) | P1 |
| 5.6 fix classes, approval, corrected copy + fix log | M | P1 (framework + ID mapping, azimuth 360→0, dip-sign flip) |
| 8.1 issues CSV + JSON; HTML: per-rule pass/fail, per-hole status, issue browser, thresholds, fingerprints, profile hash | P (CSV, XLSX, HTML) | P1 |
| 8.2 standards clause tags per rule | P (JORC tags in catalogue) | P1 (brief tags) |
| 8.3 Evidence pack HTML + JSON, QP sections empty; `EVIDENCE_SCHEMA.md` | M | P1 (P2/P3 add version, reconciliation and audit content) |
| 9 GUI: Issue Browser (filters, source row, export), Survey QA, Values, Cross-table, Lab & QA/QC, Topography & Boundary, Spatial, Rules & Profiles, Evidence Pack; DLS, twin/bias QQ, metal-delta charts | P (Issues page, charts) | P1: Issue Browser, Rules & Profiles, Survey QA, Values, Evidence Pack. P2: Cross-table, Lab & QA/QC, Topography & Boundary, versions. P3: Spatial. |
| 10 tests: positive + negative per rule; generator incl. every topography format; planar-surface accuracy; UTM round trip; regressions; performance 10 000 holes / 1 M rows | P (recall, clean twin, charts) | Each phase |

## 4. Structure additions

```
geovalid_pro/
  core/registry.py      rule metadata: name, category A–J, brief alias, standards tags, params, enabled, severity override
  core/fingerprint.py   file and per-hole canonical hashes
  core/fixes.py         fix classes, approval, corrected copies, fix_log
  rules/values.py       ASY-028/029/030, VAL inventory per batch, code dictionary (INT-015)
  rules/samples.py      SMP-001/002
  report/evidence.py    Data Verification Evidence Pack (HTML + JSON)
  versions/             P2: snapshots, three-stage diff, reconciliation, change log
  io/topo/              P2: topography readers, windowed grids, TIN, local Delaunay, UTM
  io/lab.py             P2: lab / QA-QC file loader (GEOQAQC format, R1)
```

## 5. Risks and open questions

1. **R1 (blocking for P2).** The GEOQAQC format cannot be extracted without its source or sample files. Requested from the owner.
2. **Severity changes.** Following the brief raises several defaults (e.g. SUR-003/004, INT-001, INT-005, COL-007 to CRITICAL). The CLI exit code on existing data changes accordingly (2 instead of 1). The synthetic recall gate is unaffected; the clean-twin gate stays clean.
3. **R2 scope.** A full GeoTIFF reader (LZW, predictors, tiles, BigTIFF) plus ten other formats is the largest single item. Risk is managed with format-independent planar-surface tests.
4. **Performance target** (10 000 holes, 1 M rows < 5 min): several current rules loop per row in Python; P1 measures and vectorises the hot ones.
5. **Python 3.14** is not used for the Windows build (scientific wheels); noted, not a blocker.
