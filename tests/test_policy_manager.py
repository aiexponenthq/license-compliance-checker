from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from lcc.config import LCCConfig
from lcc.policy import PolicyDecision, PolicyManager, evaluate_policy


class PolicyManagerTests(unittest.TestCase):
    def test_create_and_apply_policy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            os.environ["LCC_POLICY_DIR"] = tmp_dir
            config = LCCConfig()
            manager = PolicyManager(config)
            policy_data = {
                "name": "perm",
                "disclaimer": "Test disclaimer",
                "default_context": "internal",
                "contexts": {
                    "internal": {
                        "allow": ["MIT"],
                        "deny": ["GPL-*"] ,
                        "deny_reasons": {"GPL-*": "GPL family requires legal approval."},
                        "dual_license_preference": "most_permissive",
                    }
                },
            }
            manager.save_policy("perm", policy_data)
            manager.set_active_policy("perm")
            self.assertEqual(manager.active_policy(), "perm")
            decision = evaluate_policy(policy_data, ["GPL-3.0", "MIT"], context="internal")
            self.assertIsInstance(decision, PolicyDecision)
            self.assertEqual(decision.status, "violation")
            self.assertIn("GPL", " ".join(decision.reasons))
            self.assertEqual(decision.chosen_license, "MIT")
        os.environ.pop("LCC_POLICY_DIR", None)


if __name__ == "__main__":
    unittest.main()
