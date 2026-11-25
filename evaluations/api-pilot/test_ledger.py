"""Offline accounting tests, including real process death and competing starts.

These exercise SQLite commits/recovery and application invariants. They do not
simulate storage-device failures or claim to test physical power-loss durability.
"""
from copy import deepcopy
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest

from ledger import Journal, verify_accounting


HERE = Path(__file__).resolve().parent
PLAN = {
    "protocol_id": "test-protocol", "max_estimated_spend_usd": "1.00",
    "max_estimated_spend_per_case_usd": "0.60", "max_calls_per_case": 3,
    "assignments": [{"case_id": "case-1", "case": {}, "model": "mock"},
                    {"case_id": "case-2", "case": {}, "model": "mock"}],
}
ENVELOPE = {"http_status": 200, "headers": {"x-request-id": "mock-1"},
            "body_base64": "e30=", "started_utc": "start", "ended_utc": "end",
            "elapsed_seconds": 0.01, "error_type": None, "body_complete": True}


class LedgerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="ledger-test-", dir=HERE)
        self.directory = Path(self.temporary.name)
        self.path = self.directory / "journal.sqlite3"
        self.journal = Journal(self.path)
        self.journal.start_run("run-1", "live", deepcopy(PLAN), {"project_id": "project-test"})

    def tearDown(self):
        self.journal.close()
        self.temporary.cleanup()

    def reserve(self, case="case-1", amount="0.30"):
        return self.journal.reserve("run-1", case, {"input": "test", "model": "mock"}, amount)

    def settle(self, request_id, cost="0.20"):
        self.journal.save_response(request_id, deepcopy(ENVELOPE))
        self.journal.settle(request_id, {"estimated_cost_usd": cost, "usage": {"output_tokens": 1}})

    def child(self, code, *arguments, cwd=None, stdin=None):
        environment = os.environ.copy()
        environment["PYTHONPATH"] = str(HERE)
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        return subprocess.Popen([sys.executable, "-c", code, str(self.path), *arguments],
                                cwd=cwd or HERE, env=environment, stdin=stdin,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    def test_reserve_is_unknown_and_blocks_next_request(self):
        request_id = self.reserve()
        snapshot = self.journal.snapshot("run-1")
        self.assertEqual(snapshot["requests"][0]["id"], request_id)
        self.assertEqual(snapshot["totals"], {
            "known_estimated_spend_usd": "0", "estimated_total_cost_usd": None,
            "unresolved_reserve_usd": "0.30", "estimated_exposure_usd": "0.30",
            "unresolved_requests": 1, "attempted_requests": 1})
        with self.assertRaisesRegex(RuntimeError, "unresolved"):
            self.reserve("case-2")
        self.assertEqual(self.journal.snapshot("run-1"), snapshot)

    def test_raw_response_survives_missing_usage_and_finish_halts(self):
        request_id = self.reserve()
        self.journal.save_response(request_id, deepcopy(ENVELOPE))
        with self.assertRaisesRegex(ValueError, "estimated_cost_usd"):
            self.journal.settle(request_id, {"usage": None})
        self.journal.finish("run-1", {"outcome": "missing usage"})
        snapshot = self.journal.snapshot("run-1")
        self.assertEqual(snapshot["requests"][0]["response"], ENVELOPE)
        self.assertIsNone(snapshot["requests"][0]["cost_usd"])
        self.assertEqual(snapshot["run"]["status"], "HALTED")
        self.assertEqual(snapshot["totals"]["unresolved_reserve_usd"], "0.30")
        self.assertTrue(self.journal.verify("run-1")["verified"])

    def test_settlement_requires_response_and_is_single_use(self):
        request_id = self.reserve()
        with self.assertRaisesRegex(RuntimeError, "Capture the response"):
            self.journal.settle(request_id, {"estimated_cost_usd": "0.10"})
        self.settle(request_id)
        with self.assertRaises(RuntimeError):
            self.journal.settle(request_id, {"estimated_cost_usd": "0.10"})
        with self.assertRaises(RuntimeError):
            self.journal.save_response(request_id, ENVELOPE)
        self.assertEqual(self.journal.snapshot("run-1")["totals"]["estimated_total_cost_usd"], "0.20")

    def test_case_and_total_bounds_are_separate(self):
        self.settle(self.reserve(amount="0.60"), "0.50")
        with self.assertRaisesRegex(RuntimeError, "Case spending"):
            self.reserve(amount="0.11")
        self.settle(self.reserve("case-2", "0.50"), "0.50")
        with self.assertRaisesRegex(RuntimeError, "Run spending"):
            self.reserve(amount="0.01")
        self.assertEqual(self.journal.snapshot("run-1")["totals"]["attempted_requests"], 2)

    def test_call_ceiling_and_unknown_case(self):
        for _ in range(3):
            self.settle(self.reserve(amount="0.02"), "0.01")
        with self.assertRaisesRegex(RuntimeError, "request ceiling"):
            self.reserve(amount="0.02")
        with self.assertRaisesRegex(ValueError, "frozen assignment"):
            self.reserve("unknown", "0.02")

    def test_overrun_is_recorded_and_halts(self):
        self.settle(self.reserve(amount="0.10"), "0.20")
        snapshot = self.journal.snapshot("run-1")
        self.assertEqual(snapshot["run"]["status"], "HALTED")
        self.assertEqual(snapshot["totals"]["estimated_total_cost_usd"], "0.20")
        with self.assertRaisesRegex(RuntimeError, "not active"):
            self.reserve("case-2")
        self.journal.finish("run-1", {"outcome": "halted"})
        self.assertEqual(self.journal.snapshot("run-1")["run"]["status"], "HALTED")

    def test_protocol_claim_survives_completed_run(self):
        self.journal.finish("run-1", {"outcome": "no requests"})
        with self.assertRaisesRegex(RuntimeError, "already been claimed"):
            self.journal.start_run("run-2", "live", PLAN, {})
        changed = {**PLAN, "protocol_id": "different-protocol"}
        self.journal.start_run("run-2", "live", changed, {})
        self.journal.start_run("fixture-1", "fixture", PLAN, {})
        self.journal.start_run("fixture-2", "fixture", PLAN, {})

    def test_any_unfinished_live_run_blocks_new_protocol(self):
        changed = {**PLAN, "protocol_id": "different-protocol"}
        with self.assertRaisesRegex(RuntimeError, "previous live run"):
            self.journal.start_run("run-2", "live", changed, {})
        self.journal.halt("run-1", "uncertain result")
        self.journal.finish("run-1", {})
        with self.assertRaisesRegex(RuntimeError, "previous live run"):
            self.journal.start_run("run-2", "live", changed, {})

    def test_reject_credentials_and_nonpositive_live_reserve(self):
        with self.assertRaisesRegex(ValueError, "Credentials"):
            self.journal.add_event("run-1", "diagnostic", {"headers": {"Authorization": "redacted"}})
        with self.assertRaisesRegex(ValueError, "positive reserve"):
            self.reserve(amount="0")
        for amount in ("-1", "NaN", "Infinity", True):
            with self.assertRaises(ValueError):
                self.reserve(amount=amount)

    def test_mutable_row_tampering_is_detected(self):
        request_id = self.reserve()
        self.settle(request_id)
        self.journal.db.execute("UPDATE requests SET cost_usd='0' WHERE id=?", (request_id,))
        with self.assertRaisesRegex(RuntimeError, "immutable events"):
            self.journal.verify("run-1")
        with self.assertRaises(RuntimeError):
            self.reserve("case-2")

    def test_protocol_row_tampering_is_detected_before_relaunch(self):
        self.journal.db.execute("UPDATE runs SET protocol_id='tampered' WHERE id='run-1'")
        with self.assertRaisesRegex(RuntimeError, "Protocol claim"):
            self.journal.start_run("run-2", "live", PLAN, {})

    def test_event_chain_is_immutable_and_reserved_kinds_rejected(self):
        self.journal.add_event("run-1", "assignment_started", {"case_id": "case-1"})
        with self.assertRaises(sqlite3.IntegrityError):
            self.journal.db.execute("DELETE FROM events")
        with self.assertRaises(sqlite3.IntegrityError):
            self.journal.db.execute("UPDATE events SET event_hash='fake'")
        with self.assertRaises(ValueError):
            self.journal.add_event("run-1", "request_reserved", {})

    def test_unknown_schema_is_rejected_and_read_only_blocks_writes(self):
        readonly = Journal(self.path, read_only=True)
        try:
            self.assertTrue(readonly.verify("run-1")["verified"])
            with self.assertRaisesRegex(RuntimeError, "read-only"):
                readonly.halt("run-1", "test")
        finally:
            readonly.close()
        self.journal.db.execute("PRAGMA user_version=99")
        with self.assertRaisesRegex(RuntimeError, "schema"):
            Journal(self.path)

    def test_export_verification_requires_matching_chain_and_rows(self):
        self.settle(self.reserve())
        snapshot = self.journal.snapshot("run-1")
        self.assertTrue(verify_accounting(snapshot)["verified"])
        changed = deepcopy(snapshot)
        changed["events"][1]["data"]["reserve_usd"] = "0.01"
        with self.assertRaisesRegex(RuntimeError, "chain"):
            verify_accounting(changed)
        changed = deepcopy(snapshot)
        changed["totals"]["estimated_total_cost_usd"] = "0"
        with self.assertRaisesRegex(RuntimeError, "totals"):
            verify_accounting(changed)
        with self.assertRaisesRegex(RuntimeError, "Malformed"):
            verify_accounting({})

    def test_unrelated_database_is_not_changed_to_wal(self):
        unrelated = self.directory / "unrelated.sqlite3"
        database = sqlite3.connect(unrelated)
        database.execute("CREATE TABLE other(value TEXT)")
        database.commit()
        database.close()
        with self.assertRaisesRegex(RuntimeError, "schema"):
            Journal(unrelated)
        database = sqlite3.connect(unrelated)
        try:
            self.assertEqual(database.execute("PRAGMA journal_mode").fetchone()[0], "delete")
        finally:
            database.close()

    def test_process_death_preserves_reserve_and_blocks_other_checkout(self):
        # First finish the setup run so the subprocess can claim another protocol.
        self.journal.finish("run-1", {})
        code = """
import json, os, sys
from ledger import Journal
j = Journal(sys.argv[1])
p = json.loads(sys.argv[2])
j.start_run('crashed', 'live', p, {})
j.reserve('crashed', 'case-1', {'input': 'test'}, '0.40')
os._exit(19)
"""
        plan = {**PLAN, "protocol_id": "crash-protocol"}
        child = self.child(code, json.dumps(plan))
        output, errors = child.communicate(timeout=15)
        self.assertEqual(child.returncode, 19, output + errors)
        snapshot = self.journal.snapshot("crashed")
        self.assertIsNone(snapshot["totals"]["estimated_total_cost_usd"])
        self.assertEqual(snapshot["totals"]["unresolved_reserve_usd"], "0.40")
        checkout = self.directory / "other-checkout"
        checkout.mkdir()
        code = """
import json, sys
from ledger import Journal
j = Journal(sys.argv[1])
try:
    j.start_run('retry', 'live', json.loads(sys.argv[2]), {})
except RuntimeError as error:
    print(error)
    sys.exit(7)
sys.exit(0)
"""
        retry = self.child(code, json.dumps(plan), cwd=checkout)
        output, errors = retry.communicate(timeout=15)
        self.assertEqual(retry.returncode, 7, output + errors)
        self.assertIn("already been claimed", output)

    def test_process_death_after_response_keeps_unpriced_body(self):
        request_id = self.reserve()
        code = """
import json, os, sys
from ledger import Journal
j = Journal(sys.argv[1])
j.save_response(sys.argv[2], json.loads(sys.argv[3]))
os._exit(20)
"""
        child = self.child(code, request_id, json.dumps(ENVELOPE))
        output, errors = child.communicate(timeout=15)
        self.assertEqual(child.returncode, 20, output + errors)
        snapshot = self.journal.snapshot("run-1")
        self.assertEqual(snapshot["requests"][0]["response"], ENVELOPE)
        self.assertIsNone(snapshot["totals"]["estimated_total_cost_usd"])

    def test_competing_processes_cannot_claim_protocol_twice(self):
        self.journal.finish("run-1", {})
        plan = {**PLAN, "protocol_id": "race-protocol"}
        code = """
import json, sys
from ledger import Journal
j = Journal(sys.argv[1])
print('READY', flush=True)
input()
try:
    j.start_run(sys.argv[3], 'live', json.loads(sys.argv[2]), {})
except RuntimeError:
    sys.exit(7)
sys.exit(0)
"""
        children = [self.child(code, json.dumps(plan), f"racer-{n}", stdin=subprocess.PIPE) for n in range(2)]
        try:
            for child in children:
                self.assertEqual(child.stdout.readline().strip(), "READY")
            for child in children:
                child.stdin.write("GO\n")
                child.stdin.flush()
            results = []
            for child in children:
                output, errors = child.communicate(timeout=15)
                results.append(child.returncode)
                self.assertIn(child.returncode, {0, 7}, output + errors)
            self.assertEqual(sorted(results), [0, 7])
        finally:
            for child in children:
                if child.poll() is None:
                    child.kill()
                    child.communicate()


if __name__ == "__main__":
    unittest.main()
