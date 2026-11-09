# Laboratory and QA/QC file format (GEOQAQC) — v2 brief R1

| | |
|---|---|
| Source | Sample files from the owner's GEOQAQC application (`reference/qaqc_samples/`, received 2026-11-09). GEOQAQC's source code was not available, so this is **option B**: the format is inferred from the samples. |
| Status | **Confirmed by the owner on 2026-11-09** (sample-type codes, text codes, CRM unit conversion, repeated sample IDs). |
| Implementation | `geovalid_pro/io/lab.py` (readers), `geovalid_pro/rules/reconcile.py` (REC-01…06), `geovalid_pro/rules/qaqc.py` (QAQ rules on the laboratory file), `geovalid_pro/audit.py` (REC-07). Tests: `app/tests/test_lab.py` (synthetic files in this format; the reference counts in §6 run where the sample files exist locally). Implemented in GEOVALID PRO 0.4.0. |

A user prepares the file once for GEOQAQC and loads the same file in GEOVALID PRO without editing it.

## 1. Files

| Role | Example | Required columns | Optional columns |
|---|---|---|---|
| Laboratory / QA-QC file | `assay.csv`, `demo_assay.csv` | `SAMPLE_ID`, `SAMPLE_TYPE`, ≥ 1 element column | `CRM_ID`, `PARENT_ID`, `BATCH`, `SEQ`, `HOLE_ID`, `FROM`, `TO`, `DRILL_TYPE`, `LAB`, `DATE` |
| Check / umpire file | `umpire_lab2.csv` | `SAMPLE_ID`, ≥ 1 element column | `LAB`, `BATCH` |
| CRM certificates | `crm_certificates.csv`, `demo_crm_certificates.csv` | `CRM_ID`, `ELEMENT`, `CERTIFIED`, `SD` | `UNIT` |

File types: CSV/TXT (any delimiter and encoding the GEOVALID reader detects: UTF-8 with or without BOM, cp1252,
cp1256) and XLSX/XLS. The header is the first row. Column names are matched case-insensitively, ignoring spaces, `_`
and `-`; GEOVALID's mapping synonyms also apply (e.g. `SampleID`, `Sample No`), and the mapping can be edited in the
program like any other table.

## 2. Columns

| Column | Meaning | Rules |
|---|---|---|
| `SAMPLE_ID` | Sample ticket number | Key for pairing with the database and the umpire file. A repeated ID is a **re-assay** (§4). |
| `SAMPLE_TYPE` | Routine sample or QC type | Codes in §3. An unknown code is reported (never guessed). |
| `CRM_ID` | Reference material name | Required when the type is a CRM; matched to the certificate `CRM_ID` ignoring case and surrounding spaces only. `DEMO-501` and `DEMO 501` are different IDs: QAQ-008 reports the near match, and the profile's `crm_id_aliases` maps it explicitly. |
| `PARENT_ID` | Original sample of a duplicate | Explicit link. **No suffix stripping**: `S00003-FD` is linked to `S00003` only because `PARENT_ID` says so. |
| `BATCH` | Laboratory job / certificate | Grouping for detection limits, coding and QC per batch. |
| `SEQ` | Insertion order in the sample stream | Used for QC-insert-aware sequence checks. |
| `HOLE_ID`, `FROM`, `TO` | Location of routine samples | QC rows may carry the hole of the stream they were inserted in, with empty depths. |
| `DRILL_TYPE`, `LAB`, `DATE` | Metadata | `DATE` ISO `YYYY-MM-DD`. |
| Element columns | `<Element>_<unit>`, e.g. `Cu_pct`, `Au_ppm`, `Ag_ppm`, `Mo_ppm` | Unit from the header suffix (`pct` = %, `ppm`, `ppb`, `gpt`/`g_t` = g/t). Units are stored as received, never converted. |

## 3. Sample-type codes (confirmed)

| Code(s) | Class | Notes |
|---|---|---|
| `SAMPLE` | Routine sample | |
| `STD`, `CRM` | Certified reference material | `CRM_ID` required |
| `BLANK` | Blank | |
| `CBLK` | Coarse blank | |
| `PBLK` | Pulp blank | |
| `FD`, `FIELD DUP` | Field duplicate | `PARENT_ID` required |
| `CD`, `COARSE DUP` | Coarse (crush) duplicate | `PARENT_ID` required |
| `PD`, `PULP DUP` | Pulp duplicate | `PARENT_ID` required |

Matching ignores case, surrounding spaces and the separators ` `, `_`, `-` (so `FIELD_DUP` = `FIELD DUP`). Any other code
is reported by REC-06 with its count; the rows are not used until the code is added to the profile
(`lab_sample_types`).

## 4. Values and codes (confirmed)

| Written as | Meaning | Handling |
|---|---|---|
| number (`0.1543`) | Measured value | As received |
| `<x` (`<0.005`) | Below detection limit x | Flag BDL, DL = x; never replaced by ½DL in comparisons |
| `>x` | Above the upper limit x | Flag over-limit (ODL) |
| `IS` | Insufficient sample | **Not analysed**: kept as a code, never zero or ½DL |
| `LNR` | Listed, not received | **Not analysed**: kept as a code |
| empty | Not reported | Not analysed |
| repeated `SAMPLE_ID` | Re-assay | REC-05 lists every result and shows which one the database holds; GEOVALID never chooses |

## 5. CRM certificates (confirmed)

`ELEMENT` is either the assay column name (`Cu_pct`) or the element symbol (`Cu`) with a declared `UNIT`.
When the declared unit differs from the assay column's unit, the certified value and SD are converted with the declared
unit (e.g. Au 312 ppb → 0.312 ppm). Every conversion is listed in the report. A certificate without a unit is used only
when its `ELEMENT` is the column name (the unit is then the column's).

## 6. Reference counts (R1 acceptance test)

| File | Rows | SAMPLE | FD | CD | PD | CRM | BLANK | CBLK | PBLK |
|---|---|---|---|---|---|---|---|---|---|
| `demo_assay.csv` | 1 466 | 1 202 | 60 | 36 | 48 | 60 | 0 | 36 | 24 |
| `assay.csv` | 448 | 320 | 32 | 16 | 16 | 32 | 32 | 0 | 0 |
| `umpire_lab2.csv` | 80 | 80 check results | | | | | | | |

`demo_assay.csv` also contains, by design: 2 re-assayed sample IDs (`GQ00141`, `GQ00142`), 1 duplicate whose
`PARENT_ID` is not in the file, 3 `IS` and 2 `LNR` codes.
