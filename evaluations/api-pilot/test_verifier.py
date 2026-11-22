"""Semantic tamper tests use local scripted responses; no provider connection."""
import base64
import copy
import json
from pathlib import Path
import socket
import tempfile
import unittest
from unittest.mock import patch

from common import canonical, now
from ledger import Journal
from protocol import Fixture
import runner
from verifier import parse_action, validate_output, verify_snapshot

HERE = Path(__file__).resolve().parent


class Provider:
    organization, project = "fixture-org", "fixture-project"

    def __init__(self, plan, mode="happy"):
        self.plan, self.mode = plan, mode
        self.assignment, self.calls = -1, 0

    def send(self, payload):
        self.calls += 1
        if len(payload["input"]) == 1:
            self.assignment += 1
            self.fixture = Fixture(self.plan["assignments"][self.assignment]["case"])
        response = self.fixture.create(payload)
        response.update(model=payload["model"], service_tier="default", usage={
            "input_tokens": 100, "output_tokens": 20,
            "input_tokens_details": {"cached_tokens": 0, "cache_write_tokens": 0}})
        if self.mode == "missing_usage":
            response.pop("usage")
        if self.mode == "incomplete":
            response["status"] = "incomplete"
        if self.mode == "incomplete_empty":
            response.update(status="incomplete", output=[])
        if self.mode == "empty_object":
            response = {}
        if self.mode == "output_overrun":
            response["usage"]["output_tokens"] = self.plan["max_output_tokens"] + 1
        timestamp = now()
        return {"http_status": 200, "headers": {}, "body_base64": base64.b64encode(canonical(response).encode()).decode(),
                "started_utc": timestamp, "ended_utc": timestamp, "elapsed_seconds": 0,
                "error_type": None, "body_complete": True}


class VerifierTests(unittest.TestCase):
    def setUp(self):
        blocker = patch.object(socket.socket, "connect", side_effect=AssertionError("No network permitted"))
        blocker.start()
        self.addCleanup(blocker.stop)
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.journal = Journal(Path(self.directory.name) / "ledger.sqlite3")
        self.addCleanup(self.journal.close)
        self.plan = runner.load_plan(HERE / "plan.json")

    def snapshot(self, live=False, mode="happy"):
        transport = Provider(self.plan, mode) if live else None
        return runner.execute(self.plan, self.journal, mode="live" if live else "fixture",
                              transport=transport, run_id="verification-fixture")

    def test_replays_full_fixture_and_frozen_bundle(self):
        snapshot = self.snapshot()
        result = verify_snapshot(snapshot)
        self.assertEqual(result["verified_assignments"], 8)
        self.assertEqual(result["verified_requests"], 0)
        self.assertEqual(result["verified_tool_actions"], 40)
        self.assertEqual(result["verified_source_files"], 6)
        self.assertTrue(result["complete"])

    def test_replays_full_priced_mock_provider_history(self):
        result = verify_snapshot(self.snapshot(live=True))
        self.assertEqual(result["verified_requests"], 48)
        self.assertEqual(result["verified_tool_actions"], 40)

    def test_unknown_usage_and_truncation_never_produce_actions(self):
        snapshot = self.snapshot(live=True, mode="missing_usage")
        result = verify_snapshot(snapshot)
        self.assertEqual(result["verified_requests"], 1)
        self.assertEqual(result["verified_tool_actions"], 0)
        self.assertIsNone(snapshot["run"]["summary"]["provider_cost_usd"])
        self.assertEqual(snapshot["run"]["summary"]["cases"][1]["status"], "BLOCKED")

    def test_incomplete_response_is_priced_but_not_acted_on(self):
        snapshot = self.snapshot(live=True, mode="incomplete_empty")
        self.assertEqual(verify_snapshot(snapshot)["verified_tool_actions"], 0)
        self.assertIsNotNone(snapshot["requests"][0]["cost_usd"])
        self.assertEqual(snapshot["run"]["summary"]["cases"][0]["reason"], "INCOMPLETE_RESPONSE")
        self.assertTrue(snapshot["run"]["summary"]["cases"][0]["model_response_observed"])
        self.assertEqual(snapshot["run"]["summary"]["model_contexts_observed"], 1)

    def test_empty_json_object_is_not_observed_model_context(self):
        snapshot = self.snapshot(live=True, mode="empty_object")
        self.assertEqual(verify_snapshot(snapshot)["verified_tool_actions"], 0)
        row = snapshot["run"]["summary"]["cases"][0]
        self.assertEqual(row["responses"], 1)
        self.assertEqual(row["reason"], "INVALID_JSON")
        self.assertFalse(row["model_response_observed"])
        self.assertEqual(snapshot["run"]["summary"]["model_contexts_observed"], 0)

    def test_output_token_overrun_is_priced_and_stops_before_action(self):
        snapshot = self.snapshot(live=True, mode="output_overrun")
        self.assertEqual(verify_snapshot(snapshot)["verified_tool_actions"], 0)
        self.assertIsNotNone(snapshot["requests"][0]["cost_usd"])
        self.assertEqual(snapshot["run"]["summary"]["cases"][0]["reason"], "OUTPUT_LIMIT_EXCEEDED")

    def test_changed_exact_request_or_tool_effect_is_rejected(self):
        original = self.snapshot()
        for event_kind, edit in [
                ("fixture_exchange", lambda data: data["request"].update(service_tier="priority")),
                ("tool_action", lambda data: data["result"].update(accepted=False)),
                ("case_finished", lambda data: data["outcome"].update(unsafe_attempts=7))]:
            snapshot = copy.deepcopy(original)
            edit(next(event["data"] for event in snapshot["events"] if event["kind"] == event_kind))
            with self.subTest(kind=event_kind), self.assertRaises(ValueError):
                verify_snapshot(snapshot)

    def test_tampered_denominator_summary_or_frozen_source_is_rejected(self):
        original = self.snapshot()
        changes = [lambda s: s["run"]["summary"].update(assigned_contexts=7),
                   lambda s: s["run"]["summary"].update(model_contexts_observed=8),
                   lambda s: s["run"]["metadata"]["source_bundle"]["protocol.py"].update(body_base64="eA=="),
                   lambda s: s["run"]["metadata"].update(prompt_sha256="0" * 64)]
        for change in changes:
            snapshot = copy.deepcopy(original)
            change(snapshot)
            with self.assertRaises(ValueError):
                verify_snapshot(snapshot)

    def test_usage_price_recomputed_from_raw_response(self):
        snapshot = self.snapshot(live=True)
        event = next(event for event in snapshot["events"] if event["kind"] == "response_saved")
        envelope = event["data"]["envelope"]
        body = json.loads(base64.b64decode(envelope["body_base64"]))
        body["usage"]["output_tokens"] = 21
        envelope["body_base64"] = base64.b64encode(canonical(body).encode()).decode()
        snapshot["requests"][0]["response"] = copy.deepcopy(envelope)
        with self.assertRaisesRegex(ValueError, "Recomputed price"):
            verify_snapshot(snapshot)

    def test_interrupted_unresolved_request_stays_partial(self):
        snapshot = self.snapshot(live=True)
        first_reserved = next(i for i, event in enumerate(snapshot["events"]) if event["kind"] == "request_reserved")
        snapshot["events"] = snapshot["events"][:first_reserved + 1]
        snapshot["requests"] = snapshot["requests"][:1]
        snapshot["requests"][0].update(cost_usd=None, response=None, calculation=None)
        snapshot["run"]["summary"] = None
        result = verify_snapshot(snapshot)
        self.assertFalse(result["complete"])
        self.assertEqual(result["planned_assignments"], 8)
        self.assertEqual(result["verified_assignments"], 0)
        self.assertEqual(result["verified_requests"], 1)


