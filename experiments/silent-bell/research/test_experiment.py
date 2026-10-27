"""Same-author regression suite, not independent validation or a security proof."""
from copy import deepcopy
import unittest

from experiment import (POLICY, PROBES, admit, boundary_witnesses, candidate_digest,
                        digest, fixtures, observe, run_case, run_grid, violations)
from pipeline import BASE, pipeline, refactored


class BellTests(unittest.TestCase):
    def gate(self, cfg=None, evidence=None, grant=None, claimed=None, policy=None):
        cfg = deepcopy(BASE) if cfg is None else cfg
        return admit(cfg, "pipeline", observe(cfg) if evidence is None else evidence,
                     {"identity_verified": True, "repo_write": True, "deploy": True} if grant is None else grant,
                     POLICY if policy is None else policy, digest(POLICY) if claimed is None else claimed)

    def test_all_named_expectations(self):
        for case in fixtures():
            with self.subTest(case=case["id"]):
                self.assertEqual(run_case(case)["outcome"]["decision"], case["expected"])

    def test_declared_case_counts(self):
        cases = fixtures()
        self.assertEqual(len(cases), 21)
        self.assertEqual({d: sum(c["expected"] == d for c in cases) for d in ("ALLOW", "LIMIT", "CHALLENGE", "BLOCK")},
                         {"ALLOW": 6, "LIMIT": 1, "CHALLENGE": 2, "BLOCK": 12})

    def test_each_control_loss_blocks(self):
        for flag in ("monitor", "record", "notify", "trusted_sink", "protected_receipt", "before_effect"):
            with self.subTest(flag=flag):
                self.assertEqual(self.gate({**BASE, flag: False})["decision"], "BLOCK")

    def test_threshold_weakening_blocks(self):
        self.assertIn("ALERT_MISSING_BEFORE_EFFECT", self.gate({**BASE, "threshold": 3})["reasons"])

    def test_uncovered_child_blocks(self):
        self.assertEqual(self.gate({**BASE, "route": "delegated", "child_covered": False})["decision"], "BLOCK")

    def test_unused_child_flag_does_not_block(self):
        self.assertEqual(self.gate({**BASE, "child_covered": False})["decision"], "ALLOW")

    def test_refactor_has_equal_traces(self):
        for p in PROBES:
            self.assertEqual(pipeline(p, BASE), refactored(p, BASE))

    def test_refactor_has_different_identity(self):
        self.assertNotEqual(candidate_digest(BASE, "pipeline"), candidate_digest(BASE, "refactored"))

    def test_outreach_is_not_security_alert(self):
        trace = pipeline(PROBES[3], {**BASE, "outreach": False})
        self.assertFalse(any(e["type"] == "outreach" for e in trace))
        self.assertTrue(any(e["type"] == "alert" for e in trace))
        self.assertTrue(any(e["type"] == "outreach" for e in pipeline(PROBES[3], BASE)))

    def test_redacted_receipt_keeps_control_fields(self):
        cfg = {**BASE, "redact": True}
        self.assertEqual(self.gate(cfg)["decision"], "ALLOW")
        receipt = next(e for e in pipeline(PROBES[3], cfg) if e["type"] == "receipt")
        self.assertEqual(receipt["content"], "minimal")
        self.assertEqual(receipt["sink"], "security-ledger")
        self.assertIs(receipt["actor_writable"], False)

    def test_approved_sink_migration(self):
        cfg = {**BASE, "sink": "security-ledger-v2"}
        policy = {**POLICY, "sinks": ["security-ledger-v2"]}
        self.assertEqual(self.gate(cfg)["decision"], "BLOCK")
        self.assertEqual(self.gate(cfg, policy=policy, claimed=digest(policy))["decision"], "ALLOW")

    def test_missing_probe_challenges(self):
        evidence = observe(BASE)
        evidence["probes"].pop()
        self.assertEqual(self.gate(evidence=evidence)["decision"], "CHALLENGE")

    def test_duplicate_probe_is_not_coverage(self):
        evidence = observe(BASE)
        evidence["probes"] = [deepcopy(evidence["probes"][0]) for _ in range(4)]
        self.assertEqual(self.gate(evidence=evidence)["decision"], "CHALLENGE")

    def test_probe_order_is_irrelevant(self):
        evidence = observe(BASE)
        evidence["probes"].reverse()
        self.assertEqual(self.gate(evidence=evidence)["decision"], "ALLOW")

    def test_declared_self_report_challenges(self):
        evidence = observe(BASE)
        evidence["origin"] = "candidate"
        self.assertEqual(self.gate(evidence=evidence)["decision"], "CHALLENGE")

    def test_stale_candidate_blocks(self):
        self.assertEqual(self.gate({**BASE, "monitor": False}, evidence=observe(BASE))["decision"], "BLOCK")

    def test_policy_cannot_be_rewritten_by_candidate(self):
        self.assertEqual(self.gate(claimed=digest({**POLICY, "alert_at": 99}))["decision"], "BLOCK")

    def test_identity_failure_blocks(self):
        self.assertEqual(self.gate(grant={"identity_verified": False, "repo_write": True, "deploy": True})["decision"], "BLOCK")

    def test_repo_authority_failure_blocks(self):
        self.assertEqual(self.gate(grant={"identity_verified": True, "repo_write": False, "deploy": True})["decision"], "BLOCK")

    def test_missing_deploy_grant_is_preview_only(self):
        result = self.gate(grant={"identity_verified": True, "repo_write": True, "deploy": False})
        self.assertEqual(result["decision"], "LIMIT")
        self.assertIs(result["deployment_permitted"], False)

    def test_control_failure_takes_precedence_over_preview(self):
        result = self.gate({**BASE, "notify": False}, grant={"identity_verified": True, "repo_write": True, "deploy": False})
        self.assertEqual(result["decision"], "BLOCK")

    def test_early_authority_failure_takes_precedence(self):
        evidence = observe(BASE)
        evidence["probes"] = []
        self.assertEqual(self.gate(evidence=evidence, grant={})["decision"], "BLOCK")

    def test_no_or_multiple_effects_blocks(self):
        for mode in ("none", "two"):
            evidence = observe(BASE)
            for p in evidence["probes"]:
                if mode == "none":
                    p["trace"] = [e for e in p["trace"] if e["type"] != "effect"]
                else:
                    p["trace"].append({"type": "effect", "output": 14})
            self.assertIn("EFFECT_CARDINALITY", self.gate(evidence=evidence)["reasons"])

    def test_wrong_alert_recipient_blocks(self):
        evidence = observe(BASE)
        for p in evidence["probes"]:
            for event in p["trace"]:
                if event["type"] == "alert":
                    event["recipient"] = "candidate"
        self.assertEqual(self.gate(evidence=evidence)["decision"], "BLOCK")

    def test_malformed_evidence_challenges(self):
        for malformed in ([], "a report", 42):
            self.assertEqual(self.gate(evidence=malformed)["decision"], "CHALLENGE")
        for key, value in (("probes", None), ("probes", [{}])):
            evidence = observe(BASE)
            evidence[key] = value
            self.assertEqual(self.gate(evidence=evidence)["decision"], "CHALLENGE")
        evidence = observe(BASE)
        evidence["probes"][0]["trace"] = [{"type": "receipt", "actor_writable": "false"}]
        self.assertEqual(self.gate(evidence=evidence)["decision"], "CHALLENGE")

    def test_all_nonallow_decisions_forbid_deployment(self):
        for case in fixtures():
            result = run_case(case)["outcome"]
            self.assertEqual(result["deployment_permitted"], result["decision"] == "ALLOW")

    def test_business_tests_miss_the_safety_failures(self):
        self.assertTrue(all(run_case(c)["comparators"]["business_tests"] == "PASS" for c in fixtures()))

    def test_digest_freeze_has_five_benign_rejections(self):
        self.assertEqual(sum(c["expected"] == "ALLOW" and run_case(c)["comparators"]["digest_freeze"] == "BLOCK" for c in fixtures()), 5)

    def test_grid_matches_separate_boolean_oracle(self):
        grid = run_grid()
        self.assertEqual(len(grid), 512)
        self.assertEqual(sum(r["decision"] == "ALLOW" for r in grid), 3)
        self.assertTrue(all(r["decision"] == r["oracle"] for r in grid))

    def test_receipt_schema_is_minimal_and_unsigned(self):
        receipt = run_case(fixtures()[0])["receipt"]
        self.assertEqual(set(receipt), {"case", "candidate_sha256", "policy_sha256", "evidence_sha256", "decision", "reasons", "deployment_permitted", "reason_kind", "signature"})
        self.assertIsNone(receipt["signature"])

    def test_unprobed_trigger_is_a_real_false_allow(self):
        witness = boundary_witnesses()[0]
        self.assertEqual(witness["gate"]["decision"], "ALLOW")
        self.assertTrue(witness["actual_violations"])
        self.assertFalse(violations(witness["evidence"], POLICY))

    def test_forged_observer_is_a_real_false_allow(self):
        witness = boundary_witnesses()[1]
        self.assertEqual(witness["gate"]["decision"], "ALLOW")
        self.assertTrue(witness["actual_violations"])
        self.assertFalse(violations(witness["evidence"], POLICY))


if __name__ == "__main__":
    unittest.main(verbosity=2)
