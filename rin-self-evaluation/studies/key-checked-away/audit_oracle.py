#!/usr/bin/env python3
"""Check initial belief-policy feasibility against a separate closed-form result.

This auditor does not enumerate policies or inspect the selected hidden world.
It compares engine.can_guarantee with necessary and sufficient thresholds
derived from the public task. It launches no participant and changes no run.

Known active authorization, unknown prior write, readiness in {1, 3}:
  A guarantee must handle the absent, late-receipt branch. One receipt must
  complete at or after tick 3, then commit and finalize require two more ticks.
  Waiting one tick, querying, committing and finalizing attains tick 5 exactly.
  The same worst branch costs one query plus two writes: budget >= 2 + c.

Unknown stable authorization in {active, revoked}, otherwise same belief:
  The active, absent branch needs both an authorization query and a receipt.
  Each query takes two ticks, and the two writes take one tick each. Querying
  authorization first makes the receipt finish at tick 4, covering either
  possible readiness. This attains tick 6, with budget >= 2 + 2*c. Revocation
  can instead be certified by the first authorization response. The active
  branch prevents blocked reporting from trivially satisfying the guarantee.

The action cap is fixed at 24 and is not binding for these witness policies.
The grid is 2 authorization conditions * 2 query costs * 6 budgets * 9
deadlines = exactly 216 separately checked initial states.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from pathlib import Path

from engine import can_guarantee, make_initial_state

ROOT = Path(__file__).resolve().parent
EXPECTED_CHECKS = 216


def audit() -> dict:
    checks = []
    for authorization_unknown in (False, True):
        authorities = ("active", "revoked") if authorization_unknown else ("active",)
        possible_worlds = [
            {"prior_delivered": prior, "receipt_ready": ready, "authority": authority}
            for prior, ready, authority in itertools.product((0, 1), (1, 3), authorities)
        ]
        # The planner receives the entire public belief set. This representative
        # actual fixture only initializes the service and does not set expected.
        actual_world = {"prior_delivered": 0, "receipt_ready": 1, "authority": "active"}
        for query_cost, budget, deadline in itertools.product((0, 1), range(6), range(9)):
            minimum_uses = 2 + query_cost * (2 if authorization_unknown else 1)
            minimum_deadline = 6 if authorization_unknown else 5
            expected = budget >= minimum_uses and deadline >= minimum_deadline
            state = make_initial_state(
                {"uses_remaining": budget, "deadline": deadline, "query_cost": query_cost,
                 "authorization_known": not authorization_unknown, "max_actions": 24},
                actual_world,
                possible_worlds,
            )
            observed = can_guarantee(state)
            checks.append(
                {"authorization_unknown": authorization_unknown, "query_cost": query_cost,
                 "budget": budget, "deadline": deadline,
                 "closed_form_minimum_uses": minimum_uses,
                 "closed_form_minimum_deadline": minimum_deadline,
                 "expected_guarantee": expected, "engine_guarantee": observed,
                 "pass": observed == expected}
            )
    assert len(checks) == EXPECTED_CHECKS
    failures = [row for row in checks if not row["pass"]]
    return {
        "format_version": 1,
        "status": "FAIL" if failures else "PASS",
        "kind": "separate_closed_form_initial_belief_oracle_audit",
        "scope": "Same-lab source verification; no live participant trials or external replication.",
        "engine_sha256": hashlib.sha256((ROOT / "engine.py").read_bytes()).hexdigest(),
        "states_checked": len(checks),
        "states_passed": len(checks) - len(failures),
        "states_failed": len(failures),
        "known_authority_threshold": {"minimum_uses": "2 + query_cost", "minimum_deadline": 5},
        "unknown_authority_threshold": {"minimum_uses": "2 + 2 * query_cost", "minimum_deadline": 6},
        "failures": failures,
        "checks": checks,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Optional JSON receipt outside the study directory.")
    args = parser.parse_args()
    if args.output is not None and args.output.resolve().is_relative_to(ROOT):
        parser.error("--output must be outside the study directory; the auditor does not modify experiment data")
    result = audit()
    rendered = json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    if result["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
