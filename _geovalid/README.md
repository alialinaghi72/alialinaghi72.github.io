# GEOVALID PRO — design package

Exploration drillhole database validation, analysis and reporting system (اعتبارسنجی پایگاه دادهٔ اکتشافی).

**Status: DRAFT v0.1 for client approval (2026-10-22).** As the brief requires (§18), no code is written until this package is approved.

| File | Content |
|---|---|
| [`docs/00_requirements_brief.md`](docs/00_requirements_brief.md) | The client's requirements brief (source of truth, §0–§19) |
| [`docs/01_architecture.md`](docs/01_architecture.md) | Final architecture: modules, stack and licences, project container, rule engine, analysis layer, change management, scoring, reporting, GUI, CLI, performance, security, packaging, spikes |
| [`docs/02_data_schema.md`](docs/02_data_schema.md) | Canonical data schema: tables, fields, units, Persian/English header synonyms, system tables, import normalisation, constraints, storage |
| [`docs/03_rule_catalogue.md`](docs/03_rule_catalogue.md) | Rule catalogue: 229 rules in 18 families (all 68 brief rules + 161 additions), NEW rules for approval, deposit-type profiles, research provenance |
| [`docs/04_phase_plan.md`](docs/04_phase_plan.md) | Phase plan (P0–P5), test strategy (synthetic generator, error injector), CI gates, risks, client decisions |
| [`docs/05_traceability.md`](docs/05_traceability.md) | Requirement → design → phase matrix, deviations from the brief, phase of every rule, consolidated open decisions, review status |

This folder sits in the website repository only temporarily. GitHub Pages does not publish folders whose names start with `_`, but **the repository is public, so these files can be read on GitHub**. 04 §6.1 recommends moving the project to a dedicated private repository before Phase 0.
