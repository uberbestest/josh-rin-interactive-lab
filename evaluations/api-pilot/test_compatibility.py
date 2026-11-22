"""Independent scripted compatibility exchanges. All network access is forbidden."""
import base64
import contextlib
import copy
from decimal import Decimal
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from common import canonical, digest
from ledger import Journal, ReserveRefused
from test_runner import envelope
from test_transport import Connection, Response
from transport import Transport
import compatibility as compat

VALUE = "bedacafe" * 4


class Provider:
    organization, project = "org-offline", "proj-offline"

    def __init__(self, mutate=None, override=None, observe=None):
        self.requests, self.responses = [], []
        self.mutate, self.override, self.observe = mutate, override, observe

    def send(self, request):
        self.requests.append(copy.deepcopy(request))
        number = len(self.requests)
        if self.observe:
            self.observe(request, number)
        if number == 1:
            output = [{"type": "reasoning", "id": "rs-probe", "summary": [], "encrypted_content": "opaque café 🦆"},
                      {"type": "function_call", "id": "fc-probe", "name": "lab_probe", "call_id": "call-probe",
                       "arguments": "{}", "status": "completed"}]
        elif number == 2:
            output = [{"type": "message", "role": "assistant", "content": [
                {"type": "output_text", "text": request["input"][-1]["output"]}]}]
        else:
            raise AssertionError("A third provider request is forbidden")
        response = {"id": f"resp-probe-{number}", "model": compat.MODEL, "service_tier": "default",
                    "status": "completed", "output": output, "usage": {
                        "input_tokens": 100, "output_tokens": 10, "total_tokens": 110,
                        "input_tokens_details": {"cached_tokens": 0, "cache_write_tokens": 0},
                        "output_tokens_details": {"reasoning_tokens": 4}}}
        if self.mutate:
            self.mutate(response, number)
        self.responses.append(copy.deepcopy(response))
        evidence = envelope(response)
        if self.override:
            self.override(evidence, number)
        return evidence


class CompatibilityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.plan = compat.load_plan(compat.HERE / "compatibility.json")
        self.count = 0
        for target in ("socket.socket.connect", "socket.socket.connect_ex", "socket.create_connection"):
            guard = patch(target, side_effect=AssertionError("Network forbidden"))
            guard.start()
            self.addCleanup(guard.stop)

    def journal(self):
        self.count += 1
        journal = Journal(self.root / str(self.count) / "ledger.sqlite3")
        self.addCleanup(journal.close)
        return journal

    def execute(self, mutate=None, override=None, plan=None, nonce_factory=None, observe=None):
        provider, journal = Provider(mutate, override, observe), self.journal()
        snapshot = compat.execute(plan or self.plan, journal, "live", provider,
                                  nonce_factory=nonce_factory or (lambda: VALUE))
        compat.verify_snapshot(snapshot)
        return provider, snapshot, journal

    def test_exact_two_requests_replay_all_items_and_commit_before_effects(self):
        journal = self.journal()
        def saved():
            run_id = journal.db.execute("SELECT id FROM runs").fetchone()[0]
            independent = Journal(journal.path, read_only=True)
            try:
                return independent.snapshot(run_id)
            finally:
                independent.close()
        def observe(request, number):
            snapshot = saved()
            self.assertEqual(snapshot["requests"][-1]["payload"], request)
            self.assertEqual(snapshot["requests"][-1]["state"], "RESERVED")
            if number == 2:
                self.assertEqual(snapshot["requests"][0]["state"], "SETTLED")
                receipt = next(e for e in snapshot["events"] if e["kind"] == "probe_receipt")
                self.assertEqual(receipt["data"]["receipt"]["verification_value"], VALUE)
        def nonce():
            snapshot = saved()
            self.assertEqual(len(snapshot["requests"]), 1)
            self.assertEqual(snapshot["requests"][0]["state"], "SETTLED")
            self.assertFalse(any(e["kind"] == "probe_receipt" for e in snapshot["events"]))
            return VALUE
        provider = Provider(observe=observe)
        snapshot = compat.execute(self.plan, journal, "live", provider, nonce_factory=nonce)
        first, second = provider.requests
        self.assertNotIn(VALUE, canonical(first))
        self.assertEqual(first["tool_choice"], {"type": "function", "name": "lab_probe"})
        self.assertEqual(first["tools"][0]["parameters"],
                         {"type": "object", "properties": {}, "required": [], "additionalProperties": False})
        self.assertEqual(second["input"][1:-1], provider.responses[0]["output"])
        self.assertEqual(second["input"][-1]["call_id"], "call-probe")
        self.assertEqual(second["tool_choice"], "none")
        for request in provider.requests:
            self.assertEqual(request["service_tier"], "default")
            self.assertIs(request["store"], False)
            self.assertIs(request["parallel_tool_calls"], False)
            self.assertEqual(request["include"], ["reasoning.encrypted_content"])
            self.assertEqual(request["max_output_tokens"], 4096)
            self.assertEqual(request["reasoning"], {"effort": "medium"})
        result = snapshot["run"]["summary"]
        self.assertEqual(result["verdict"], "PASS")
        self.assertEqual(result["local_tool_executions"], 1)
        self.assertTrue(result["encrypted_reasoning_replay_demonstrated"])
        self.assertEqual(result["provider_cost_usd"], "0.0024")
        self.assertEqual([r["reserve_usd"] for r in snapshot["requests"]], ["0.32768"] * 2)

    def test_no_encrypted_item_does_not_claim_replay(self):
        def mutate(response, number):
            if number == 1:
                response["output"].pop(0)
        _, snapshot, _ = self.execute(mutate)
        result = snapshot["run"]["summary"]
        self.assertEqual(result["verdict"], "PASS")
        self.assertFalse(result["encrypted_reasoning_observed"])
        self.assertFalse(result["encrypted_reasoning_in_request_2"])
        self.assertFalse(result["encrypted_reasoning_replay_demonstrated"])

    def test_full_exchange_through_real_adapter_with_mocked_https(self):
        provider = Provider()
        wire_bodies = []
        class MockConnection(Connection):
            def request(self, method, path, body, headers):
                self_outer.assertEqual((method, path), ("POST", "/v1/responses"))
                wire_bodies.append(body)
                request = json.loads(body)
                evidence = provider.send(request)
                self.response = Response(base64.b64decode(evidence["body_base64"]))
        self_outer = self
        with patch("transport.http.client.HTTPSConnection", MockConnection):
            snapshot = compat.execute(self.plan, self.journal(), "live",
                                      Transport("offline-dummy-value", "org-offline", "proj-offline"),
                                      nonce_factory=lambda: VALUE)
        self.assertEqual(len(wire_bodies), 2)
        for raw, record in zip(wire_bodies, snapshot["requests"]):
            self.assertEqual(raw, canonical(record["payload"]).encode("utf-8"))
            self.assertEqual(record["response"]["headers"], {"x-request-id": "request-1"})
        self.assertNotIn("offline-dummy-value", canonical(snapshot))
        self.assertEqual(compat.verify_snapshot(snapshot)["verdict"], "PASS")

    def test_cache_usage_and_reasoning_are_priced_once_in_exchange(self):
        def mutate(response, number):
            response["usage"]["input_tokens_details"] = {
                "cached_tokens": 20, "cache_write_tokens": 30,
                "cache_write_tokens_details": {"ttl_30m_tokens": 10, "ttl_12h_tokens": 20}}
        _, snapshot, _ = self.execute(mutate)
        self.assertEqual(snapshot["run"]["summary"]["provider_cost_usd"], "0.002616")

    def test_invalid_scope_or_pricing_is_rejected_before_run(self):
        changes = [{"max_calls_per_case": 3}, {"max_output_tokens": 8192}, {"reasoning_effort": "high"},
                   {"nonce_bytes": 16.0}, {"max_estimated_spend_usd": "2"}, {"assignments": []},
                   {"reservation_policy": None}, {"pricing": {}}, {"accepted_returned_models": {compat.MODEL: [{}]}}]
        for change in changes:
            with self.subTest(change=change):
                with self.assertRaises(ValueError):
                    compat.execute(dict(self.plan, **change), self.journal(), "live", Provider())

    def test_bad_final_format_or_value_never_gets_repair_turn(self):
        for text in ('{"verification_value":"wrong"}', '```json\n{}\n```',
                     canonical({"verification_value": VALUE, "extra": 1}),
                     '{"verification_value":"wrong","verification_value":"' + VALUE + '"}',
                     'Here is the value: ' + VALUE, 'null'):
            with self.subTest(text=text):
                def mutate(response, number):
                    if number == 2:
                        response["output"][0]["content"][0]["text"] = text
                provider, snapshot, _ = self.execute(mutate)
                self.assertEqual(len(provider.requests), 2)
                self.assertEqual(snapshot["run"]["summary"]["verdict"], compat.NOT_DEMONSTRATED)
                self.assertEqual(snapshot["run"]["status"], "COMPLETED")
                self.assertFalse(snapshot["run"]["summary"]["encrypted_reasoning_replay_demonstrated"])

    def test_invalid_first_call_prevents_nonce_and_second_request(self):
        changes = [lambda output: output.clear(),
                   lambda output: output.append(copy.deepcopy(output[-1])),
                   lambda output: output[-1].update(name="other_tool"),
                   lambda output: output[-1].update(call_id=" "),
                   lambda output: output[-1].update(status="in_progress"),
                   lambda output: output[-1].update(arguments='{"extra":1}'),
                   lambda output: output[-1].update(arguments="[]"),
                   lambda output: output[-1].update(arguments="{")]
        for change in changes:
            with self.subTest(change=change):
                def mutate(response, number):
                    change(response["output"])
                provider, snapshot, _ = self.execute(mutate, nonce_factory=lambda: self.fail("Nonce generated prematurely"))
                self.assertEqual(len(provider.requests), 1)
                self.assertEqual(snapshot["run"]["summary"]["verdict"], compat.NOT_DEMONSTRATED)
                self.assertEqual(snapshot["run"]["summary"]["local_tool_executions"], 0)
                self.assertEqual(snapshot["totals"]["unresolved_requests"], 0)

    def test_nonce_must_first_occur_in_local_receipt(self):
        def mutate(response, number):
            response["output"][0]["summary"] = [{"type": "summary_text", "text": VALUE}]
        for change, value in ((mutate, VALUE), (None, "not-32-hex")):
            provider, snapshot, _ = self.execute(change, nonce_factory=lambda: value)
            self.assertEqual(len(provider.requests), 1)
            self.assertEqual(snapshot["run"]["summary"]["reason"], "INVALID_OR_NONFRESH_RECEIPT")

    def test_uncertain_outcomes_remain_reserved_at_either_stage(self):
        mutations = {
            "missing_usage": lambda r: r.pop("usage"),
            "unknown_model": lambda r: r.update(model="unpriced-model"),
            "unknown_tier": lambda r: r.update(service_tier="priority"),
            "unsupported_output": lambda r: r.update(output=[{"type": "web_search_call"}]),
            "unsupported_audio": lambda r: r.update(output=[{"type": "message", "content": [{"type": "audio"}]}]),
        }
        overrides = {
            "timeout": lambda e: e.update(error_type="TimeoutError", body_complete=False),
            "partial": lambda e: e.update(body_complete=False, body_base64="ew=="),
            "rejected": lambda e: e.update(http_status=401),
            "invalid_json": lambda e: e.update(body_base64=base64.b64encode(b'{bad').decode()),
            "bad_timing": lambda e: e.update(elapsed_seconds=-1),
        }
        for stage in (1, 2):
            for name in (*mutations, *overrides):
                with self.subTest(stage=stage, error=name):
                    def mutate(response, number):
                        if number == stage and name in mutations:
                            mutations[name](response)
                    def override(evidence, number):
                        if number == stage and name in overrides:
                            overrides[name](evidence)
                    provider, snapshot, journal = self.execute(mutate, override)
                    self.assertEqual(len(provider.requests), stage)
                    self.assertEqual(snapshot["totals"]["unresolved_requests"], 1)
                    self.assertIsNone(snapshot["run"]["summary"]["provider_cost_usd"])
                    self.assertIsNone(snapshot["requests"][-1]["cost_usd"])
                    self.assertGreater(Decimal(snapshot["totals"]["unresolved_reserve_usd"]), 0)
                    self.assertEqual(snapshot["run"]["summary"]["verdict"], compat.BLOCKED)
                    self.assertEqual(snapshot["run"]["status"], "HALTED")
                    if stage == 1 and name == "missing_usage":
                        self.assertTrue(snapshot["run"]["summary"]["encrypted_reasoning_observed"])
                    self.assertEqual(len(snapshot["run"]["summary"]["request_slots"]), 2)
                    with self.assertRaises(RuntimeError):
                        journal.review_halt(snapshot["run"]["id"], digest(snapshot), "reviewer", "unknown cost",
                                            protocol_verifier=compat.verify_snapshot)
                    with self.assertRaises(RuntimeError):
                        journal.start_run("new", "live", dict(self.plan, protocol_id="different"), {})

    def test_transport_exception_is_preserved_without_exception_text(self):
        def observe(request, number):
            raise TimeoutError("sensitive exception detail")
        provider, snapshot, _ = self.execute(observe=observe)
        self.assertEqual(len(provider.requests), 1)
        self.assertEqual(snapshot["requests"][0]["response"]["error_type"], "TimeoutError")
        self.assertNotIn("sensitive exception detail", canonical(snapshot))

    def test_priced_truncation_at_either_stage_is_observed_failure(self):
        for stage in (1, 2):
            def mutate(response, number):
                if number == stage:
                    response.update(status="incomplete", output=[], incomplete_details={"reason": "max_output_tokens"})
            provider, snapshot, _ = self.execute(mutate)
            self.assertEqual(len(provider.requests), stage)
            self.assertEqual(snapshot["totals"]["unresolved_requests"], 0)
            self.assertEqual(snapshot["run"]["summary"]["reason"], "INCOMPLETE_RESPONSE")
            self.assertEqual(snapshot["run"]["summary"]["verdict"], compat.NOT_DEMONSTRATED)

    def test_provider_output_overrun_is_known_halt_and_reviewable(self):
        def mutate(response, number):
            response["usage"].update(output_tokens=4097, total_tokens=4197)
        provider, snapshot, journal = self.execute(mutate)
        self.assertEqual(len(provider.requests), 1)
        self.assertEqual(snapshot["totals"]["unresolved_requests"], 0)
        self.assertEqual(snapshot["run"]["summary"]["reason"], "OUTPUT_LIMIT_EXCEEDED")
        event = journal.review_halt(snapshot["run"]["id"], digest(snapshot), "offline reviewer", "accounted mock violation",
                                    protocol_verifier=compat.verify_snapshot)
        self.assertEqual(event["data"]["reviewed_snapshot_sha256"], digest(snapshot))
        compat.verify_snapshot(journal.snapshot(snapshot["run"]["id"]))
        journal.start_run("new", "live", dict(self.plan, protocol_id="separately-approved-test-only"), {})
        with self.assertRaises(RuntimeError):
            journal.start_run("same-protocol", "live", self.plan, {})

    def test_budget_gates_before_first_or_second_dispatch(self):
        plan = copy.deepcopy(self.plan)
        plan.update(max_estimated_spend_usd="0.1", max_estimated_spend_per_case_usd="0.1")
        provider, snapshot, _ = self.execute(plan=plan)
        self.assertEqual(len(provider.requests), 0)
        self.assertEqual(snapshot["run"]["summary"]["reason"], "RUN_BUDGET_EXCEEDED")
        plan.update(max_estimated_spend_usd="0.4", max_estimated_spend_per_case_usd="0.4")
        def grow(response, number):
            response["usage"].update(input_tokens=12000, total_tokens=12010)
        provider, snapshot, _ = self.execute(grow, plan=plan)
        self.assertEqual(len(provider.requests), 1)
        self.assertEqual(snapshot["totals"]["unresolved_requests"], 0)
        self.assertEqual(snapshot["run"]["summary"]["reason"], "RUN_BUDGET_EXCEEDED")

    def test_continuation_uses_provider_tokens_not_ciphertext_bytes(self):
        def grow(response, number):
            if number == 1:
                response["usage"].update(input_tokens=12000, total_tokens=12010)
                response["output"][0]["encrypted_content"] = "padding" * 10000
        _, snapshot, _ = self.execute(grow)
        self.assertEqual(snapshot["requests"][1]["reserve_usd"], "0.42452")
        self.assertEqual(snapshot["run"]["summary"]["verdict"], "PASS")

    def test_reserve_overrun_is_recorded_and_no_continuation_occurs(self):
        def grow(response, number):
            response["usage"].update(input_tokens=50000, total_tokens=50010)
        provider, snapshot, _ = self.execute(grow)
        self.assertEqual(len(provider.requests), 1)
        self.assertEqual(snapshot["run"]["summary"]["reason"], "RESERVE_EXCEEDED")
        self.assertEqual(snapshot["totals"]["unresolved_requests"], 0)

    def test_fixture_and_export_never_claim_provider_usage(self):
        snapshot = compat.execute(self.plan, self.journal())
        result = snapshot["run"]["summary"]
        self.assertEqual(result["verdict"], "FIXTURE_PASS")
        self.assertEqual(result["fixture_exchanges"], 2)
        self.assertIsNone(result["provider_requests_attempted"])
        self.assertIsNone(result["provider_cost_usd"])
        self.assertFalse(result["encrypted_reasoning_replay_demonstrated"])
        for record in snapshot["requests"]:
            self.assertEqual(record["calculation"]["basis"], "offline_fixture_not_provider_usage")
        path = self.root / "private" / "evidence.json"
        compat.export_snapshot(snapshot, path)
        self.assertEqual(compat.verify_export(path), result)
        with self.assertRaises(FileExistsError):
            compat.export_snapshot(snapshot, path)

    def test_interruption_before_response_keeps_reserve_and_two_slot_denominator(self):
        journal = self.journal()
        with patch.object(journal, "save_response", side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                compat.execute(self.plan, journal, "live", Provider())
        run_id = journal.db.execute("SELECT id FROM runs").fetchone()[0]
        snapshot = journal.snapshot(run_id)
        result = compat.verify_snapshot(snapshot)
        self.assertEqual(result["reason"], "RESPONSE_UNRECORDED")
        self.assertEqual(len(result["request_slots"]), 2)
        self.assertEqual(snapshot["totals"]["unresolved_requests"], 1)
        self.assertIsNone(result["provider_cost_usd"])
        path = self.root / "partial.json"
        compat.export_snapshot(snapshot, path)
        self.assertEqual(compat.verify_export(path), result)
        with self.assertRaises(RuntimeError):
            compat.execute(dict(self.plan, protocol_id="new-unapproved"), journal, "live", Provider())

    def test_semantic_verifier_checks_more_than_hashes(self):
        _, original, _ = self.execute()
        # Bypass just the accounting checker to prove semantic replay is an
        # independent check of the actual exchange, rather than a hash-only PASS.
        changes = [lambda s: s["requests"][1]["payload"]["input"][1].update(encrypted_content="lost"),
                   lambda s: s["requests"][1]["payload"]["input"][-1].update(call_id="wrong-call"),
                   lambda s: s["run"]["metadata"].update(prompt_sha256="0" * 64),
                   lambda s: s["run"]["metadata"]["source_bundle"]["transport.py"].update(body_base64=""),
                   lambda s: s["requests"][0].update(reserve_usd="0.01"),
                   lambda s: s["requests"][0]["calculation"].update(estimated_cost_usd="0"),
                   lambda s: s["run"]["summary"].update(encrypted_reasoning_replay_demonstrated=False),
                   lambda s: next(e for e in s["events"] if e["kind"] == "probe_receipt")["data"].update(request_id="wrong"),
                   lambda s: next(e for e in s["events"] if e["kind"] == "probe_receipt").update(sequence=1),
                   lambda s: s["requests"].append(copy.deepcopy(s["requests"][-1]))]
        for change in changes:
            with self.subTest(change=change):
                altered = copy.deepcopy(original)
                change(altered)
                with patch.object(compat, "verify_accounting"):
                    with self.assertRaises((ValueError, RuntimeError)):
                        compat.verify_snapshot(altered)
        altered = copy.deepcopy(original)
        altered["requests"][0]["response"]["body_base64"] = "e30="
        with self.assertRaises((ValueError, RuntimeError)):
            compat.verify_snapshot(altered)

    def test_ledger_itself_forbids_third_reservation(self):
        journal = self.journal()
        journal.start_run("fixed", "live", self.plan, {})
        for index in range(2):
            rid = journal.reserve("fixed", "compat01", {}, "0.01")
            journal.save_response(rid, {})
            journal.settle(rid, {"estimated_cost_usd": "0.001"})
        with self.assertRaises(ReserveRefused) as caught:
            journal.reserve("fixed", "compat01", {}, "0.01")
        self.assertEqual(caught.exception.reason, "CALL_LIMIT")

    def test_freeze_binds_source_and_plan_and_bad_approval_never_reads_credentials(self):
        bundle = compat.source_bundle()
        original = compat.freeze_hash(self.plan, bundle)
        self.assertNotEqual(original, compat.freeze_hash(dict(self.plan, purpose="changed"), bundle))
        bundle["transport.py"]["sha256"] = "0" * 64
        self.assertNotEqual(original, compat.freeze_hash(self.plan, bundle))
        with patch.object(compat, "credentials", side_effect=AssertionError("Credential access forbidden")), \
                patch.object(compat, "Transport", side_effect=AssertionError("Network forbidden")), \
                contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(compat.main(["check"]), 0)
            self.assertEqual(compat.main(["live", "--approve-freeze", "wrong"]), 1)
            self.assertEqual(compat.main(["dry-run", "--output", str(self.root / "cli")] ), 0)
            self.assertEqual(compat.main(["verify", str(self.root / "cli" / "evidence.json")]), 0)

    def test_cli_returns_failure_for_recorded_unsuccessful_exchange(self):
        real_fixture = compat.fixture_response
        def bad_fixture(request, number):
            evidence = real_fixture(request, number)
            if number == 2:
                body = json.loads(base64.b64decode(evidence["body_base64"]))
                body["output"][0]["content"][0]["text"] = '{"verification_value":"wrong"}'
                evidence["body_base64"] = base64.b64encode(canonical(body).encode()).decode()
            return evidence
        with patch.object(compat, "fixture_response", side_effect=bad_fixture), \
                contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(compat.main(["dry-run", "--output", str(self.root / "cli-failed")]), 2)


if __name__ == "__main__":
    unittest.main()
