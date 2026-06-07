# SciQuery

[![Code License: MIT](https://img.shields.io/badge/Code%20License-MIT-yellow)](LICENSE)
[![Data License: CC0 1.0](https://img.shields.io/badge/Data%20License-CC0%201.0-lightgrey)](https://creativecommons.org/publicdomain/zero/1.0/)
[![Python](https://img.shields.io/badge/python-3.11-blue)](https://www.python.org/)
[![CI smoke run](https://github.com/HadiQaemi/SciQ/actions/workflows/ci.yml/badge.svg)](https://github.com/HadiQaemi/SciQ/actions/workflows/ci.yml)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20580183.svg)](https://doi.org/10.5281/zenodo.20580183)

## Quick start

- Use `evaluation/gold_eval.jsonl` for evaluation.
- Canonical paper-disjoint gold split: **520 train / 153 test**.
- Score predictions:


Raw Dryad data are not redistributed. Reconstruct databases from the original Dryad records before executing SQL locally.

## Layout

| Path | Contents |
|---|---|
| `benchmark/gold_items.jsonl` | 673 expert-validated gold items (question, gold SQL, recorded answer, audit fields). |
| `benchmark/candidate_pool.jsonl` | 707 candidate items (incl. non-gold; see `pipeline_status`). |
| `benchmark/train_pool.jsonl` · `test_pool.jsonl` | Paper-disjoint split of the **full candidate pool** (549 / 158). |
| `benchmark/item_schema.md` | Field reference for item records. |
| `evaluation/gold_eval.jsonl` | Flat eval file: 673 gold items with embedded answers; gold split 520 / 153. |
| `evaluation/eval_results.csv` | Per-item execution-accuracy results. |
| `sql/gold_sql.jsonl` · `gold_answers.jsonl` | Gold SQL and recorded gold result per item. |
| `sql/schema_metadata.jsonl` | Per-database table/column schema (see below). |
| `sql/schema_field_flags.csv` · `execution_report.json` | Cryptic/coded flags; gold-SQL execution summary. |
| `metadata/dryad_manifest.jsonl` | Per-record source metadata: Dryad DOI/URL, paper title, publication DOI/year, domain, license, source files. |

## Schema metadata

Each column in `sql/schema_metadata.jsonl` carries: `name`, `type`, `description` (from the source data dictionary where available), and **data-derived** fields — `unit` (from column names), `value_domain` (categorical encodings), `value_range` (numeric min/max), `missing_tokens` (missing-value conventions present in the data) — plus `cryptic_name` / `coded_value` flags.

## Splits & gold

- **Gold** = only the 673 expert-validated items (`gold_items.jsonl` / `gold_eval.jsonl`). Candidate items are auxiliary — treat as gold only when `pipeline_status == "gold"`.
- `benchmark/{train,test}_pool.jsonl` split the full 707-item candidate pool (549 / 158); `evaluation/gold_eval.jsonl` carries the gold-only split (520 / 153).
- Source data are licensed **CC0 1.0** (Dryad); per-record provenance is in `metadata/dryad_manifest.jsonl`.
