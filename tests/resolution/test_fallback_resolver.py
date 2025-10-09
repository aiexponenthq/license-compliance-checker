from __future__ import annotations

import unittest

from lcc.models import Component, ComponentFinding, ComponentType, LicenseEvidence
from lcc.resolution.base import Resolver
from lcc.resolution.fallback import FallbackResolver


class _FakeResolver(Resolver):
    def __init__(self, name: str, evidences: list[LicenseEvidence]) -> None:
        super().__init__(name=name)
        self._evidences = evidences

    def resolve(self, component: Component):
        return list(self._evidences)


class FallbackResolverTests(unittest.TestCase):
    def test_selects_highest_confidence(self) -> None:
        component = Component(type=ComponentType.PYTHON, name="example", version="1.0.0")
        finding = ComponentFinding(component=component)

        resolver_high = _FakeResolver(
            "high",
            [LicenseEvidence(source="sourceA", license_expression="MIT", confidence=0.9, raw_data={})],
        )
        resolver_low = _FakeResolver(
            "low",
            [LicenseEvidence(source="sourceB", license_expression="Apache-2.0", confidence=0.5, raw_data={})],
        )
        fallback = FallbackResolver([resolver_low, resolver_high])
        fallback.resolve(finding)

        self.assertEqual(finding.resolved_license, "MIT")
        self.assertAlmostEqual(finding.confidence, 0.9)
        self.assertEqual(len(finding.evidences), 2)


if __name__ == "__main__":
    unittest.main()
