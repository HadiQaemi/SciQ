#!/usr/bin/env python3
"""Integrity smoke test for the SciQuery NL->SQL benchmark bundle.

Runs in CI with no database and no network (Python standard library only).
It checks that the released files are well-formed and internally consistent:
record counts, required fields, paper-disjoint train/test splits, the canonical
category vocabulary, and cross-file key agreement.

Usage:  python tests/test_bundle_integrity.py
Exit code 0 = all checks pass, 1 = one or more failures.
"""
from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATEGORIES = {"QC", "Supporting", "Paper-Claim"}

_failures: list[str] = []
_checks = 0


def check(cond: bool, msg: str) -> None:
    global _checks
    _checks += 1
    if cond:
        print(f"  ok    {msg}")
    else:
        _failures.append(msg)
        print(f"  FAIL  {msg}")


def load_jsonl(rel: str) -> list[dict]:
    path = ROOT / rel
    rows: list[dict] = []
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:  # malformed line => recorded failure
            _failures.append(f"{rel}:{i} invalid JSON: {exc}")
            print(f"  FAIL  {rel}:{i} invalid JSON: {exc}")
    return rows


def main() -> int:
    print("SciQuery bundle integrity checks\n")

    gold = load_jsonl("benchmark/gold_items.jsonl")
    cand = load_jsonl("benchmark/candidate_pool.jsonl")
    train = load_jsonl("benchmark/train_pool.jsonl")
    test = load_jsonl("benchmark/test_pool.jsonl")
    geval = load_jsonl("evaluation/gold_eval.jsonl")
    gsql = load_jsonl("sql/gold_sql.jsonl")
    gans = load_jsonl("sql/gold_answers.jsonl")
    manifest = load_jsonl("metadata/dryad_manifest.jsonl")
    schema = load_jsonl("sql/schema_metadata.jsonl")

    # --- record counts -------------------------------------------------------
    check(len(gold) == 673, f"gold_items == 673 (got {len(gold)})")
    check(len(cand) == 707, f"candidate_pool == 707 (got {len(cand)})")
    check(len(train) == 549, f"train_pool == 549 (got {len(train)})")
    check(len(test) == 158, f"test_pool == 158 (got {len(test)})")
    check(len(train) + len(test) == len(cand), "train_pool + test_pool == candidate_pool")
    check(len(geval) == 673, f"gold_eval == 673 (got {len(geval)})")
    check(len(gsql) == 673, f"gold_sql == 673 (got {len(gsql)})")
    check(len(gans) == 673, f"gold_answers == 673 (got {len(gans)})")
    check(len(manifest) == 30, f"dryad_manifest == 30 (got {len(manifest)})")
    check(len(schema) == 30, f"schema_metadata == 30 (got {len(schema)})")

    # --- gold items ----------------------------------------------------------
    check(all(g.get("pipeline_status") == "gold" for g in gold),
          "every gold item has pipeline_status == 'gold'")
    uids = [g["item_uid"] for g in gold]
    check(len(set(uids)) == len(uids), "gold item_uid values are unique")
    bad = sorted({g.get("category") for g in gold} - CATEGORIES)
    check(not bad, f"gold category vocabulary is {sorted(CATEGORIES)} (offenders: {bad})")

    # --- gold_eval split -----------------------------------------------------
    split_counts = Counter(r.get("split") for r in geval)
    check(split_counts.get("train") == 520 and split_counts.get("test") == 153,
          f"gold_eval split is 520 train / 153 test (got {dict(split_counts)})")
    check(all(r.get("question") and r.get("gold_sql") for r in geval),
          "gold_eval rows have non-empty question and gold_sql")
    bad = sorted({r.get("category") for r in geval} - CATEGORIES)
    check(not bad, f"gold_eval category vocabulary (offenders: {bad})")

    # --- paper-disjoint splits ----------------------------------------------
    def dbset(rows: list[dict]) -> set:
        return {r.get("db_id") for r in rows}

    check(not (dbset(train) & dbset(test)),
          "candidate train/test are paper-disjoint (no shared db_id)")
    ge_train = {r["db_id"] for r in geval if r.get("split") == "train"}
    ge_test = {r["db_id"] for r in geval if r.get("split") == "test"}
    check(not (ge_train & ge_test),
          "gold_eval train/test are paper-disjoint (no shared db_id)")

    # --- cross-file key agreement -------------------------------------------
    gold_uids = {g["item_uid"] for g in gold}
    check(gold_uids == {r["item_uid"] for r in gsql}, "sql/gold_sql uids == gold_items uids")
    check(gold_uids == {r["item_uid"] for r in gans}, "sql/gold_answers uids == gold_items uids")

    gold_ids = {f"{g['db_id']}::{g['index']}" for g in gold}
    check({r["item_id"] for r in geval} == gold_ids,
          "gold_eval item_id set == gold_items 'db_id::index'")

    uid_by_id = {f"{g['db_id']}::{g['index']}": g["item_uid"] for g in gold}
    sql_by_uid = {r["item_uid"]: r["gold_sql"] for r in gsql}
    mism = sum(1 for r in geval
               if r.get("gold_sql") != sql_by_uid.get(uid_by_id.get(r["item_id"])))
    check(mism == 0, f"gold_eval.gold_sql matches sql/gold_sql.jsonl ({mism} mismatch)")

    # --- database coverage ---------------------------------------------------
    gold_dbs = {g["db_id"] for g in gold}
    check(len(gold_dbs) == 30, f"gold spans 30 databases (got {len(gold_dbs)})")
    check(gold_dbs <= {m["db_id"] for m in manifest},
          "every gold db_id appears in dryad_manifest")
    check(gold_dbs <= {s["db_id"] for s in schema},
          "every gold db_id appears in schema_metadata")
    check(all(m.get("dryad_doi") and m.get("dryad_url") for m in manifest),
          "manifest carries dryad_doi + dryad_url for every record")
    check(all(s.get("tables") for s in schema),
          "schema_metadata: every record has at least one table")

    # --- optional artifacts --------------------------------------------------
    er = ROOT / "evaluation" / "eval_results.csv"
    if er.exists():
        with er.open(encoding="utf-8", newline="") as f:
            n = sum(1 for _ in csv.DictReader(f))
        check(n > 0, f"eval_results.csv is non-empty ({n} rows)")

    rc = ROOT / "ro-crate-metadata.json"
    if rc.exists():
        try:
            doc = json.loads(rc.read_text(encoding="utf-8"))
            ok = (isinstance(doc, dict) and isinstance(doc.get("@graph"), list)
                  and any(e.get("@id") == "ro-crate-metadata.json" for e in doc["@graph"]))
            check(ok, "ro-crate-metadata.json has @graph and a metadata descriptor")
        except json.JSONDecodeError as exc:
            check(False, f"ro-crate-metadata.json is valid JSON ({exc})")

    print(f"\n{_checks - len(_failures)}/{_checks} checks passed")
    if _failures:
        print(f"\n{len(_failures)} FAILURE(S):")
        for fl in _failures:
            print(f"  - {fl}")
        return 1
    print("ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
