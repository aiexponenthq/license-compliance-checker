# Copyright 2025 Ajay Pundhir
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for regulatory policy templates (EU AI Act and NIST AI RMF)."""

from __future__ import annotations

import os
import tempfile
import unittest

import yaml

from lcc.config import LCCConfig
from lcc.policy import evaluate_policy
from lcc.policy.base import PolicyManager


def _load_policy_via_manager(policy_name: str) -> dict:
    """Load a bundled policy template through PolicyManager."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        os.environ["LCC_POLICY_DIR"] = tmp_dir
        try:
            config = LCCConfig()
            manager = PolicyManager(config)
            policy = manager.load_policy(policy_name)
            return policy.data
        finally:
            os.environ.pop("LCC_POLICY_DIR", None)


class TestEUAIActPolicyLoading(unittest.TestCase):
    """EU AI Act policy should load without errors and have expected structure."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.policy_data = _load_policy_via_manager("eu-ai-act-compliance")

    def test_loads_without_errors(self) -> None:
        self.assertIsInstance(self.policy_data, dict)
        self.assertEqual(self.policy_data["name"], "eu-ai-act-compliance")

    def test_has_expected_contexts(self) -> None:
        contexts = self.policy_data.get("contexts", {})
        for ctx in ("gpai", "training_data", "saas"):
            self.assertIn(ctx, contexts, f"Missing context: {ctx}")

    def test_has_disclaimer(self) -> None:
        self.assertTrue(self.policy_data.get("disclaimer"))

    def test_passes_validate_policy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            os.environ["LCC_POLICY_DIR"] = tmp_dir
            try:
                config = LCCConfig()
                manager = PolicyManager(config)
                errors = manager.validate_policy(self.policy_data)
                self.assertEqual(errors, [], f"Validation errors: {errors}")
            finally:
                os.environ.pop("LCC_POLICY_DIR", None)


class TestNISTAIRMFPolicyLoading(unittest.TestCase):
    """NIST AI RMF policy should load without errors and have expected structure."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.policy_data = _load_policy_via_manager("nist-ai-rmf")

    def test_loads_without_errors(self) -> None:
        self.assertIsInstance(self.policy_data, dict)
        self.assertEqual(self.policy_data["name"], "nist-ai-rmf")

    def test_has_expected_contexts(self) -> None:
        contexts = self.policy_data.get("contexts", {})
        for ctx in ("govern", "high_risk", "federal"):
            self.assertIn(ctx, contexts, f"Missing context: {ctx}")

    def test_has_disclaimer(self) -> None:
        self.assertTrue(self.policy_data.get("disclaimer"))

    def test_passes_validate_policy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            os.environ["LCC_POLICY_DIR"] = tmp_dir
            try:
                config = LCCConfig()
                manager = PolicyManager(config)
                errors = manager.validate_policy(self.policy_data)
                self.assertEqual(errors, [], f"Validation errors: {errors}")
            finally:
                os.environ.pop("LCC_POLICY_DIR", None)


