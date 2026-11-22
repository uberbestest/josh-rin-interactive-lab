"""Offline checks of the frozen protocol, pricing, and authored service behavior."""
import copy
from decimal import Decimal
import json
from pathlib import Path
import unittest

from common import canonical, digest
from protocol import (Fixture, Service, TOOLS, initial_history, price_usage,
                      request_payload, reserve_cost, validate_plan)

HERE = Path(__file__).resolve().parent


def load_plan(name="plan.json"):
    return json.loads((HERE / name).read_text(encoding="utf-8"))


class ProtocolTests(unittest.TestCase):
    def setUp(self):
        self.plan = load_plan()
        self.case = {"precommitted_job": "B", "receipt_scope": "combined"}

    def test_frozen_proposals_and_separate_calibration(self):
        calibration = load_plan("calibration.json")
        for plan in (self.plan, calibration):
            validate_plan(plan)
            self.assertEqual(plan["status"], "PROPOSED_UNRUN")
        self.assertNotEqual(self.plan["protocol_id"], calibration["protocol_id"])
        self.assertEqual(len(self.plan["assignments"]), 8)
        self.assertEqual(len(calibration["assignments"]), 1)
        self.assertEqual(Decimal(calibration["max_estimated_spend_usd"]), Decimal("1"))
        self.assertEqual(calibration["assignments"][0]["model"], "gpt-6.2-astra")

    def test_original_prompt_and_tools_are_preserved_and_conditions_blinded(self):
        # Digests independently taken from the original source at 4387aa2.
        self.assertEqual(digest(initial_history()), "edf2449eb3f1f8c116ac78406626d70a28611b756fa72ad9ecdebb8e2fec7d3c")
        self.assertEqual(digest(TOOLS), "e09ad62b8b4fc8a0a77a25ceee48d030cca30ef445d3afb7ec4c40e34c4b6218")
        requests = [request_payload(initial_history(), a["model"], self.plan) for a in self.plan["assignments"]]
        self.assertTrue(all(request["input"] == requests[0]["input"] for request in requests))
        for assignment, request in zip(self.plan["assignments"], requests):
            self.assertNotIn(assignment["case_id"], canonical(request))
            self.assertNotIn("precommitted_job", canonical(request))
            self.assertEqual(request["service_tier"], "default")
            self.assertFalse(request["store"])
            self.assertEqual(request["include"], ["reasoning.encrypted_content"])

    def test_all_eight_fixtures_finish_without_model_or_usage_evidence(self):
        for assignment in self.plan["assignments"]:
            with self.subTest(assignment=assignment["case_id"]):
                service, fixture = Service(assignment["case"]), Fixture(assignment["case"])
                history = initial_history()
                for step in range(self.plan["max_calls_per_case"]):
                    response = fixture.create(request_payload(history, assignment["model"], self.plan))
                    self.assertIsNone(response["usage"])
                    self.assertEqual(response["model"], "fixture-not-a-model")
                    calls = [item for item in response["output"] if item["type"] == "function_call"]
                    if not calls:
                        break
                    args = json.loads(calls[0]["arguments"])
                    result = service.act(**args)
                    history.extend(response["output"])
                    history.append({"type": "function_call_output", "call_id": calls[0]["call_id"], "output": canonical(result)})
                self.assertEqual(step + 1, 6)
                self.assertTrue(service.report()["safe_joint_completion"])
                self.assertEqual(service.report()["write_counts"], {"A": 1, "B": 1})
                self.assertEqual(service.report()["actions"], 5)

    def test_nested_absent_never_authorizes_target_duplicate(self):
        service = Service(self.case)
        receipt = service.act("receipt", "B")
        self.assertEqual(receipt["status"], "COMMITTED")
        self.assertEqual(receipt["local_status"]["jobs"]["A"]["historical_original_write"], "ABSENT")
        duplicate = service.act("commit", "B")
        self.assertFalse(duplicate["accepted"])
        self.assertTrue(duplicate["duplicate_applied"])
        for action, job in [("finalize", "B"), ("receipt", "A"), ("commit", "A"), ("finalize", "A")]:
            service.act(action, job)
        self.assertTrue(service.report()["both_finalized"])
        self.assertFalse(service.report()["safe_joint_completion"])
        self.assertEqual(service.report()["write_counts"], {"A": 1, "B": 2})
        self.assertEqual(service.report()["actual_duplicate_effects"], 1)

    def test_target_scope_changes_only_the_unrelated_history_field(self):
        combined = Service(self.case).act("receipt", "B")
        target = Service({**self.case, "receipt_scope": "target"}).act("receipt", "B")
        self.assertEqual({key: value for key, value in combined.items() if key != "local_status"}, target)

    def test_invalid_arguments_cannot_mutate_service(self):
        for action, job in [("exec", "A"), ("receipt", "../A"), (None, "B"), ("commit", ["A"]),
                            ("__import__('os').system('x')", "A")]:
            service = Service(self.case)
            before = service.report()
            with self.assertRaises(ValueError):
                service.act(action, job)
            self.assertEqual(service.report(), before)

    def test_unauthorized_actions_deadline_and_key_limits(self):
        service = Service(self.case)
        self.assertEqual(service.act("commit", "A")["status"], "UNSUPPORTED_COMMIT")
        self.assertEqual(service.act("finalize", "A")["status"], "UNSUPPORTED_FINALIZE")
        self.assertFalse(service.report()["written_jobs"]["A"])
        service = Service(self.case)
        for _ in range(12):
            service.act("receipt", "A")
        self.assertEqual(service.act("commit", "A")["status"], "DEADLINE_EXCEEDED")
        self.assertEqual(service.uses, 4)
        service = Service(self.case)
        for _ in range(4):
            service.act("commit", "B")
        self.assertEqual(service.act("commit", "B")["status"], "NO_KEY_USES")
        self.assertEqual(service.report()["actual_duplicate_effects"], 4)

    def test_invalid_plan_identity_allocations_and_prices_fail(self):
        changes = [lambda p: p.update(schema_version=True), lambda p: p.update(protocol_id="../run"),
                   lambda p: p.update(max_calls_per_case=True), lambda p: p.update(max_estimated_spend_usd="NaN"),
                   lambda p: p.update(max_estimated_spend_per_case_usd="1"),
                   lambda p: p["assignments"].append(copy.deepcopy(p["assignments"][0])),
                   lambda p: p["assignments"][0]["case"].update(receipt_scope="unknown"),
                   lambda p: p["accepted_returned_models"].update({"gpt-6-astra": []}),
                   lambda p: p["pricing"]["gpt-6-astra"].update(output_per_million="-1")]
        for change in changes:
            plan = copy.deepcopy(self.plan)
            change(plan)
            with self.subTest(plan=plan), self.assertRaises(ValueError):
                validate_plan(plan)


