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
| `dataset` | object | `files`: list of {`file`, `sheet`, `sha256`, `table`, `kind`} for every input (tables, topography, licence, CRM, laboratory and umpire files); `dataset_hash`: SHA-256 over the sorted per-hole canonical hashes; `hole_count`; `hole_hashes_file`: name of the CSV with one hash per hole |
| `profile` | object | `hash`: SHA-256 of the canonical JSON of the rule profile used; `depth_tolerance_m`; `severity_overrides`; `disabled_rules` |
| `summary` | object | `issues_by_severity` {CRITICAL, ERROR, WARNING, INFO}; `issues_by_category` {A…J}; `rules` {PASS, FAIL, NOT_APPLICABLE, DISABLED, FAILED} |
| `clauses` | list | one object per standards tag (below) |
| `fixes` | object | `applied` (bool); `log_file`; `by_class` {fix class: count}; `log`: up to 500 rows {`fix_class`, `rule`, `file`, `row`, `field`, `old`, `new`, `timestamp`, `user`} |
| `version_comparison` | object | `{"status": "not run"}` without a previous version or snapshot. Otherwise: `holes` {`baseline`, `current`, `added`, `deleted`, `common`, `unchanged`, `changed`}; `added_holes`, `deleted_holes`, `changed_holes` (lists, capped); `change_classes` {class: count} with classes `hole added`, `hole deleted`, `collar moved`, `survey changed`, `interval added`, `interval removed`, `re-segmented`, `re-assayed`, `code changed`, `metadata changed`; `metal`: per analyte and scope (`all holes`, `common holes`) {`unit`, `old_metres`, `new_metres`, `old_metal`, `new_metal`, `delta_metal`, `delta_pct`, `old_grade`, `new_grade`} with metal = Σ(length × grade); `baseline_files` {`file`, `sha256`, `kind`}; `change_log_file` (`change_log.csv`); `accepted_snapshot` {`file`, `accepted_at`, `reviewer`, `note`, `app_version`, `dataset_hash`, `locked_holes` (count), `locked_holes_changed` (hole IDs, VER-009)} |
| `topography` | object | `surfaces`: one object per topography {`label`, `date`, `file`, `format`, `extent` [xmin, ymin, xmax, ymax], `resolution`, `n_points` / `n_cells` / `n_triangles`, `nodata`, `crs`, `notes`}; `licence` {`format`, `polygons`, `rings`, `vertices`, `extent`, `crs`, `notes`, `alignment`}; `sanity` {`n_collars`, `n_with_topography`, `inside_extent`, `elevation_ratio`, `findings` [[severity, message]], `not_checked` (hole IDs), `blocked` (cause, when a gross CRS or unit problem stopped the ΔZ rules)} |
| `qaqc_reconciliation` | object | `status`; `rules`: QA/QC rule results; `insertion_rates` per table; `lab_file_reconciliation`: `{"status": "not run"}` without a laboratory file, else `lab_file`, `samples` {`lab_rows`, `lab_routine`, `lab_routine_not_in_db`, `db_samples_in_scope`, `db_samples_not_in_lab`, `scope`}, `values` per assay column {`table`, `column`, `lab_column`, `unit`, `lab_unit`, `pairs`, `match`, `coding`, `rounded`, `scale`, `mismatch`, `missing in database`, `no laboratory result`}, `error_rate` {`compared`, `mismatched`, `rate_pct`, `upper95_pct` (Clopper–Pearson)} |
| `random_audit` | object | Before results are imported: `status` ("selection ready …"), `seed`, `pct`, `min_n`, `population`, `selected`, `selection_hash`. After import: also `file`, `rows_in_file`, `checked`, `verified`, `discrepancies`, `unchecked`, `rate_pct`, `upper95_pct`, `selection_matches` (the file is the selection this dataset and seed produce), `checked_by`, `discrepancy_rows` [{`audit_id`, `hole_id`, `sample_id`, `from_m`, `discrepancy`, `checked_by`}] |
| `spatial` | object | v2 F11: `clash_pairs` [{`a`, `b`, `distance_m` (minimum 3-D segment distance), `depth_a_m`, `depth_b_m`}]; `twin_pairs` [{`a`, `b`, `collar_dist_m`, `angle_deg`, `method_a`, `method_b`}]; `twin_comparisons` and `drilling_method_bias` [{holes or methods, `analyte`, `n`, `mean_a`, `mean_b`, `mean_ratio`, `mean_rel_diff`, `median_rel_diff`, `mean_diff`, `wilcoxon_p`, `pair_dist_median_m` (bias only)}] |
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