class TestEUAIActPolicyEvaluation(unittest.TestCase):
    """Evaluate licences against the EU AI Act policy contexts."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.policy_data = _load_policy_via_manager("eu-ai-act-compliance")

    def test_gpai_denies_agpl3(self) -> None:
        decision = evaluate_policy(self.policy_data, ["AGPL-3.0"], context="gpai")
        self.assertEqual(decision.status, "violation")

    def test_gpai_allows_apache2(self) -> None:
        decision = evaluate_policy(self.policy_data, ["Apache-2.0"], context="gpai")
        self.assertEqual(decision.status, "pass")

    def test_training_data_allows_cc0(self) -> None:
        decision = evaluate_policy(self.policy_data, ["CC0-1.0"], context="training_data")
        self.assertEqual(decision.status, "pass")

    def test_gpai_allows_mit(self) -> None:
        decision = evaluate_policy(self.policy_data, ["MIT"], context="gpai")
        self.assertEqual(decision.status, "pass")

    def test_gpai_denies_sspl(self) -> None:
        decision = evaluate_policy(self.policy_data, ["SSPL-1.0"], context="gpai")
        self.assertEqual(decision.status, "violation")

    def test_saas_denies_gpl(self) -> None:
        decision = evaluate_policy(self.policy_data, ["GPL-3.0"], context="saas")
        self.assertEqual(decision.status, "violation")

    def test_training_data_allows_apache2(self) -> None:
        decision = evaluate_policy(self.policy_data, ["Apache-2.0"], context="training_data")
        self.assertEqual(decision.status, "pass")


class TestNISTAIRMFPolicyEvaluation(unittest.TestCase):
    """Evaluate licences against the NIST AI RMF policy contexts."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.policy_data = _load_policy_via_manager("nist-ai-rmf")

    def test_high_risk_denies_gpl(self) -> None:
        decision = evaluate_policy(self.policy_data, ["GPL-3.0"], context="high_risk")
        self.assertEqual(decision.status, "violation")

    def test_high_risk_denies_agpl(self) -> None:
        decision = evaluate_policy(self.policy_data, ["AGPL-3.0"], context="high_risk")
        self.assertEqual(decision.status, "violation")

    def test_high_risk_allows_mit(self) -> None:
        decision = evaluate_policy(self.policy_data, ["MIT"], context="high_risk")
        self.assertEqual(decision.status, "pass")

    def test_high_risk_allows_apache2(self) -> None:
        decision = evaluate_policy(self.policy_data, ["Apache-2.0"], context="high_risk")
        self.assertEqual(decision.status, "pass")

    def test_govern_allows_mit(self) -> None:
        decision = evaluate_policy(self.policy_data, ["MIT"], context="govern")
        self.assertEqual(decision.status, "pass")

    def test_govern_denies_sspl(self) -> None:
        decision = evaluate_policy(self.policy_data, ["SSPL-1.0"], context="govern")
        self.assertEqual(decision.status, "violation")

    def test_federal_allows_cc0(self) -> None:
        decision = evaluate_policy(self.policy_data, ["CC0-1.0"], context="federal")
        self.assertEqual(decision.status, "pass")

    def test_federal_denies_agpl(self) -> None:
        decision = evaluate_policy(self.policy_data, ["AGPL-3.0"], context="federal")
        self.assertEqual(decision.status, "violation")


class TestAPIEndpointImports(unittest.TestCase):
    """Verify the regulatory API router can be imported and has routes."""

    @classmethod
    def setUpClass(cls) -> None:
        # lcc.auth.core requires LCC_SECRET_KEY at module-import time
        os.environ.setdefault("LCC_SECRET_KEY", "test-secret-key-for-unit-tests-only")

    def test_regulatory_router_importable(self) -> None:
        from lcc.api.regulatory_routes import router
        self.assertIsNotNone(router)
        self.assertEqual(router.prefix, "/regulatory")

    def test_regulatory_router_has_routes(self) -> None:
        from lcc.api.regulatory_routes import router
        route_paths = [route.path for route in router.routes]
        self.assertTrue(
            any("/assess/" in path or "/assess" in path for path in route_paths),
            f"Expected /assess route, found: {route_paths}",
        )
        self.assertTrue(
            any("/compliance-pack/" in path or "/compliance-pack" in path for path in route_paths),
            f"Expected /compliance-pack route, found: {route_paths}",
        )

    def test_server_includes_regulatory_router(self) -> None:
        """Verify server.py mounts the regulatory router."""
        from lcc.api.server import create_app

        # Just confirm the import works; actually calling create_app()
        # would require config/redis setup, so we verify the import path
        # and that the function is callable.
        self.assertTrue(callable(create_app))

        # Verify regulatory_router is imported in server module
        import lcc.api.server as server_module
        self.assertTrue(
            hasattr(server_module, "regulatory_router"),
            "server module should import regulatory_router",
        )


if __name__ == "__main__":
    unittest.main()
