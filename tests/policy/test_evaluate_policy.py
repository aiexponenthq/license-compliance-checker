from __future__ import annotations

import unittest

from lcc.policy import PolicyDecision, evaluate_policy


def make_policy() -> dict:
    return {
        "name": "test",
        "disclaimer": "Test policy.",
        "default_context": "internal",
        "contexts": {
            "internal": {
                "allow": ["MIT", "Apache-2.0", "BSD-*"] ,
                "deny": ["SSPL-1.0"],
                "dual_license_preference": "most_permissive",
                "deny_reasons": {"SSPL-1.0": "SSPL not permitted."},
            },
            "saas": {
                "allow": ["MIT", "Apache-2.0", "GPL-3.0"],
                "deny": [],
                "review": [],
                "dual_license_preference": "avoid_copyleft",
            },
        },
    }


class EvaluatePolicyTests(unittest.TestCase):
    def test_denied_license_records_reason(self) -> None:
        policy = make_policy()
        decision = evaluate_policy(policy, ["SSPL-1.0"], context="internal")
        self.assertIsInstance(decision, PolicyDecision)
        self.assertEqual(decision.status, "violation")
        self.assertIn("SSPL", " ".join(decision.reasons))
        self.assertEqual(decision.alternatives[0].disposition, "deny")

    def test_dual_license_preference_avoids_copyleft(self) -> None:
        policy = make_policy()
        decision = evaluate_policy(policy, ["GPL-3.0", "MIT"], context="saas")
        self.assertEqual(decision.status, "pass")
        self.assertEqual(decision.chosen_license, "MIT")

    def test_component_override_short_circuits(self) -> None:
        policy = make_policy()
        policy["contexts"]["internal"]["overrides"] = {
            "demo": {
                "decision": "warning",
                "license": "GPL-3.0",
                "reason": "Approved by legal",
                "explanation": "Override demo component",
            }
        }
        decision = evaluate_policy(policy, ["MIT"], context="internal", component_name="demo")
        self.assertEqual(decision.status, "warning")
        self.assertEqual(decision.override, "component")
        self.assertIn("Approved", " ".join(decision.reasons))

    def test_unknown_license_with_allowlist_prompts_review(self) -> None:
        policy = make_policy()
        decision = evaluate_policy(policy, ["Custom-License"], context="internal")
        self.assertEqual(decision.status, "warning")
        self.assertEqual(decision.alternatives[0].disposition, "review")


if __name__ == "__main__":
    unittest.main()
