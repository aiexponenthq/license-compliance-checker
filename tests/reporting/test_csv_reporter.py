from __future__ import annotations

import csv
import io
import unittest

from lcc.models import Component, ComponentFinding, ComponentType, LicenseEvidence, ScanReport, ScanSummary
from lcc.reporting.csv_reporter import CSVReporter


class CSVReporterTests(unittest.TestCase):
    def test_renders_csv_output(self) -> None:
        component = Component(type=ComponentType.PYTHON, name="example", version="*")
        component.metadata["assumptions"] = [{"type": "version", "value": "1.0.0", "source": "pypi"}]
        component.metadata["project_root"] = "/tmp/project"
        finding = ComponentFinding(
            component=component,
            evidences=[LicenseEvidence(source="pypi", license_expression="MIT", confidence=0.9, raw_data={})],
            resolved_license="MIT",
            confidence=0.9,
        )
        summary = ScanSummary(component_count=1, violations=0)
        report = ScanReport(findings=[finding], summary=summary)

        payload = CSVReporter(include_evidence=True).render(report)
        reader = csv.reader(io.StringIO(payload))
        rows = list(reader)
        self.assertEqual(rows[0][0], "component_type")
        self.assertIn("MIT", rows[1])
        self.assertIn("pypi", rows[1])


if __name__ == "__main__":
    unittest.main()
