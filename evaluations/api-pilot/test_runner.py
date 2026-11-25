"""Offline integration tests. The provider is scripted and all sockets are blocked."""
import base64
import copy
from decimal import Decimal
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from common import canonical, now
from ledger import Journal
from protocol import Fixture, initial_history
import runner


HERE = Path(__file__).resolve().parent


def envelope(response):
    return {"http_status": 200, "headers": {"x-request-id": "mock-request"},
            "body_base64": base64.b64encode(canonical(response).encode("utf-8")).decode("ascii"),
            "started_utc": now(), "ended_utc": now(), "elapsed_seconds": 0.001,
            "error_type": None, "body_complete": True}


class FakeProvider:
    organization = "org-offline-test"
    project = "proj-offline-test"

    def __init__(self, plan, mutate=None, override=None, observe=None):
        self.plan, self.mutate, self.override, self.observe = plan, mutate, override, observe
        self.requests, self.responses = [], []
        self.assignment = -1

    def send(self, payload):
        self.requests.append(copy.deepcopy(payload))
        if self.observe:
            self.observe(payload)
        if len(payload["input"]) == 1:
            self.assignment += 1
            self.fixture = Fixture(self.plan["assignments"][self.assignment]["case"])
        response = self.fixture.create(payload)
        response.update(id=f"mock-{self.assignment}-{self.fixture.sequence}",
                        model=payload["model"], service_tier="default", usage={
                            "input_tokens": 100, "output_tokens": 10, "total_tokens": 110,
                            "input_tokens_details": {"cached_tokens": 0, "cache_write_tokens": 0},
                            "output_tokens_details": {"reasoning_tokens": 4}})
        response["output"].insert(0, {"type": "reasoning", "id": "rs-" + response["id"],
            "summary": [{"type": "summary_text", "text": "café 🦆"}],
            "encrypted_content": "opaque-" + response["id"]})
        if self.mutate:
            self.mutate(response, len(self.requests))
        self.responses.append(copy.deepcopy(response))
        evidence = envelope(response)
        if self.override:
            self.override(evidence, len(self.requests))
        return evidence


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.plan = runner.load_plan(HERE / "plan.json")
        self.journal = Journal(self.root / "ledger.sqlite3")
        self.addCleanup(self.journal.close)
        for target in ("socket.socket.connect", "socket.socket.connect_ex", "socket.create_connection"):
            guard = patch(target, side_effect=AssertionError("Network is forbidden in offline integration tests"))
            guard.start()
            self.addCleanup(guard.stop)

    def run_fake(self, **kwargs):
        provider = FakeProvider(self.plan, **kwargs)
        snapshot = runner.execute(self.plan, self.journal, "live", provider, "mock-run")
        return provider, snapshot

    def assert_one_uncertain_attempt(self, provider, snapshot, reason):
        summary = snapshot["run"]["summary"]
        self.assertEqual(len(provider.requests), 1)
        self.assertEqual(snapshot["totals"]["attempted_requests"], 1)
        self.assertEqual(snapshot["totals"]["unresolved_requests"], 1)
        self.assertIsNone(snapshot["totals"]["estimated_total_cost_usd"])
        self.assertGreater(Decimal(snapshot["totals"]["unresolved_reserve_usd"]), 0)
        self.assertIsNone(summary["provider_cost_usd"])
        self.assertEqual(summary["assigned_contexts"], 8)
        self.assertEqual(summary["cases"][0]["reason"], reason)
        self.assertEqual([row["status"] for row in summary["cases"]], ["HALTED"] + ["BLOCKED"] * 7)
        self.assertFalse(any(event["kind"] == "tool_action" for event in snapshot["events"]))

    def test_fixture_all_assignments_and_no_provider_evidence(self):
        snapshot = runner.execute(self.plan, self.journal, run_id="fixture-run")
        summary = snapshot["run"]["summary"]
        self.assertEqual(summary["assigned_contexts"], 8)
        self.assertEqual(summary["safe_joint_completions"], 8)
        self.assertEqual(summary["model_contexts_observed"], 0)
        self.assertIsNone(summary["provider_cost_usd"])
        self.assertEqual(snapshot["requests"], [])
        self.assertTrue(all(row["calls"] == 6 for row in summary["cases"]))

    def test_full_matrix_retains_reasoning_and_reserves_before_dispatch(self):
        observed = []
        def inspect_committed_reserve(payload):
            independent = Journal(self.journal.path, read_only=True)
            try:
                saved = independent.snapshot("mock-run")
                last = saved["requests"][-1]
                observed.append(last["state"] == "RESERVED" and last["cost_usd"] is None
                                and last["payload"] == payload)
            finally:
                independent.close()
        provider, snapshot = self.run_fake(observe=inspect_committed_reserve)
        summary = snapshot["run"]["summary"]
        self.assertEqual(len(provider.requests), 48)
        self.assertEqual(observed, [True] * 48)
        self.assertEqual(summary["safe_joint_completions"], 8)
        self.assertEqual(summary["model_contexts_observed"], 8)
        self.assertEqual(snapshot["totals"]["unresolved_requests"], 0)
        self.assertEqual(snapshot["totals"]["attempted_requests"], 48)
        self.assertGreater(Decimal(summary["provider_cost_usd"]), 0)
        second_history = provider.requests[1]["input"]
        self.assertEqual(second_history[:-1], initial_history() + provider.responses[0]["output"])
        self.assertEqual(second_history[-1]["type"], "function_call_output")
        self.assertEqual(second_history[1]["encrypted_content"], "opaque-mock-0-1")
        self.assertTrue(all(payload["store"] is False and payload["service_tier"] == "default"
                            for payload in provider.requests))
        evidence = self.root / "café 🦆" / "evidence.json"
        runner.export_snapshot(snapshot, evidence)
        self.assertIn("café 🦆".encode("utf-8"), evidence.read_bytes())
        verified = runner.verify_export(evidence)
        self.assertEqual(verified["verified_assignments"], 8)
        artifact = json.loads(evidence.read_text(encoding="utf-8"))
        self.assertEqual(artifact["snapshot"], snapshot)

    def test_missing_usage_keeps_returned_response_and_stops(self):
        def missing(response, _count):
            response.pop("usage")
        provider, snapshot = self.run_fake(mutate=missing)
        self.assert_one_uncertain_attempt(provider, snapshot, "UNPRICEABLE_USAGE")
        raw = base64.b64decode(snapshot["requests"][0]["response"]["body_base64"])
        self.assertEqual(json.loads(raw), provider.responses[0])
        self.assertEqual(snapshot["run"]["summary"]["cases"][0]["responses"], 1)

    def test_empty_json_object_is_not_a_model_participant(self):
        def empty(evidence, _count):
            evidence["body_base64"] = base64.b64encode(b"{}").decode("ascii")
        provider, snapshot = self.run_fake(override=empty)
        self.assert_one_uncertain_attempt(provider, snapshot, "INVALID_JSON")
        self.assertEqual(snapshot["run"]["summary"]["model_contexts_observed"], 0)

    def test_empty_truncated_output_keeps_known_charge(self):
        def empty_truncation(response, _count):
            response["output"] = []
            response["status"] = "incomplete"
        provider, snapshot = self.run_fake(mutate=empty_truncation)
        self.assertEqual(len(provider.requests), 8)
        self.assertEqual(snapshot["totals"]["unresolved_requests"], 0)
        self.assertGreater(Decimal(snapshot["totals"]["estimated_total_cost_usd"]), 0)
        self.assertEqual(snapshot["run"]["summary"]["cases"][0]["reason"], "INCOMPLETE_RESPONSE")

    def test_reported_output_over_requested_limit_is_priced_then_halted(self):
        def over_limit(response, _count):
            response["usage"]["output_tokens"] = self.plan["max_output_tokens"] + 1
            response["usage"]["total_tokens"] = 100 + response["usage"]["output_tokens"]
        provider, snapshot = self.run_fake(mutate=over_limit)
        self.assertEqual(len(provider.requests), 1)
        self.assertEqual(snapshot["totals"]["unresolved_requests"], 0)
        self.assertEqual(snapshot["run"]["summary"]["cases"][0]["reason"], "OUTPUT_LIMIT_EXCEEDED")
        self.assertFalse(any(event["kind"] == "tool_action" for event in snapshot["events"]))

    def test_unexpected_audio_content_is_not_priced_as_text(self):
        def audio_output(response, _count):
            response["output"] = [{"type": "message", "content": [{"type": "output_audio", "audio": "data"}]}]
        provider, snapshot = self.run_fake(mutate=audio_output)
        self.assert_one_uncertain_attempt(provider, snapshot, "INVALID_OUTPUT")

    def test_unknown_second_charge_retains_the_first_settled_charge(self):
        def missing_second(response, count):
            if count == 2:
                response.pop("usage")
        provider, snapshot = self.run_fake(mutate=missing_second)
        self.assertEqual(len(provider.requests), 2)
        totals = snapshot["totals"]
        self.assertEqual(totals["attempted_requests"], 2)
        self.assertEqual(totals["unresolved_requests"], 1)
        self.assertIsNone(totals["estimated_total_cost_usd"])
        known = Decimal(snapshot["requests"][0]["cost_usd"])
        reserve = Decimal(snapshot["requests"][1]["reserve_usd"])
        self.assertGreater(known, 0)
        self.assertEqual(Decimal(totals["known_estimated_spend_usd"]), known)
        self.assertEqual(Decimal(totals["estimated_exposure_usd"]), known + reserve)
        self.assertEqual(snapshot["run"]["summary"]["cases"][0]["outcome"]["ticks"], 1)

    def test_storage_failure_after_dispatch_cannot_erase_the_reserve(self):
        provider = FakeProvider(self.plan)
        with patch.object(self.journal, "save_response", side_effect=OSError("storage unavailable")):
            with self.assertRaises(OSError):
                runner.execute(self.plan, self.journal, "live", provider, "interrupted-run")
        self.assertEqual(len(provider.requests), 1)
        saved = self.journal.snapshot("interrupted-run")
        self.assertEqual(saved["totals"]["unresolved_requests"], 1)
        self.assertIsNone(saved["totals"]["estimated_total_cost_usd"])
        self.assertEqual(saved["requests"][0]["state"], "RESERVED")
        independent = Journal(self.journal.path)
        try:
            next_plan = copy.deepcopy(self.plan)
            next_plan["protocol_id"] += "-another"
            with self.assertRaises(RuntimeError):
                independent.start_run("another-run", "live", next_plan, {})
        finally:
            independent.close()

    def test_timeout_stops_without_retry_and_keeps_unknown_cost(self):
        def timeout(evidence, _count):
            evidence.update(error_type="TimeoutError", body_complete=False,
                            http_status=None, body_base64="")
        provider, snapshot = self.run_fake(override=timeout)
        self.assert_one_uncertain_attempt(provider, snapshot, "RESPONSE_UNCERTAIN")
        self.assertEqual(snapshot["run"]["summary"]["model_contexts_observed"], 0)

    def test_invalid_json_saved_before_parsing(self):
        def invalid(evidence, _count):
            evidence["body_base64"] = base64.b64encode(b"{broken").decode("ascii")
        provider, snapshot = self.run_fake(override=invalid)
        self.assert_one_uncertain_attempt(provider, snapshot, "INVALID_JSON")
        self.assertEqual(base64.b64decode(snapshot["requests"][0]["response"]["body_base64"]), b"{broken")

    def test_unexpected_model_is_unknown_and_stops(self):
        def unknown(response, _count):
            response["model"] = "unpriced-model"
        provider, snapshot = self.run_fake(mutate=unknown)
        self.assert_one_uncertain_attempt(provider, snapshot, "UNEXPECTED_MODEL")

    def test_unexpected_service_tier_is_unknown_and_stops(self):
        def tier(response, _count):
            response["service_tier"] = "priority"
        provider, snapshot = self.run_fake(mutate=tier)
        self.assert_one_uncertain_attempt(provider, snapshot, "UNEXPECTED_TIER")

    def test_incomplete_response_is_priced_then_stops_only_its_case(self):
        def incomplete(response, _count):
            response["status"] = "incomplete"
            response["incomplete_details"] = {"reason": "max_output_tokens"}
        provider, snapshot = self.run_fake(mutate=incomplete)
        self.assertEqual(len(provider.requests), 8)
        self.assertEqual(snapshot["totals"]["unresolved_requests"], 0)
        self.assertGreater(Decimal(snapshot["totals"]["estimated_total_cost_usd"]), 0)
        rows = snapshot["run"]["summary"]["cases"]
        self.assertEqual(rows[0]["reason"], "INCOMPLETE_RESPONSE")
        self.assertTrue(all(row["status"] == "CASE_FAILED" for row in rows))
        self.assertEqual(snapshot["run"]["status"], "COMPLETED")
        self.assertFalse(snapshot["run"]["summary"]["successful"])
        self.assertFalse(any(event["kind"] == "tool_action" for event in snapshot["events"]))

    def test_malformed_tool_call_has_no_service_effect(self):
        def malformed(response, _count):
            response["output"][-1]["arguments"] = '{"action":"commit","job":"C"}'
        provider, snapshot = self.run_fake(mutate=malformed)
        self.assertEqual(len(provider.requests), 8)
        row = snapshot["run"]["summary"]["cases"][0]
        self.assertEqual(row["reason"], "INVALID_TOOL_CALL")
        self.assertTrue(all(c["status"] == "CASE_FAILED" for c in snapshot["run"]["summary"]["cases"]))
        self.assertEqual(row["outcome"]["ticks"], 0)
        self.assertEqual(snapshot["totals"]["unresolved_requests"], 0)

    def test_budget_refusal_dispatches_nothing(self):
        self.plan["max_estimated_spend_usd"] = "0.008"
        self.plan["max_estimated_spend_per_case_usd"] = "0.001"
        provider, snapshot = self.run_fake()
        self.assertEqual(provider.requests, [])
        self.assertEqual(snapshot["requests"], [])
        self.assertEqual(snapshot["totals"]["attempted_requests"], 0)
        self.assertEqual(snapshot["run"]["summary"]["cases"][0]["reason"], "RUN_BUDGET_EXCEEDED")

    def test_state_lives_outside_checkout(self):
        with patch.dict(os.environ, {"LOCALAPPDATA": str(self.root), "XDG_STATE_HOME": str(self.root)}):
            self.assertEqual(runner.live_database(), self.root / "JoshRinLab" / "api-pilot" / "ledger.sqlite3")

    def test_default_cli_check_and_verify_are_offline_without_credentials(self):
        copy_root = self.root / "native café"
        copy_root.mkdir()
        for name in (*runner.SOURCE_FILES, "plan.json"):
            shutil.copy2(HERE / name, copy_root / name)
        environment = {key: value for key, value in os.environ.items()
                       if key not in {"OPENAI_API_KEY", "OPENAI_ORG_ID", "OPENAI_PROJECT_ID"}}
        environment.update(PYTHONUTF8="0", LOCALAPPDATA=str(self.root), XDG_STATE_HOME=str(self.root))
        bootstrap = ("import runpy,socket,sys; "
                     "blocked=lambda *a,**k: (_ for _ in ()).throw(AssertionError('Network forbidden')); "
                     "socket.socket.connect=blocked; socket.socket.connect_ex=blocked; "
                     "socket.create_connection=blocked; "
                     "sys.argv=sys.argv[1:]; runpy.run_path(sys.argv[0],run_name='__main__')")
        def command(*args):
            completed = subprocess.run([sys.executable, "-c", bootstrap, str(copy_root / "runner.py"), *args],
                                       cwd=copy_root, env=environment, capture_output=True,
                                       text=True, encoding="utf-8", timeout=30)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            return json.loads(completed.stdout)
        result = command()
        self.assertEqual(result["mode"], "fixture")
        self.assertEqual(result["safe_joint_completions"], 8)
        self.assertIsNone(result["provider_cost_usd"])
        self.assertEqual(command("verify", result["evidence"])["verified_assignments"], 8)
        self.assertEqual(command("check")["offline_storage_check"], "passed")


if __name__ == "__main__":
    unittest.main()
