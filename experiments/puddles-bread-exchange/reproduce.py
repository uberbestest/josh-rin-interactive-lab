"""Reproduce all finite results using Python's standard library.

Usage: python reproduce.py --output reproduced
No network, third-party packages, secrets, or model APIs are used.
"""
from __future__ import annotations
import argparse
import csv
import gzip
import hashlib
import io
import json
from pathlib import Path
from engine import RULES, cells, histories, predict, decide, summarize

HERE = Path(__file__).resolve().parent
FIELDS = ["cell", "truth", "shared_fault", "local_errors", "root_bits", "weight", *["p_"+r for r in RULES], *["action_"+r for r in RULES]]

def run(output: Path) -> dict:
    protocol = HERE / "protocol.json"
    freeze = json.loads((HERE / "protocol-freeze.json").read_text())
    sha = hashlib.sha256(protocol.read_bytes()).hexdigest()
    if sha != freeze["protocol_sha256"]:
        raise RuntimeError("Frozen protocol fingerprint mismatch")
    output.mkdir(parents=True, exist_ok=True)
    summaries = []
    total = 0
    with (output / "histories.csv.gz").open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as gz:
            with io.TextIOWrapper(gz, encoding="utf-8", newline="") as text:
                writer = csv.DictWriter(text, fieldnames=FIELDS, lineterminator="\n")
                writer.writeheader()
                for cell in cells():
                    rows = list(histories(cell))
                    pred_cache = {}
                    for row in rows:
                        bits = row["bits"]
                        if bits not in pred_cache:
                            pred_cache[bits] = predict(bits, cell.copies, cell.marginal, cell.shared)
                        ps = pred_cache[bits]
                        writer.writerow({"cell": cell.id, "truth": row["truth"], "shared_fault": row["shared_fault"],
                            "local_errors": "".join(map(str,row["local_errors"])), "root_bits": "".join(map(str,bits)),
                            "weight": str(row["weight"]), **{"p_"+r:str(ps[r]) for r in RULES},
                            **{"action_"+r:decide(ps[r]) for r in RULES}})
                    summaries.append(summarize(cell, rows))
                    total += len(rows)
    result = {"id": "PUDDLES-BREAD-EXCHANGE-2026-11-04-001", "version": "0.1.0",
        "evidence_status": "EXECUTED_EXACT_SYNTHETIC_ENUMERATION_SAME_AUTHOR_CHECKS",
        "external_model_runs": 0, "independent_review": False,
        "protocol_sha256": sha, "cell_count": len(summaries), "history_count": total,
        "rule_evaluations": total*len(RULES), "weighting": "Exact rational probability mass, not uniform history counts.",
        "cells": summaries}
    (output / "results.json").write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    (output / "results-data.js").write_text("window.BREAD_RESULTS = "+json.dumps(result,separators=(",",":"))+";\n",encoding="utf-8")
    print(json.dumps({"cells":len(summaries),"histories":total,"rule_evaluations":total*len(RULES),"output":str(output)}, indent=2))
    return result

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=HERE / "reproduced")
    args = parser.parse_args()
    run(args.output)
