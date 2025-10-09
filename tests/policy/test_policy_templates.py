from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from lcc.config import LCCConfig
from lcc.policy.base import PolicyManager


class PolicyTemplateTests(unittest.TestCase):
    def test_templates_are_seeded(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            os.environ["LCC_POLICY_DIR"] = tmp_dir
            config = LCCConfig()
            manager = PolicyManager(config)
            templates = manager.list_policies()
            self.assertIn("permissive", templates)
            policy = manager.load_policy("permissive")
            contexts = policy.data.get("contexts", {})
            self.assertIn("internal", contexts)
            internal = contexts["internal"]
            self.assertIn("allow", internal)
            self.assertIn("MIT", internal["allow"])
            self.assertTrue(policy.data.get("disclaimer"))
        os.environ.pop("LCC_POLICY_DIR", None)


if __name__ == "__main__":
    unittest.main()
