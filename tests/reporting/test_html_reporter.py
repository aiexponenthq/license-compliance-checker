from __future__ import annotations

import unittest

from lcc.models import Component, ComponentFinding, ComponentType, LicenseEvidence, ScanReport, ScanSummary
from lcc.reporting.html_reporter import HTMLReporter


class HTMLReporterTests(unittest.TestCase):
    def test_generates_table(self) -> None:
        component = Component(type=ComponentType.JAVASCRIPT, name="lib", version="2.0.0")
        finding = ComponentFinding(
            component=component,
            evidences=[LicenseEvidence(source="clearlydefined", license_expression="Apache-2.0", confidence=0.95)],
            resolved_license="Apache-2.0",
            confidence=0.92,
        )
        summary = ScanSummary(component_count=1, violations=0)
        report = ScanReport(findings=[finding], summary=summary)

        component.metadata["assumptions"] = [{"type": "version", "value": "2.1.0", "source": "pypi"}]
        output = HTMLReporter(include_evidence=True).render(report)
        self.assertIn("<table>", output)
        self.assertIn("Apache-2.0", output)
        self.assertIn("assumed latest", output)


if __name__ == "__main__":
    unittest.main()
