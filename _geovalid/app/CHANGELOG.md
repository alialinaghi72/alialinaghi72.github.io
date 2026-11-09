# Changelog — GEOVALID PRO

## 0.4.0 — v2 upgrade, Phase 2 (2026-11-09)

Brief: `../docs/06_v2_upgrade_brief.md` (F6–F9, R1, R2). Laboratory format: `../docs/QAQC_FORMAT.md`. 90 → 109 rules.

**Laboratory and QA/QC reconciliation (F7, R1 — GEOQAQC format inferred from the owner's sample files, confirmed)**
- Readers (`io/lab.py`): laboratory / QA-QC file, umpire file, CRM certificates with declared units. Sample-type codes
  SAMPLE, STD/CRM, BLANK, CBLK, PBLK, FD, CD, PD; `<x` = below detection; IS and LNR = not analysed; repeated
  SAMPLE_ID = re-assay. Unknown codes are kept and reported.
- REC-01…06 (`rules/reconcile.py`): SMP-004 samples missing either way (suggestions only from the other side's orphans),
  ASY-020 value / scale / detection-coding mismatches, rounding, sample-ID offset runs, project error rate with the
  95 % Clopper–Pearson bound, ASY-009 re-assays listed (never chosen) and umpire results held in the database, CRS-008
  QC samples stored as intervals, unknown codes, QC rows without results.
- QA/QC on the laboratory file when the database has no QC: QAQ-006 mislabelled CRM and CRM/blank swap (new),
  QAQ-007 umpire bias (new), QAQ-008 CRM identity (no silent ID matching; `crm_id_aliases`), QAQ-010 duplicate–parent
  link (new); QAQ-002 converts certified values by the declared unit, flags CRMs reported below detection and probable
  unit errors. SMP-002 counts laboratory-issued numbers as used.
- REC-07 random verification audit (`audit.py`): seeded, reproducible selection; checklist export (XLSX/CSV); results
  import with a selection-hash check; summary and discrepancies in the evidence pack.

**Cross-table consistency (F8)**
- ASY-008 (XTB-01) mineralised zones without assay coverage; INT-011 (XTB-05) per-hole table coverage and coverage
  within mineralised zones (heat map); WTH-001 (XTB-06) weathering inversions with fault control; CRS-001 (XTB-07) high
  grade in barren-logged units and low grade in logged ore zones.
- GEO-001 recovered length beyond the interval (XTB-02); DEN-001 user density ranges by logged code and robust fences
  per code × weathering (XTB-04). Mineralised / barren codes are the project's own (profile or app dialog).

**Topography and licence boundary (F9, R2)**
- Topography readers (`io/topo.py`, `io/tiff.py`, `io/vector.py`): ESRI ASCII, Surfer DSAA/DSBB/DSRB, BIL/BIP/BSQ/FLT,
  GeoTIFF (strips and tiles; none, Deflate, LZW, PackBits; predictors 2 and 3; BigTIFF; GeoKeys; GDAL_NODATA;
  windowed reading), SRTM `.hgt`, regular XYZ grids and point clouds, DXF points / contours / 3DFACE / polyface,
  Surpac `.str` + `.dtm`, OBJ, STL, PLY, Shapefile PointZ / PolylineZ, KML/KMZ. Auto-detection by extension and magic
  bytes, manual override; each reader reports what it read. Points and contours: local Delaunay with a support
  distance (no full-area TIN); meshes: grid-indexed point-in-triangle.
- WGS 84 ↔ UTM (`io/geo.py`, Krüger series, sub-millimetre); geographic surfaces and boundaries are bridged to the
  declared zone (or the inferred one, reported); other datums are reported, never shifted.
- Licence boundary (`io/boundary.py`): KML/KMZ, Shapefile (+ .prj), GeoJSON, DXF closed polylines, CSV/TXT/XLSX vertex
  lists; multipart polygons and holes (even–odd ray casting). COL-005 buffer tolerance.
- COL-025 sanity checks before any ΔZ comparison: no overlap (swapped E/N, false easting or northing, another zone,
  another CRS), feet vs metres (ratio ≈ 3.28), collars outside the topography reported as not checked. COL-011
  exemptions through a chosen collar field and topography chosen by date; COL-012 vertical-datum offset (COL-06b).

**Version comparison (F6)**
- `versions.py`: per-hole hashes skip unchanged holes; collar, survey (end-of-hole shift) and three-stage interval diff
  (exact key match, overlap clustering, true additions / removals); change classes; metal-weighted deltas and grade
  reconciliation for all holes and common holes; change log (`change_log.csv`, XLSX export).
- Accepted snapshots (JSON manifest: file, per-hole and profile hashes, version, reviewer, date, note, locked holes).
  VER-009 (brief VER-01) reports any change to a locked hole as CRITICAL. VER-001…005 on the comparison.

**Desktop app**
- New pages: Cross-table (coverage heat map, code dialog), Lab & QA/QC (reconciliation chart, CRM, umpire and HARD
  charts, audit export / import), Topography & boundary (what was read, sanity checks, ΔZ map), Versions (metal change
  chart, change classes, filterable change log, accept snapshot).
- New optional inputs: laboratory file, umpire file, previous version folder, accepted snapshot; topography and
  boundary file filters list every format. The sample project now includes matching laboratory files and a previous
  version. Evidence-pack page columns no longer overflow.

**Reports and command line**
- Evidence pack: version comparison (holes, change classes, metal reconciliation, accepted snapshot and locked holes
  changed), topography and boundary, laboratory reconciliation with the error rate, random audit summary.
- CLI: `--lab`, `--umpire`, `--baseline`, `--snapshot`, `--accept-snapshot --reviewer --note --lock`,
  `--audit-export`, `--audit-results`, `--topo-format`.
- Column mapping takes the best match across all fields first (`RecM` = recovered length, not recovery %).

**Tests:** 126 (+69): laboratory reconciliation with one discrepancy of each class and a clean twin, the owner's
GEOQAQC reference counts (run locally only; the files are not in the public repository), cross-table cases, every
topography format reading a plane back within 1e-6 m, UTM round trip < 1 mm, boundary formats with parts and holes,
sanity checks, dated topographies, version comparison and snapshots. GeoTIFF decoding was also cross-checked against
files written by Pillow (libtiff) and tifffile.

## 0.3.0 — v2 upgrade, Phase 1 (2026-11-09)

Brief: `../docs/06_v2_upgrade_brief.md`; plan and gap table: `../docs/07_v2_gap_analysis.md`.

**Core (v2 §5)**
- Issue model: `category` (A–J), `rule_alias` (v2 brief IDs), `source_file`, `src_row` (line in the file), `fix_class`,
  `standards_refs`, `severity_default`.
- Rule registry metadata (`core/registry.py`): category, brief aliases, JORC / NI 43-101 / S-K 1300 / CIM clause tags.
  `docs/RULE_CATALOGUE.md` is generated from it (`tools/gen_rule_catalogue.py`).
- Profile: per-rule severity overrides (v2 defaults included), disabled rules, code dictionaries, dip convention,
  north reference, declared CRS. Profiles are saved as versioned JSON; YAML profiles still load.
- Global depth tolerance: overlaps and gaps no larger than it are precision artefacts (new INT-012), reported apart.
- Fingerprints: SHA-256 of every input, per-hole canonical hashes (`hole_hashes.csv`), dataset hash, profile hash.
- Fix classes (`core/fixes.py`): ID_MAP, AZ_360, AZ_WRAP, SURVEY_DUP_IDENTICAL, INTERVAL_DUP_IDENTICAL. Applied only after
  approval per class; writes corrected copies plus `fix_log.csv`. Sources are never modified.

**Rules (v2 §7, P1)** — 76 → 90 rules
- Survey QA pack: SUR-007 (missing 0 m station, states the desurvey assumption), SUR-009 (straight-line holes > 100 m),
  SUR-012 (near-vertical suppression reported), SUR-013 (3-D neighbour-inconsistent station), SUR-014 (north reference,
  magnetic vs corrected azimuth), SUR-015 (tangential / balanced tangential / minimum curvature sensitivity), SUR-023
  (collar vs first station), SUR-027 (magnetic interference indicators). Dip convention can be set in the profile.
- Hole IDs: COL-003 groups IDs across all tables by a normalised key and suggests a target (ID mapping table);
  SUR-001 / INT-006 suggest the closest collar IDs.
- Completeness: IMP-006 (blank vs zero vs missing codes), IMP-012 (CRS plausibility, mixed coordinate systems),
  COL-002 dummy coordinates, COL-014 drill-type codes, INT-001 / INT-002 severities, INT-007 by drill type,
  SMP-001 (duplicate sample IDs), SMP-002 (QC-aware numbering gaps, downhole order).
- Values: ASY-002 below-detection coding by batch, ASY-003 sum of elements, ASY-010 detection limits, ASY-015 97–102 %,
  ASY-019 labs and methods, ASY-028 stoichiometric caps, ASY-029 downhole spikes, ASY-030 repeated values,
  INT-015 code dictionary.
- ASY-004 unchanged since 0.2.0. INT-009 vectorised (10× faster).

**Outputs (v2 §8)**
- `issues.json`; HTML report: PASS/FAIL per rule, status by hole, issue filters by severity and category,
  severity overrides, dataset fingerprints.
- Data Verification Evidence Pack (`evidence_pack_<lang>.html`, `evidence_pack.json`, schema
  `docs/EVIDENCE_SCHEMA.md`) by JORC, NI 43-101, S-K 1300 and CIM clauses, with empty Qualified Person sections.

**Desktop app (v2 §9)**
- New pages: Survey QA (downhole dip, azimuth and dogleg chart; desurvey sensitivity), Values, Rules & profiles
  (enable, severity, thresholds, code dictionaries, JSON profiles), Evidence pack (with the fix-approval dialog).
- Issue Browser: filters by severity, category, rule, table and hole; double-click shows the source file and line;
  export of the filtered view.
- Command line: `--codes` (code dictionary), JSON profiles.

**Performance** — 10 000 holes and 1.09 million rows validate in about 105 s (`tools/perf_bench.py 10000 100`).

## 0.2.0 — grade versus logged geology, redesigned interface
## 0.1.0 — first release
