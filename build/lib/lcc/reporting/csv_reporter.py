"""
CSV report renderer.
"""

from __future__ import annotations

import csv
import io
from typing import Iterable, Sequence

from lcc.models import ComponentFinding, ScanReport


class CSVReporter:
    """
    Serialises scan findings into CSV format.
    """

    def __init__(self, include_evidence: bool = False) -> None:
        self.include_evidence = include_evidence

    def render(self, report: ScanReport) -> str:
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        base_headers = [
            "component_type",
            "component_name",
            "component_version",
            "assumed_version",
            "license",
            "confidence",
            "policy_status",
            "project_root",
        ]
        headers = list(base_headers)
        if self.include_evidence:
            headers.extend(["evidence_source", "evidence_license", "evidence_confidence", "evidence_url"])
        writer.writerow(headers)

        for finding in report.findings:
            row_prefix = self._base_row(finding)
            evidences = finding.evidences if self.include_evidence else [None]
            for evidence in evidences:
                row = list(row_prefix)
                if self.include_evidence and evidence is not None:
                    row.extend(
                        [
                            evidence.source,
                            evidence.license_expression,
                            f"{evidence.confidence:.2f}",
                            evidence.url or "",
                        ]
                    )
                writer.writerow(row)

        return buffer.getvalue()

    def _base_row(self, finding: ComponentFinding) -> Sequence[str]:
        component = finding.component
        metadata = component.metadata if isinstance(component.metadata, dict) else {}
        assumptions = metadata.get("assumptions", [])
        assumed_version = ""
        for assumption in assumptions or []:
            if assumption.get("type") == "version":
                assumed_version = assumption.get("value", "")
                break
        policy_status = metadata.get("policy", {}).get("status") if isinstance(metadata.get("policy"), dict) else None
        project_root = metadata.get("project_root", "")
        return [
            component.type.value,
            component.name,
            component.version or "",
            assumed_version,
            finding.resolved_license or "UNKNOWN",
            f"{finding.confidence:.2f}",
            policy_status or "",
            project_root,
        ]