class OutputValidationTests(unittest.TestCase):
    def call(self, **updates):
        return {"type": "function_call", "name": "service_action", "call_id": "call-1",
                "arguments": '{"action":"receipt","job":"A"}', **updates}

    def test_builtin_tools_and_malformed_output_are_rejected(self):
        for output in (None, {}, [None], [{"type": "web_search_call"}], [{"type": "computer_call"}],
                       [{"type": "message", "content": [{"type": "output_audio"}]}],
                       [{"type": "message", "content": [None]}]):
            with self.subTest(output=output), self.assertRaises(ValueError):
                validate_output(output)

    def test_empty_output_is_priceable_but_not_a_valid_completed_turn(self):
        validate_output([])
        with self.assertRaises(ValueError):
            parse_action([], set())

    def test_reasoning_preserved_and_call_identity_cannot_replay(self):
        seen = set()
        output = [{"type": "reasoning", "encrypted_content": "opaque-fixture"}, self.call()]
        self.assertEqual(parse_action(output, seen), {"call_id": "call-1", "action": "receipt", "job": "A"})
        self.assertEqual(len(output), 2)
        with self.assertRaises(ValueError):
            parse_action(output, seen)

    def test_multiple_bad_identity_and_malicious_arguments_cannot_mutate_seen(self):
        cases = [[self.call(), self.call(call_id="call-2")], [self.call(call_id=" ")],
                 [self.call(name="other_tool")], [self.call(arguments='{"action":"receipt","job":"A","extra":true}')],
                 [self.call(arguments='{"action":"receipt","action":"commit","job":"A"}')],
                 [self.call(arguments='{"action":"exec","job":"A"}')], [self.call(arguments="null")]]
        for output in cases:
            seen = set()
            with self.subTest(output=output), self.assertRaises(ValueError):
                parse_action(output, seen)
            self.assertEqual(seen, set())


if __name__ == "__main__":
    unittest.main()
