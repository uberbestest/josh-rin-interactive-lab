"""Focused architecture-review regressions; no provider connections or credentials."""
import contextlib
import copy
import io
import json
from pathlib import Path
import socket
import tempfile
import unittest
from unittest.mock import patch

from common import digest
from ledger import Journal, verify_accounting
from test_runner import FakeProvider
import runner


class RepairTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.path = self.root / "ledger.sqlite3"
        self.journal = Journal(self.path)
        self.addCleanup(self.journal.close)
        self.plan = runner.load_plan(runner.HERE / "plan.json")
        for target in ("socket.socket.connect", "socket.socket.connect_ex", "socket.create_connection"):
            guard = patch(target, side_effect=AssertionError("No network permitted"))
            guard.start()
            self.addCleanup(guard.stop)

    def execute(self, mutate=None, plan=None, run_id="test-run"):
        plan = plan or self.plan
        provider = FakeProvider(plan, mutate=mutate)
        snapshot = runner.execute(plan, self.journal, "live", provider, run_id)
        return provider, snapshot

    def known_halt(self):
        def over_limit(response, _count):
            response["usage"]["output_tokens"] = self.plan["max_output_tokens"] + 1
            response["usage"]["total_tokens"] = response["usage"]["input_tokens"] + response["usage"]["output_tokens"]
        return self.execute(over_limit)

    def test_opaque_padding_counterexample_no_longer_changes_comparison(self):
        def pad(response, _count):
            response["output"][0]["encrypted_content"] = "x" * 6000
        provider, snapshot = self.execute(pad)
        self.assertEqual(len(provider.requests), 48)
        self.assertEqual(snapshot["run"]["summary"]["safe_joint_completions"], 8)
        self.assertTrue(snapshot["run"]["summary"]["successful"])
        for record in snapshot["requests"]:
            expected = "0.4096" if record["payload"]["model"] == "gpt-6-astra" else "0.32768"
            self.assertEqual(record["reserve_usd"], expected)
        self.assertEqual(snapshot["totals"]["estimated_total_cost_usd"], "0.0648")

    def test_calibration_padding_no_longer_causes_premature_refusal(self):
        plan = runner.load_plan(runner.HERE / "calibration.json")
        def pad(response, _count):
            response["output"][0]["encrypted_content"] = "x" * 10000
        provider, snapshot = self.execute(pad, plan)
        self.assertEqual(len(provider.requests), 6)
        self.assertEqual(snapshot["run"]["summary"]["safe_joint_completions"], 1)
        self.assertTrue(snapshot["run"]["summary"]["successful"])

    def test_real_token_growth_can_exhaust_case_without_blocking_later_cases(self):
        def larger_usage(response, count):
            if count == 1:
                response["usage"]["input_tokens"] = 12000
                response["usage"]["total_tokens"] = 12010
        provider, snapshot = self.execute(larger_usage)
        summary = snapshot["run"]["summary"]
        self.assertEqual(len(provider.requests), 43)
        self.assertEqual(summary["cases"][0]["reason"], "CASE_BUDGET_EXCEEDED")
        self.assertEqual(summary["safe_joint_completions"], 7)
        self.assertEqual(summary["blocked_contexts"], 0)
        self.assertEqual(snapshot["run"]["status"], "COMPLETED")
        self.assertEqual(snapshot["totals"]["unresolved_requests"], 0)

    def test_one_malformed_tool_call_does_not_censor_other_contexts(self):
        def malformed(response, count):
            if count == 1:
                response["output"][-1]["arguments"] = '{"action":"commit","job":"C"}'
        provider, snapshot = self.execute(malformed)
        summary = snapshot["run"]["summary"]
        self.assertEqual(len(provider.requests), 43)
        self.assertEqual(summary["cases"][0]["outcome"]["ticks"], 0)
        self.assertEqual(summary["cases"][0]["status"], "CASE_FAILED")
        self.assertEqual(summary["case_failures"], 1)
        self.assertEqual(summary["safe_joint_completions"], 7)
        self.assertFalse(summary["successful"])
        self.assertIsNone(snapshot["run"]["halt_reason"])

    def test_one_priced_truncation_does_not_censor_other_contexts(self):
        def truncate(response, count):
            if count == 1:
                response.update(status="incomplete", output=[], incomplete_details={"reason": "max_output_tokens"})
        provider, snapshot = self.execute(truncate)
        summary = snapshot["run"]["summary"]
        self.assertEqual(len(provider.requests), 43)
        self.assertEqual(summary["cases"][0]["reason"], "INCOMPLETE_RESPONSE")
        self.assertEqual(summary["cases"][0]["outcome"]["ticks"], 0)
        self.assertEqual(summary["safe_joint_completions"], 7)
        self.assertEqual(summary["blocked_contexts"], 0)
        self.assertEqual(snapshot["totals"]["unresolved_requests"], 0)

    def test_case_call_limit_is_local(self):
        self.plan["max_calls_per_case"] = 2
        provider, snapshot = self.execute()
        summary = snapshot["run"]["summary"]
        self.assertEqual(len(provider.requests), 16)
        self.assertTrue(all(row["status"] == "CALL_LIMIT" for row in summary["cases"]))
        self.assertEqual(summary["case_failures"], 8)
        self.assertEqual(summary["blocked_contexts"], 0)
        self.assertEqual(snapshot["run"]["status"], "COMPLETED")

    def test_case_budget_exhaustion_is_not_a_global_halt(self):
        self.plan["max_estimated_spend_per_case_usd"] = "0.001"
        provider, snapshot = self.execute()
        self.assertFalse(provider.requests)
        summary = snapshot["run"]["summary"]
        self.assertTrue(all(row["status"] == "CASE_FAILED" for row in summary["cases"]))
        self.assertFalse(any(row["model_response_observed"] for row in summary["cases"]))
        self.assertFalse(summary["successful"])
        self.assertEqual(summary["blocked_contexts"], 0)
        self.assertEqual(snapshot["run"]["status"], "COMPLETED")

    def test_provider_output_limit_violation_still_halts_globally(self):
        provider, snapshot = self.known_halt()
        self.assertEqual(len(provider.requests), 1)
        self.assertEqual(snapshot["run"]["status"], "HALTED")
        self.assertEqual(snapshot["run"]["summary"]["blocked_contexts"], 7)
        self.assertIsNotNone(snapshot["totals"]["estimated_total_cost_usd"])

    def test_review_retains_original_halt_costs_and_single_use_claim(self):
        _, before = self.known_halt()
        with self.assertRaises(RuntimeError):
            self.journal.start_run("unreviewed-next", "live", {**self.plan, "protocol_id": "next-protocol"}, {})
        receipt = self.journal.review_halt("test-run", digest(before), "Offline reviewer", "Inspected all priced requests")
        after = self.journal.snapshot("test-run")
        self.assertEqual(after["run"], before["run"])
        self.assertEqual(after["requests"], before["requests"])
        self.assertEqual(after["totals"], before["totals"])
        self.assertEqual(after["events"][:-1], before["events"])
        self.assertEqual(after["events"][-1], receipt)
        with self.assertRaises(RuntimeError):
            self.journal.start_run("same-protocol", "live", self.plan, {})
        with self.assertRaises(RuntimeError):
            self.journal.reserve("test-run", "case01", {}, "0.1")
        independent = Journal(self.path)
        try:
            independent.start_run("new-protocol", "live", {**self.plan, "protocol_id": "new-protocol"}, {})
        finally:
            independent.close()
        destination = self.root / "reviewed-evidence.json"
        runner.export_snapshot(after, destination)
        self.assertEqual(runner.verify_export(destination)["verified_requests"], 1)

    def test_review_cannot_release_unknown_costs(self):
        def unknown(response, _count):
            response.pop("usage")
        provider, snapshot = self.execute(unknown)
        with self.assertRaisesRegex(RuntimeError, "fully accounted"):
            self.journal.review_halt("test-run", digest(snapshot), "Offline reviewer", "Cannot reconcile")
        self.assertEqual(self.journal.snapshot("test-run"), snapshot)
        self.assertEqual(len(provider.requests), 1)
        self.assertGreater(float(snapshot["totals"]["unresolved_reserve_usd"]), 0)

    def test_stale_duplicate_and_empty_reviews_are_rejected_without_mutation(self):
        _, snapshot = self.known_halt()
        for snapshot_hash, reviewer, note in (("0" * 64, "Josh", "Reviewed"),
                                               (digest(snapshot), " ", "Reviewed"),
                                               (digest(snapshot), "Josh", " ")):
            with self.assertRaises(ValueError):
                self.journal.review_halt("test-run", snapshot_hash, reviewer, note)
            self.assertEqual(self.journal.snapshot("test-run"), snapshot)
        self.journal.review_halt("test-run", digest(snapshot), "Josh", "Reviewed all charges")
        reviewed = self.journal.snapshot("test-run")
        with self.assertRaises(RuntimeError):
            self.journal.review_halt("test-run", digest(reviewed), "Josh", "Duplicate")

    def test_review_of_running_or_successful_run_is_rejected(self):
        self.journal.start_run("pending", "live", self.plan, {})
        snapshot = self.journal.snapshot("pending")
        with self.assertRaises(RuntimeError):
            self.journal.review_halt("pending", digest(snapshot), "Josh", "Not finished")
        self.journal.finish("pending", {})
        snapshot = self.journal.snapshot("pending")
        with self.assertRaises(RuntimeError):
            self.journal.review_halt("pending", digest(snapshot), "Josh", "Already completed")

    def test_review_recomputes_prices_before_releasing_the_halt(self):
        _, before = self.known_halt()
        forged = copy.deepcopy(before)
        settlement = next(e for e in forged["events"] if e["kind"] == "request_settled")
        settlement["data"]["calculation"]["estimated_cost_usd"] = "0"
        with patch.object(self.journal, "_current", return_value=forged):
            with self.assertRaisesRegex(ValueError, "Recomputed price"):
                self.journal.review_halt("test-run", digest(forged), "Josh", "Incorrect price")
        self.assertEqual(self.journal.snapshot("test-run"), before)

    def test_failed_review_transaction_cannot_unblock_execution(self):
        _, before = self.known_halt()
        original = self.journal._append
        def fail_before_commit(*args, **kwargs):
            original(*args, **kwargs)
            raise OSError("simulated failed review transaction")
        with patch.object(self.journal, "_append", side_effect=fail_before_commit):
            with self.assertRaises(OSError):
                self.journal.review_halt("test-run", digest(before), "Josh", "Reviewed")
        self.assertEqual(self.journal.snapshot("test-run"), before)
        with self.assertRaises(RuntimeError):
            self.journal.start_run("next-run", "live", {**self.plan, "protocol_id": "next-protocol"}, {})

    def test_review_receipt_tampering_is_detected_even_with_new_event_hash(self):
        _, snapshot = self.known_halt()
        self.journal.review_halt("test-run", digest(snapshot), "Josh", "Reviewed charges")
        changed = self.journal.snapshot("test-run")
        changed["events"][-1]["data"]["reviewed_snapshot_sha256"] = "0" * 64
        event = changed["events"][-1]
        event["event_hash"] = digest({k: v for k, v in event.items() if k != "event_hash"})
        with self.assertRaises(RuntimeError):
            verify_accounting(changed)

    def cli_run(self, mutate=None):
        source = runner.HERE
        bundle = runner.source_bundle()
        provider = FakeProvider(self.plan, mutate=mutate)
        output = io.StringIO()
        with patch.object(runner, "HERE", self.root), patch.object(runner, "source_bundle", return_value=bundle), \
             patch.object(runner, "live_database", return_value=self.path), \
             patch.object(runner, "credentials", return_value=("offline-placeholder", "org-offline", "proj-offline")), \
             patch.object(runner, "Transport", return_value=provider), contextlib.redirect_stdout(output):
            code = runner.main(["live", "--plan", str(source / "plan.json"), "--approve-plan", digest(self.plan)])
        return code, json.loads(output.getvalue()), provider

    def test_cli_success_returns_zero(self):
        code, output, provider = self.cli_run()
        self.assertEqual(code, 0)
        self.assertTrue(output["successful"])
        self.assertEqual(len(provider.requests), 48)

    def test_cli_known_case_failure_returns_nonzero_without_global_halt(self):
        def truncate(response, count):
            if count == 1:
                response.update(status="incomplete", output=[])
        code, output, _ = self.cli_run(truncate)
        self.assertEqual(code, 2)
        self.assertFalse(output["successful"])
        self.assertEqual(output["status"], "COMPLETED")
        self.assertEqual(output["case_failures"], 1)
        self.assertEqual(output["blocked_contexts"], 0)

    def test_cli_uncertain_global_halt_returns_nonzero(self):
        def unknown(response, _count):
            response.pop("usage")
        code, output, provider = self.cli_run(unknown)
        self.assertEqual(code, 2)
        self.assertFalse(output["successful"])
        self.assertEqual(output["status"], "HALTED")
        self.assertIsNone(output["provider_cost_usd"])
        self.assertEqual(len(provider.requests), 1)

    def test_cli_report_and_review_need_no_credentials_or_transport(self):
        _, before = self.known_halt()
        output = io.StringIO()
        with patch.object(runner, "live_database", return_value=self.path), \
             patch.object(runner, "credentials", side_effect=AssertionError("No credential access")), \
             patch.object(runner, "Transport", side_effect=AssertionError("No transport")), \
             contextlib.redirect_stdout(output):
            self.assertEqual(runner.main(["report", "--run-id", "test-run"]), 0)
            report = json.loads(output.getvalue())
            self.assertEqual(report["snapshot_sha256"], digest(before))
            output.seek(0)
            output.truncate()
            self.assertEqual(runner.main(["review-halt", "test-run", "--snapshot-sha256", report["snapshot_sha256"],
                                          "--reviewer", "Josh", "--note", "Reviewed retained prices and stop reason"]), 0)
        self.assertEqual(self.journal.snapshot("test-run")["run"]["status"], "HALTED")


if __name__ == "__main__":
    unittest.main()
