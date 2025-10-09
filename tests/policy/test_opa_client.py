from __future__ import annotations

import json
import unittest
from pathlib import Path

import responses

from lcc.config import LCCConfig
from lcc.models import Component, ComponentFinding, ComponentType
from lcc.policy.opa_client import OPAClient, OPAClientError


class OPAClientTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = LCCConfig()
        self.config.opa_url = "https://opa.test"
        self.config.timeouts["opa"] = 1

    @responses.activate
    def test_evaluate_success(self) -> None:
        responses.add(
            responses.POST,
            "https://opa.test/v1/data/lcc/license/decision",
            json={"result": {"status": "pass"}},
            status=200,
        )
        client = OPAClient(self.config)
        component = Component(type=ComponentType.PYTHON, name="demo", version="1.0.0")
        finding = ComponentFinding(component=component, resolved_license="MIT", confidence=0.9)
        result = client.evaluate(
            finding,
            policy_name="permissive",
            context="saas",
            licenses=["MIT", "GPL-2.0"],
        )
        self.assertEqual(result["status"], "pass")
        payload = json.loads(responses.calls[0].request.body)
        self.assertEqual(payload["input"]["license"], "MIT")
        self.assertEqual(payload["input"]["context"], "saas")
        self.assertEqual(payload["input"]["license_options"], ["MIT", "GPL-2.0"])

    @responses.activate
    def test_evaluate_error(self) -> None:
        responses.add(
            responses.POST,
            "https://opa.test/v1/data/lcc/license/decision",
            json={},
            status=500,
        )
        client = OPAClient(self.config)
        component = Component(type=ComponentType.PYTHON, name="demo", version="1.0.0")
        finding = ComponentFinding(component=component, resolved_license="MIT", confidence=0.9)
        with self.assertRaises(OPAClientError):
            client.evaluate(finding)


if __name__ == "__main__":
    unittest.main()
