# Changelog — GEOVALID PRO

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
