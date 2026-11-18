#!/usr/bin/env python3
"""Freeze the prospective instrument exactly once, before participant events."""
from __future__ import annotations
import datetime
import hashlib
import json
from pathlib import Path
import unittest
import io
import audit_oracle

ROOT = Path(__file__).resolve().parent


def main():
    target = ROOT / "protocol/frozen.json"
    if target.exists():
        raise SystemExit("Freeze already exists; do not replace a prospective record")
    if any(path.stat().st_size for path in (ROOT / "runs").glob("*/events.jsonl")):
        raise SystemExit("Participant events already exist; a pre-run freeze cannot now be created")
    audit = audit_oracle.audit()
    assert audit["status"] == "PASS" and audit["states_checked"] == 216
    suite = unittest.defaultTestLoader.discover(str(ROOT), pattern="test_*.py")
    result = unittest.TextTestRunner(stream=io.StringIO()).run(suite)
    assert result.wasSuccessful(), "Semantic test failure"
    sources = list(ROOT.glob("*.py")) + list((ROOT / "protocol").glob("*"))
    sources += list((ROOT / "runs").glob("*/initial_state.json")) + list((ROOT / "runs").glob("*/prompt.txt"))
    sources += list((ROOT / "runs").glob("*/dispatch_message.txt"))
    source_hashes = {path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
                     for path in sorted(sources) if path.is_file()}
    value = {"record": "JRR-CONSUMABLE-CHECKS-2026-11-18-004", "status": "frozen_before_native_participants",
             "frozen_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
             "display_timezone": "America/New_York", "cases": 20, "assigned_native_contexts": 40,
             "requested_selectors": ["gpt-6-astra", "gpt-6.2-astra"],
             "reasoning_effort": "inherited from parent; not independently attested",
             "semantic_tests_passed": result.testsRun, "separate_analytic_states_passed": audit["states_passed"],
             "source_hashes": source_hashes,
             "limits": "Same-lab pre-run record; instruction-scoped access; no external backend or timestamp attestation."}
    target.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": value["status"], "frozen_at_utc": value["frozen_at_utc"],
                      "freeze_sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
                      "frozen_files": len(source_hashes), "semantic_tests": result.testsRun,
                      "analytic_states": audit["states_passed"]}))


if __name__ == "__main__":
    main()
