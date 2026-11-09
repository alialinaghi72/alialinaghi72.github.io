# Reference material (read-only)

`qaqc_samples/` holds sample input files in the format of the owner's separate QA/QC application **GEOQAQC**, received
on 2026-11-09. They define the laboratory / QA-QC file format GEOVALID PRO must read without editing (v2 brief R1,
option B). The format, and the assumptions the owner confirmed, are in `../docs/QAQC_FORMAT.md`.
Never edit these files: the R1 acceptance test (`app/tests/test_lab.py`) loads them as they are. They are not committed to the public repository (see `.gitignore`); the test is skipped where they are absent.

| File | Content |
|---|---|
| `assay.csv` | Lab / QA-QC file with long sample-type codes (FIELD DUP, CRM, BLANK, COARSE DUP, PULP DUP); no hole or depth columns |
| `demo_assay.csv` | Lab / QA-QC file with short codes (FD, STD, PD, CBLK, CD, PBLK), hole, depths, drill type, lab, date; contains re-assays and text codes |
| `crm_certificates.csv` | CRM certificates; `ELEMENT` written as the assay column name (`Cu_pct`) |
| `demo_crm_certificates.csv` | CRM certificates; `ELEMENT` as the element symbol with a declared `UNIT` (Au in ppb) |
| `umpire_lab2.csv` | Check / umpire laboratory file paired by `SAMPLE_ID` |
