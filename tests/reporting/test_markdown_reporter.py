from __future__ import annotations

import unittest

from lcc.models import Component, ComponentFinding, ComponentType, LicenseEvidence, ScanReport, ScanSummary
from lcc.reporting.markdown_reporter import MarkdownReporter


class MarkdownReporterTests(unittest.TestCase):
    def test_renders_grouped_output(self) -> None:
        component = Component(type=ComponentType.PYTHON, name="example", version="1.0.0")
        finding = ComponentFinding(
            component=component,
            evidences=[LicenseEvidence(source="filesystem", license_expression="MIT", confidence=0.8)],
            resolved_license="MIT",
            confidence=0.9,
        )
        summary = ScanSummary(component_count=1, violations=0)
        report = ScanReport(findings=[finding], summary=summary)

        component.metadata["assumptions"] = [{"type": "version", "value": "1.2.3", "source": "npm"}]
        output = MarkdownReporter(include_evidence=True).render(report)
        self.assertIn("## Findings", output)
        self.assertIn("filesystem", output)
        self.assertIn("assumed", output)


if __name__ == "__main__":
    unittest.main()
