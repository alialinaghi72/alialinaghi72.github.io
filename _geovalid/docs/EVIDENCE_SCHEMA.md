# Evidence pack JSON schema — `geovalid-evidence/1.0`

GEOVALID PRO writes `evidence_pack.json` next to `evidence_pack_<lang>.html` in every output folder (v2 brief §8.3).
The HTML and the JSON hold the same content. The schema is versioned: a change that removes or renames a key
increases the major number; adding keys increases the minor number.

| Key | Type | Content |
|---|---|---|
| `schema` | string | `"geovalid-evidence/1.0"` |
| `generated_utc` | string | ISO-8601 time the pack was written |
| `application` | object | `name`, `version` |
| `run` | object | `run_id`, `project`, `started`, `finished` |
| `dataset` | object | `files`: list of {`file`, `sheet`, `sha256`, `table`, `kind`} for every input (tables, DEM, licence, CRM); `dataset_hash`: SHA-256 over the sorted per-hole canonical hashes; `hole_count`; `hole_hashes_file`: name of the CSV with one hash per hole |
| `profile` | object | `hash`: SHA-256 of the canonical JSON of the rule profile used; `depth_tolerance_m`; `severity_overrides`; `disabled_rules` |
| `summary` | object | `issues_by_severity` {CRITICAL, ERROR, WARNING, INFO}; `issues_by_category` {A…J}; `rules` {PASS, FAIL, NOT_APPLICABLE, DISABLED, FAILED} |
| `clauses` | list | one object per standards tag (below) |
| `fixes` | object | `applied` (bool); `log_file`; `by_class` {fix class: count}; `log`: up to 500 rows {`fix_class`, `rule`, `file`, `row`, `field`, `old`, `new`, `timestamp`, `user`} |
| `version_comparison` | object | `{"status": "not run"}` until a version comparison is run (P2); then its summary |
| `qaqc_reconciliation` | object | `status`; `rules`: QA/QC rule results; `insertion_rates` per table; `lab_file_reconciliation` (P2) |
| `random_audit` | object | `{"status": "not run"}` until a random verification audit is run (P2) |
| `qp_sections` | object | `procedures_applied`, `limitations`, `opinion_on_adequacy`: always empty strings. Only the Qualified / Competent Person fills them; the software never writes an opinion |

## Clause object

| Key | Type | Content |
|---|---|---|
| `tag` | string | One of `JORC-T1-S1-Verification`, `JORC-T1-S1-Location`, `JORC-T1-S3-DBIntegrity`, `NI43101-F1-Item12`, `SK1300-601b96-iii-B-9`, `CIM2019-4.2`, `CIM2019-4.5`, `CIM2019-6.2` |
| `title` | string | Clause title |
| `rules` | list | {`id`, `aliases` (v2 brief IDs), `name`, `category`, `status` (RUN, NOT_APPLICABLE, DISABLED, FAILED), `result` (PASS, FAIL or the status), `n_issues`, `worst`, `standards`} for every rule carrying the tag |
| `results` | object | counts of `PASS`, `FAIL`, `NOT_APPLICABLE`, `DISABLED`, `FAILED` |
| `open_issues` | object | open issues of these rules by severity |
| `top_issues` | list | up to 25 most severe open issues {`issue_id`, `rule_id`, `severity`, `table`, `hole_id`, `from_m`, `to_m`, `source_file`, `src_row`, `message_en`} |

`PASS` means the rule ran and raised nothing above INFO; `FAIL` means it raised at least one WARNING, ERROR or CRITICAL.
`src_row` is the line number in the source file, with the header on line 1.
