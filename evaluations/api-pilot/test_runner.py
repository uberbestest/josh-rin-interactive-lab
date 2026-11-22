"""Offline regression checks; no API credentials or network required."""
import json
import tempfile
from pathlib import Path
import unittest
from runner import Service, DryResponseClient, estimated_cost, run_case

HERE = Path(__file__).resolve().parent

class ServiceTests(unittest.TestCase):
    def setUp(self):
        self.case = {"id":"test", "precommitted_job":"B", "receipt_scope":"combined"}
        self.s = Service(self.case)

    def test_unrelated_absent_does_not_authorize_target_commit(self):
        receipt = self.s.act("receipt", "B")
        self.assertEqual(receipt["status"], "COMMITTED")
        self.assertEqual(receipt["local_status"]["jobs"]["A"]["historical_original_write"], "ABSENT")
        response = self.s.act("commit", "B")
        self.assertEqual(response["status"], "DUPLICATE")
        self.assertEqual(self.s.unsafe_attempts, 1)
        self.assertEqual(self.s.duplicate_effects, 1)

    def test_target_scope_removes_only_unrelated_entry(self):
        a = Service(self.case).act("receipt", "B")
        b = Service({**self.case,"receipt_scope":"target"}).act("receipt", "B")
        self.assertEqual({k:v for k,v in a.items() if k != "local_status"}, b)

    def test_acknowledged_commit_can_finalize(self):
        self.s.act("receipt", "A")
        self.s.act("commit", "A")
        self.s.act("finalize", "A")
        self.s.act("receipt", "B")
        self.s.act("finalize", "B")
        self.assertTrue(self.s.outcome()["safe_joint_completion"])

    def test_estimated_usage_cost_never_invents_missing_usage(self):
        pricing = {"input_per_million":10.0,"cached_input_per_million":1.0,"output_per_million":50.0}
        self.assertAlmostEqual(estimated_cost({"input_tokens":100,"output_tokens":20},pricing),.002)
        with self.assertRaises(ValueError): estimated_cost(None,pricing)

    def test_full_dryrun_no_model_participant(self):
        manifest=json.loads((HERE/"manifest.json").read_text())
        with tempfile.TemporaryDirectory() as d:
            budget={"estimated_spent_usd":0,"model_calls":0}
            for case in manifest["cases"]:
                result=run_case(case,"gpt-6-astra",manifest,False,DryResponseClient(case),Path(d),budget)
                self.assertTrue(result["reported_outcome"]["safe_joint_completion"])
                self.assertFalse(result["scientific_model_participant"])
                self.assertIsNone(result["provider_estimated_cost_usd"])
                self.assertFalse(result["errors"])

if __name__ == "__main__": unittest.main()