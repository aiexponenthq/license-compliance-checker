from __future__ import annotations

import unittest

from rich.console import Console

from lcc.models import Component, ComponentFinding, ComponentType, ScanReport, ScanSummary
from lcc.reporting.console_reporter import ConsoleReporter


class ConsoleReporterTests(unittest.TestCase):
    def test_highlights_violations_below_threshold(self) -> None:
        component = Component(type=ComponentType.PYTHON, name="example", version="1.0.0")
        finding = ComponentFinding(component=component, resolved_license="MIT", confidence=0.4)
        summary = ScanSummary(component_count=1, violations=1, duration_seconds=0.1, context={})
        report = ScanReport(findings=[finding], summary=summary, errors=[])

        console = Console(record=True)
        reporter = ConsoleReporter(console=console, threshold=0.8)
        reporter.write(report)

        output = console.export_text()
        self.assertIn("FAIL", output)
        self.assertIn("MIT", output)

    def test_displays_assumed_version(self) -> None:
        component = Component(type=ComponentType.PYTHON, name="pkg", version="*")
        component.metadata["assumptions"] = [{"type": "version", "value": "2.0.0", "source": "pypi"}]
        finding = ComponentFinding(component=component, resolved_license="Apache-2.0", confidence=0.9)
        summary = ScanSummary(component_count=1, violations=0, duration_seconds=0.1, context={})
        report = ScanReport(findings=[finding], summary=summary, errors=[])

        console = Console(record=True)
        reporter = ConsoleReporter(console=console, threshold=0.5)
        reporter.write(report)

        output = console.export_text()
        self.assertIn("(~2.0.0 assumed)", output)
        self.assertIn("assumed latest", output)


if __name__ == "__main__":
    unittest.main()
