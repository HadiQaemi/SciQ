# Item schema (`benchmark/*.jsonl`)

Each line of `gold_items.jsonl`, `candidate_pool.jsonl`, `train_pool.jsonl`, and
`test_gold.jsonl` is one JSON object with the fields below.

## Identity & provenance
| field | type | description |
|---|---|---|
| `item_uid` | string | Stable unique id for the item (primary key across all logs). |
| `db_id` | string | Sanitised record dir id, e.g. `doi_10.5061_dryad.brv15dvkg`. |
| `record_id` | string | Canonical Dryad record id, e.g. `doi:10.5061/dryad.brv15dvkg`. |
| `index` | int | Original 0-based index of the item within its record. |
| `claim_source` | object | `{origin, paper_section, paper_location, ...}` — where the claim comes from. |

## Task
| field | type | description |
|---|---|---|
| `question` | string | The natural-language analytical question. |
| `query` | string | The gold **PostgreSQL** query (executed against the record's schema). |
| `category` | enum | `paper-claim` \| `supporting` \| `QC` (authoritative reviewer category). |
| `category_auto_suggested` | enum | Auto-suggested category before review (advisory only). |
| `difficulty` | enum | `easy` \| `medium` \| `hard`. |
| `statistical_task` | enum | `descriptive` \| `inferential_test` \| `distribution` \| `regression` \| `correlation` \| `window_analysis`. |
| `postgres_function_used` | list/string | PostgreSQL feature(s) exercised (e.g. `percentile_cont`, `regr_slope`). |

## Answer & validation state
| field | type | description |
|---|---|---|
| `recorded_answer` | any | The gold answer Expert A recorded from executing `query` (null until recorded). |
| `evidence_locator` | object | Where in the dataset/paper the answer is grounded. |
| `python_crosscheck_status` | enum | `match` \| `mismatch` \| null — automatic Python oracle comparison. |
| `pipeline_status` | enum | `draft` \| `submitted_to_b` \| `gold` \| `needs_revision` \| `excluded`. |
| `validation_status` | enum | `expert_b_validated` (gold) \| `candidate`. |
