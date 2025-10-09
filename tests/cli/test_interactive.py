from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from rich.console import Console

from lcc.cli.main import interactive_session
from lcc.models import Component, ComponentFinding, ComponentType, LicenseEvidence, ScanReport, ScanSummary


class InteractiveSessionTests(unittest.TestCase):
    def _sample_report(self) -> ScanReport:
        component1 = Component(type=ComponentType.PYTHON, name="pkgA", version="*")
        component1.metadata.update(
            {
                "assumptions": [{"type": "version", "value": "1.2.3", "source": "pypi"}],
                "project_root": "/tmp/project",
                "policy": {"status": "warning"},
            }
        )
        finding1 = ComponentFinding(
            component=component1,
            resolved_license="MIT",
            confidence=0.8,
            evidences=[LicenseEvidence(source="pypi", license_expression="MIT", confidence=0.8, raw_data={})],
        )

        component2 = Component(type=ComponentType.PYTHON, name="pkgB", version="*")
        component2.metadata["project_root"] = "/tmp/project"
        finding2 = ComponentFinding(component=component2, resolved_license="UNKNOWN", confidence=0.2)

        summary = ScanSummary(component_count=2, violations=1)
        return ScanReport(findings=[finding1, finding2], summary=summary)

    def test_interactive_commands_export(self) -> None:
        report = self._sample_report()
        console = Console(record=True)
        with tempfile.TemporaryDirectory() as tmp_dir:
            commands = [
                "summary",
                "list",
                "show 1",
                "filter license MIT",
                "export csv results.csv",
                "quit",
            ]
            interactive_session(console, report, commands=commands, output_dir=Path(tmp_dir))
            output = console.export_text()
            self.assertIn("Summary", output)
            self.assertIn("Components", output)
            exported = Path(tmp_dir) / "results.csv"
            self.assertTrue(exported.exists())


if __name__ == "__main__":
    unittest.main()
