**GEOVALID PRO 0.4.0, Windows x64 (portable, offline).** Drillhole database validation — v2 upgrade, Phase 2.

Unzip the archive, then run `GEOVALID\GEOVALID.exe`. No installation is needed. The quick-start guide (Persian/English) is `README_RUN.md`; the changes are in `CHANGELOG.md`. Screenshots of this exact build are in `screenshots/`.

New in 0.4.0:
- Laboratory reconciliation with the GEOQAQC file: samples missing either way, value, scale and detection-coding mismatches, sample-ID offsets, re-assays (listed, never chosen), QC samples stored as intervals, project error rate with its 95 % upper bound. CRM identity, mislabelled CRMs, CRM/blank swaps, umpire bias, duplicate–parent links.
- Random verification audit: seeded, reproducible checklist export and results import into the evidence pack.
- Cross-table checks: mineralised zones without assays, table coverage per hole, weathering inversions, grade in barren units, recovery and density by rock.
- Topography in 17 formats (GeoTIFF incl. LZW/Deflate/tiled/BigTIFF, Surfer, BIL/FLT, SRTM, XYZ, DXF, Surpac, OBJ, STL, PLY, Shapefile, KML/KMZ) and licence boundaries in 5 formats with multipart polygons and holes; WGS 84 ↔ UTM; sanity checks for swapped coordinates, wrong zone, false easting and feet vs metres; exemptions and dated topographies.
- Version comparison: unchanged holes skipped by hash, three-stage interval diff, change classes, metal change for all and common holes, change log; accepted snapshots with locked holes (any change = CRITICAL).
- New app pages: Cross-table, Lab & QA/QC, Topography & boundary, Versions.

109 validation rules. This build was produced by GitHub Actions on Windows. Before publishing, its unit tests, injected-error recall tests, and CLI and GUI smoke tests all passed.

This is a decision-support tool. Final acceptance of data for public reporting rests with the Competent/Qualified Person.