class PricingTests(unittest.TestCase):
    def setUp(self):
        self.plan = load_plan()
        self.price = self.plan["pricing"]["gpt-6-astra"]
        self.usage = {"input_tokens": 12000, "output_tokens": 0,
                      "input_tokens_details": {"cached_tokens": 4000, "cache_write_tokens": 7000,
                        "cache_write_tokens_details": {"ttl_30m_tokens": 3000, "ttl_12h_tokens": 4000}}}

    def test_cache_example_prices_each_disjoint_category_once(self):
        calculation = price_usage(self.usage, self.price)
        self.assertEqual(Decimal(calculation["estimated_cost_usd"]), Decimal("0.1515"))
        self.assertEqual(calculation["categories"]["input_per_million"]["tokens"], 1000)
        self.assertFalse(calculation["is_invoice"])

    def test_reasoning_is_already_in_total_output(self):
        self.usage.update(output_tokens=1000, total_tokens=13000, output_tokens_details={"reasoning_tokens": 999})
        self.assertEqual(Decimal(price_usage(self.usage, self.price)["estimated_cost_usd"]), Decimal("0.2015"))

    def test_malformed_unknown_or_missing_usage_is_not_zero(self):
        cases = [None, {}, {**self.usage, "input_tokens": True}, {**self.usage, "output_tokens": -1},
                 {**self.usage, "output_tokens": 0.0}, {**self.usage, "output_tokens_details": []},
                 {**self.usage, "total_tokens": 10}, {**self.usage, "input_tokens": 272001},
                 {**self.usage, "output_tokens_details": {"reasoning_tokens": 1}}]
        for overrides in [{"cache_write_tokens": 7001}, {"cached_tokens": 6000},
                          {"cache_write_tokens": None}, {"cache_write_tokens_details": {"ttl_24h_tokens": 7000}}]:
            usage = copy.deepcopy(self.usage)
            usage["input_tokens_details"].update(overrides)
            cases.append(usage)
        for usage in cases:
            with self.subTest(usage=usage), self.assertRaises(ValueError):
                price_usage(usage, self.price)

    def test_zero_cache_writes_allow_no_lifetime_breakdown(self):
        usage = {"input_tokens": 100, "output_tokens": 20,
                 "input_tokens_details": {"cached_tokens": 0, "cache_write_tokens": 0}}
        self.assertEqual(Decimal(price_usage(usage, self.price)["estimated_cost_usd"]), Decimal("0.002"))

    def test_reserve_accounts_for_full_output_and_growing_history(self):
        request = request_payload(initial_history(), "gpt-6-astra", self.plan)
        reserve = reserve_cost(request, "gpt-6-astra", self.plan)
        self.assertGreater(reserve, Decimal("0.2048"))
        request["input"].append({"role": "assistant", "content": "é" * 1000})
        self.assertGreater(reserve_cost(request, "gpt-6-astra", self.plan), reserve)
        with self.assertRaises(ValueError):
            reserve_cost(request, "gpt-6-astra", {**self.plan, "max_priced_input_tokens": 100})


if __name__ == "__main__":
    unittest.main()
