"""Audit regressions: all provider calls use in-memory fixtures; sockets forbidden."""
import copy
import contextlib
import io
import json
from decimal import Decimal
from pathlib import Path
import socket
import os
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import runner


def manifest():
    return json.loads((runner.HERE / "manifest.json").read_text())


def usage():
    return {"input_tokens": 100, "output_tokens": 20, "total_tokens": 120,
            "input_tokens_details": {"cached_tokens": 0, "cache_write_tokens": 0},
            "output_tokens_details": {"reasoning_tokens": 10}}


class FakeRaw:
    def __init__(self, response, payload):
        self.text = runner.canonical(response)
        self.status_code = 200
        self.headers = {"x-request-id": "offline-request"}
        self.http_request = SimpleNamespace(content=runner.canonical(payload).encode())

    def parse(self):
        return json.loads(self.text)


class FakeClient:
    def __init__(self, mode="happy", settings=None):
        self.mode, self.settings = mode, settings or manifest()
        self.requests = []
        self.responses = SimpleNamespace(with_raw_response=self)
        self.assignment = -1

    def create(self, **payload):
        self.requests.append(copy.deepcopy(payload))
        if self.mode == "timeout" or (self.mode == "second_timeout" and len(self.requests) == 2):
            raise TimeoutError("offline uncertain charge")
        if self.mode == "interrupt":
            raise KeyboardInterrupt()
        if len(payload["input"]) == 1:
            self.assignment += 1
            case = self.settings["cases"][self.assignment % len(self.settings["cases"])]
            self.fixture = runner.DryResponseClient(case)
        response = self.fixture.create()
        response.update(model=payload["model"], usage=usage(), service_tier="default")
        response["output"].insert(0, {"type": "reasoning", "id": "offline-reasoning",
                                      "summary": [], "encrypted_content": "offline-encrypted"})
        if self.mode == "missing_usage":
            response["usage"] = None
        elif self.mode == "missing_categories":
            del response["usage"]["input_tokens_details"]["cache_write_tokens"]
        elif self.mode == "incomplete":
            response.update(status="incomplete", incomplete_details={"reason": "max_output_tokens"})
        elif self.mode == "wrong_tier":
            response["service_tier"] = "priority"
        elif self.mode == "wrong_model":
            response["model"] = "unexpected-snapshot"
        elif self.mode == "over_reserve":
            response["usage"] = {**usage(), "input_tokens": 250000, "total_tokens": 250020}
        elif self.mode == "invalid_tool":
            response["output"][-1]["arguments"] = '{"action":"commit","job":"X"}'
        elif self.mode == "missing_call_id":
            del response["output"][-1]["call_id"]
        elif self.mode == "duplicate_call_id":
            response["output"][-1]["call_id"] = "offline-reused"
        raw = FakeRaw(response, payload)
        if self.mode == "invalid_json":
            raw.text = "{invalid json from offline server"
        return raw


class RegressionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.out = Path(self.temp.name) / "archive"
        self.manifest = manifest()
        self.socket_patch = patch.object(socket.socket, "connect", side_effect=AssertionError("No network"))
        self.socket_patch.start()
        self.addCleanup(self.socket_patch.stop)

    def execute(self, mode="happy", settings=None):
        settings = settings or self.manifest
        client = FakeClient(mode, settings)
        summary = runner.execute(settings, runner.canonical(settings).encode(), True, client, self.out)
        rows = [json.loads(s) for s in (self.out / "assigned-results.jsonl").read_text().splitlines()]
        return client, summary, rows

    def events(self, row):
        return [json.loads(s) for s in (self.out / (row["case_id"] + ".jsonl")).read_text().splitlines()]

    def test_missing_usage_stops_batch_retains_response_and_reserve(self):
        client, summary, rows = self.execute("missing_usage")
        self.assertEqual(len(client.requests), 1)
        self.assertEqual(summary["provider_attempted_requests"], 1)
        self.assertIsNone(summary["estimated_provider_cost_usd"])
        self.assertEqual(summary["unresolved_requests"], 1)
        self.assertGreater(Decimal(summary["unresolved_reserve_usd"]), 0)
        self.assertIsNone(rows[0]["provider_estimated_cost_usd"])
        self.assertEqual(len(rows), 8)
        self.assertTrue(all(r["assignment_status"] == "blocked_unattempted" for r in rows[1:]))
        self.assertTrue(any(e["event"] == "provider_response" for e in self.events(rows[0])))
        self.assertEqual(runner.verify_archive(self.out)["verified_assignments"], 8)

    def test_timeout_is_one_attempt_not_zero_cost(self):
        client, summary, rows = self.execute("timeout")
        self.assertEqual(len(client.requests), 1)
        self.assertEqual(rows[0]["provider_calls"], 1)
        self.assertEqual(rows[0]["provider_responses"], 0)
        self.assertIsNone(summary["estimated_provider_cost_usd"])
        self.assertIsNone(rows[0]["provider_estimated_cost_usd"])
        self.assertFalse(rows[0]["scientific_model_participant"])

    def test_prior_known_charge_preserved_when_later_call_times_out(self):
        client, summary, rows = self.execute("second_timeout")
        self.assertEqual(len(client.requests), 2)
        self.assertEqual(Decimal(summary["known_estimated_provider_cost_usd"]), Decimal("0.002"))
        self.assertIsNone(summary["estimated_provider_cost_usd"])
        self.assertIsNone(summary["cost_per_assigned_task_usd"])
        ledger = json.loads((self.out / "budget.json").read_text())
        self.assertEqual(ledger["unresolved_requests"], 1)
        self.assertEqual(ledger["estimated_exposure_usd"], str(Decimal("0.002") + Decimal(ledger["unresolved_reserve_usd"])))

    def test_interrupt_preserves_reserve_and_blocks_later_assignments(self):
        client, summary, _ = self.execute("interrupt")
        self.assertEqual(len(client.requests), 1)
        self.assertEqual(summary["halt_reason"], "UNRESOLVED_REQUEST")

    def test_missing_categories_fail_closed(self):
        client, summary, _ = self.execute("missing_categories")
        self.assertEqual(len(client.requests), 1)
        self.assertIsNone(summary["estimated_provider_cost_usd"])

    def test_invalid_raw_json_is_retained_before_parse_failure(self):
        client, summary, rows = self.execute("invalid_json")
        self.assertEqual(len(client.requests), 1)
        self.assertIsNone(summary["estimated_provider_cost_usd"])
        raw = next(e for e in self.events(rows[0]) if e["event"] == "provider_response")
        self.assertEqual(raw["body"], "{invalid json from offline server")

    def test_incomplete_response_is_priced_but_stops_protocol(self):
        client, summary, rows = self.execute("incomplete")
        self.assertEqual(len(client.requests), 1)
        self.assertEqual(Decimal(summary["estimated_provider_cost_usd"]), Decimal("0.002"))
        self.assertEqual(summary["unresolved_requests"], 0)
        self.assertEqual(rows[0]["errors"], ["INCOMPLETE_PROVIDER_RESPONSE"])
        self.assertTrue(all(r["errors"] for r in rows[1:]))

    def test_unexpected_model_or_tier_preserves_uncertainty(self):
        for mode in ("wrong_model", "wrong_tier"):
            with self.subTest(mode=mode):
                self.out = Path(self.temp.name) / mode
                client, summary, _ = self.execute(mode)
                self.assertEqual(len(client.requests), 1)
                self.assertIsNone(summary["estimated_provider_cost_usd"])

    def test_reserve_overrun_records_charge_and_halts(self):
        client, summary, _ = self.execute("over_reserve")
        self.assertEqual(len(client.requests), 1)
        self.assertEqual(summary["halt_reason"], "RESERVE_EXCEEDED")
        self.assertGreater(Decimal(summary["estimated_provider_cost_usd"]), Decimal("0.625"))

    def test_global_and_case_budget_block_without_requests(self):
        for limit, expected in (("max_estimated_spend_usd", "LOCAL_BUDGET_CIRCUIT_BREAKER"),
                                ("max_estimated_spend_per_case_usd", "CASE_BUDGET_CIRCUIT_BREAKER")):
            with self.subTest(limit=limit):
                settings = {**self.manifest, limit: 0.000001}
                budget = runner.Budget(settings)
                client = FakeClient()
                row = runner.run_case(settings["cases"][0], settings["models"][0], settings,
                                      True, client, Path(self.temp.name), budget)
                self.assertEqual(client.requests, [])
                self.assertEqual(row["errors"], [expected])
                self.assertFalse(row["scientific_model_participant"])

    def test_reserve_is_durable_before_client_dispatch(self):
        original = FakeClient.create

        def checked_create(client, **payload):
            ledger = json.loads((self.out / "budget.json").read_text())
            self.assertEqual(ledger["unresolved_requests"], 1)
            self.assertGreater(Decimal(ledger["unresolved_reserve_usd"]), 0)
            return original(client, **payload)

        with patch.object(FakeClient, "create", checked_create):
            self.execute()

    def test_journal_write_failure_prevents_dispatch(self):
        client = FakeClient()
        budget = runner.Budget(self.manifest, Path(self.temp.name) / "budget.json")
        with patch.object(budget, "persist", side_effect=OSError("offline disk full")):
            with self.assertRaises(OSError):
                runner.run_case(self.manifest["cases"][0], self.manifest["models"][0],
                                self.manifest, True, client, Path(self.temp.name), budget)
        self.assertFalse(client.requests)

    def test_post_response_disk_failure_does_not_dispatch_again(self):
        client = FakeClient()
        budget = runner.Budget(self.manifest, Path(self.temp.name) / "budget.json")
        original = runner.Trace.add

        def failed_add(trace, event, **fields):
            if event == "provider_response":
                raise OSError("offline disk full")
            return original(trace, event, **fields)

        with patch.object(runner.Trace, "add", failed_add):
            row = runner.run_case(self.manifest["cases"][0], self.manifest["models"][0],
                                  self.manifest, True, client, Path(self.temp.name), budget)
        self.assertEqual(len(client.requests), 1)
        self.assertIsNone(row["provider_estimated_cost_usd"])
        self.assertEqual(json.loads(budget.path.read_text())["unresolved_requests"], 1)

    def test_live_guard_is_exclusive_and_survives_restarts(self):
        path = Path(self.temp.name) / "guard.json"
        runner.acquire_live_guard(path, self.out, "abc")
        with self.assertRaises(FileExistsError):
            runner.acquire_live_guard(path, self.out, "abc")
        self.assertEqual(json.loads(path.read_text())["status"], "STARTED_OR_INTERRUPTED")

    def test_happy_loop_blinding_evidence_and_replay(self):
        client, summary, rows = self.execute()
        self.assertEqual(summary["safe_joint_completions"], 8)
        self.assertEqual(summary["provider_attempted_requests"], 48)
        initial = [r["input"] for r in client.requests if len(r["input"]) == 1]
        self.assertEqual(len(initial), 8)
        self.assertTrue(all(prompt == initial[0] for prompt in initial))
        self.assertNotIn("precommitted", runner.canonical(initial[0]))
        self.assertNotIn("_target", runner.canonical(initial[0]))
        for request in client.requests:
            self.assertEqual(request["service_tier"], "default")
            self.assertEqual(request["max_output_tokens"], 4096)
            if len(request["input"]) > 1:
                self.assertTrue(any(i.get("encrypted_content") for i in request["input"]))
                self.assertEqual(request["input"][-1]["type"], "function_call_output")
        for row in rows:
            self.assertGreaterEqual(row["elapsed_seconds"], 0)
            self.assertLessEqual(row["started_utc"], row["ended_utc"])
        self.assertEqual(runner.verify_archive(self.out)["verified_assignments"], 8)
        self.assertEqual((self.out / "runner.py").read_bytes(), Path(runner.__file__).read_bytes())

    def test_archive_tampering_is_detected(self):
        _, _, rows = self.execute()
        path = self.out / (rows[0]["case_id"] + ".jsonl")
        path.write_text(path.read_text().replace('"action":"receipt"', '"action":"commit"', 1))
        with self.assertRaises(ValueError):
            runner.verify_archive(self.out)
        runner.seal_archive(self.out)
        with self.assertRaises(ValueError):
            runner.verify_archive(self.out)

    def test_missing_assignment_is_detected_after_reseal(self):
        self.execute()
        path = self.out / "assigned-results.jsonl"
        path.write_text("\n".join(path.read_text().splitlines()[:-1]) + "\n")
        runner.seal_archive(self.out)
        with self.assertRaises(ValueError):
            runner.verify_archive(self.out)

    def test_invalid_tool_cannot_mutate_service(self):
        _, _, rows = self.execute("invalid_tool")
        self.assertTrue(all(r["reported_outcome"]["actions"] == 0 for r in rows))
        self.assertTrue(all(r["errors"] == ["INVALID_PROVIDER_TOOL_OUTPUT"] for r in rows))

    def test_missing_or_reused_tool_id_never_applies_unlogged_effect(self):
        for mode, expected_actions in (("missing_call_id", 0), ("duplicate_call_id", 1)):
            with self.subTest(mode=mode):
                self.out = Path(self.temp.name) / mode
                _, _, rows = self.execute(mode)
                self.assertTrue(all(r["reported_outcome"]["actions"] == expected_actions for r in rows))
                self.assertTrue(all(r["errors"] == ["INVALID_PROVIDER_TOOL_OUTPUT"] for r in rows))

    def test_default_cli_uses_no_sdk_or_provider_usage(self):
        constructor = unittest.mock.Mock(side_effect=AssertionError("SDK must not be used"))
        with patch.dict(sys.modules, {"openai": SimpleNamespace(OpenAI=constructor)}), \
             patch.dict(os.environ, {}, clear=True), \
             patch.object(sys, "argv", ["runner.py", "--output", str(self.out)]), \
             contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(runner.main(), 0)
        constructor.assert_not_called()
        summary = json.loads((self.out / "summary.json").read_text())
        self.assertIsNone(summary["estimated_provider_cost_usd"])
        self.assertIsNone(summary["provider_attempted_requests"])
        self.assertEqual(summary["safe_joint_completions"], 8)

    def test_live_cli_rejects_missing_confirmation_or_key_before_import(self):
        for flags in (["--live"], ["--live", "--confirm-live", "YES"]):
            with self.subTest(flags=flags), patch.dict(os.environ, {}, clear=True), \
                 patch.object(sys, "argv", ["runner.py", *flags]), \
                 contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as caught:
                runner.main()
            self.assertEqual(caught.exception.code, 2)

    def test_case_reserves_cannot_borrow_from_later_assignments(self):
        budget = runner.Budget(self.manifest)
        self.assertIsNone(budget.reserve("r1", "case1", Decimal("0.4")))
        budget.settle("r1", {"estimated_cost_usd": "0.3"})
        self.assertEqual(budget.reserve("r2", "case1", Decimal("0.4")), "CASE_BUDGET_CIRCUIT_BREAKER")
        self.assertIsNone(budget.reserve("r3", "case2", Decimal("0.4")))
        self.assertEqual(budget.snapshot()["estimated_exposure_usd"], "0.7")

    def test_input_reserve_outside_short_context_blocks_without_dispatch(self):
        client = FakeClient()
        with patch.object(runner, "initial_history", return_value=[{"role": "user", "content": "a" * 140000}]):
            row = runner.run_case(self.manifest["cases"][0], self.manifest["models"][0], self.manifest,
                                  True, client, Path(self.temp.name), runner.Budget(self.manifest))
        self.assertEqual(row["errors"], ["INPUT_RESERVE_OUTSIDE_PRICING_BASIS"])
        self.assertFalse(client.requests)

    def test_manifest_bytes_must_match_object_before_dispatch(self):
        client = FakeClient()
        with self.assertRaises(ValueError):
            runner.execute(self.manifest, b'{}', True, client, self.out)
        self.assertFalse(client.requests)

    def test_all_budget_blocked_assignments_are_not_model_participants(self):
        settings = {**self.manifest, "max_estimated_spend_per_case_usd": 0.000001}
        client, summary, rows = self.execute(settings=settings)
        self.assertFalse(client.requests)
        self.assertEqual(summary["assigned_records"], 8)
        self.assertEqual(summary["attempted_assignments"], 0)
        self.assertEqual(summary["estimated_provider_cost_usd"], "0")
        self.assertTrue(all(not r["scientific_model_participant"] for r in rows))

    def test_summary_cost_tampering_is_detected_after_reseal(self):
        self.execute()
        path = self.out / "summary.json"
        summary = json.loads(path.read_text())
        summary["estimated_provider_cost_usd"] = "0"
        path.write_text(runner.canonical(summary) + "\n")
        runner.seal_archive(self.out)
        with self.assertRaises(ValueError):
            runner.verify_archive(self.out)


