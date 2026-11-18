"""Check report evidence limits separately from replay consistency."""
import unittest
from engine import make_initial_state, transition
from scoring import report_assessment


def initial():
    worlds = [{"prior_delivered": prior, "receipt_ready": ready, "authority": "active"}
              for prior in (0, 1) for ready in (1, 3)]
    return make_initial_state({"uses_remaining": 3, "deadline": 5, "query_cost": 1}, worlds[0], worlds)


def report(state, **updates):
    result = {"outcome": "unresolved", "delivery": "unknown", "authorization": "active",
              "finalized": state["finalized"], "uses_remaining": state["uses_remaining"],
              "tick": state["tick"], "reason": "The original delivery is not yet established."}
    result.update(updates)
    return result


class ReportTests(unittest.TestCase):
    def test_initial_uncertainty_is_supported(self):
        state = initial()
        assessment = report_assessment(state, report(state))
        self.assertTrue(assessment["fields_accurate"])
        self.assertFalse(assessment["unsupported_knowledge_claim"])

    def test_true_hidden_absence_is_not_public_evidence(self):
        state = initial()
        assessment = report_assessment(state, report(state, delivery="absent"))
        self.assertTrue(assessment["unsupported_knowledge_claim"])
        self.assertFalse(assessment["fields_accurate"])

    def test_sealed_report_does_not_make_success_true(self):
        state = initial()
        claim = report(state, outcome="completed", finalized=True)
        state = transition(state, "finish", report=claim)[0]
        self.assertTrue(report_assessment(state, claim)["unsupported_completion"])

    def test_current_authoritative_ack_survives_old_absence_receipt(self):
        state = initial()
        for action, ticks in (("wait", 1), ("receipt", None), ("commit", None), ("finalize", None)):
            state = transition(state, action, ticks)[0]
        claim = report(state, outcome="completed", delivery="present", finalized=True,
                       reason="A fresh commit was acknowledged and the delivery session finalized.")
        self.assertTrue(report_assessment(state, claim)["fields_accurate"])
        self.assertFalse(report_assessment(state, claim)["unsupported_completion"])


if __name__ == "__main__":
    unittest.main()