class PricingTests(unittest.TestCase):
    def test_mixed_cache_lifetimes_are_disjoint_for_both_models(self):
        example = {"input_tokens": 12000, "output_tokens": 20,
                   "input_tokens_details": {"cached_tokens": 4000, "cache_write_tokens": 7000,
                        "cache_write_tokens_details": {"ttl_30m_tokens": 3000, "ttl_12h_tokens": 4000}},
                   "output_tokens_details": {"reasoning_tokens": 10}}
        for model, expected in (("gpt-6-astra", "0.1525"), ("gpt-6.2-astra", "0.1204")):
            result = runner.price_usage(example, manifest()["pricing"][model])
            self.assertEqual(Decimal(result["estimated_cost_usd"]), Decimal(expected))
            self.assertEqual(sum(result["categories"][k]["tokens"] for k in runner.PRICE_KEYS[:-1]), 12000)
            self.assertEqual(result["categories"]["output_per_million"]["tokens"], 20)

    def test_missing_and_malformed_usage_is_unknown_not_zero(self):
        variants = [None, {}, {**usage(), "output_tokens": True},
                    {**usage(), "input_tokens": -1}, {**usage(), "total_tokens": 0},
                    {**usage(), "input_tokens": 272001},
                    {**usage(), "input_tokens_details": {"cached_tokens": 99, "cache_write_tokens": 2}},
                    {**usage(), "input_tokens_details": {"cached_tokens": 0, "cache_write_tokens": 10}},
                    {**usage(), "input_tokens_details": {"cached_tokens": 0, "cache_write_tokens": 5,
                        "cache_write_tokens_details": {"ttl_30m_tokens": 4, "ttl_12h_tokens": 0}}}]
        for data in variants:
            with self.subTest(data=data), self.assertRaises(ValueError):
                runner.price_usage(data, manifest()["pricing"]["gpt-6-astra"])

    def test_manifest_rejects_nonfinite_limits_and_unsafe_assignments(self):
        variants = []
        for bad in (float("nan"), float("inf"), -1, 0, True):
            variants.append({**manifest(), "max_estimated_spend_usd": bad})
        variants.append({**manifest(), "max_model_calls_per_case": True})
        variants.append({**manifest(), "cases": [{**manifest()["cases"][0], "id": "../escape"}]})
        variants.append({**manifest(), "models": ["gpt-6-astra", "gpt-6-astra"]})
        variants.append({**manifest(), "cases": [manifest()["cases"][0]] * 2})
        for settings in variants:
            with self.subTest(settings=settings), self.assertRaises(ValueError):
                runner.validate_manifest(settings)


if __name__ == "__main__":
    unittest.main()
