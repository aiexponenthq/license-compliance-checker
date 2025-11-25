"""
High-level orchestration for running scans.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Callable, Iterable, List, Optional

from lcc.config import LCCConfig
from lcc.detection.base import Detector
from lcc.models import ComponentFinding, ScanReport, ScanSummary
from lcc.resolution.base import Resolver
from lcc.resolution.fallback import FallbackResolver


class Scanner:
    """
    Coordinates detectors and resolvers to produce a ScanReport.
    """

    def __init__(self, detectors: Iterable[Detector], resolvers: Iterable[Resolver], config: LCCConfig):
        self.detectors = list(detectors)
        self.resolvers = list(resolvers)
        self.config = config

    def scan(
        self,
        project_root: Path,
        progress_callback: Optional[Callable[[str, str, int, int], None]] = None,
    ) -> ScanReport:
        start = time.time()
        findings: List[ComponentFinding] = []
        for index, detector in enumerate(self.detectors, start=1):
            if not detector.supports(project_root):
                continue
            for component in detector.discover(project_root):
                component.metadata.setdefault("project_root", str(project_root))
                findings.append(ComponentFinding(component=component))
            if progress_callback:
                progress_callback("detector", detector.name, index, len(self.detectors))

        fallback = FallbackResolver(self.resolvers)
        for index, finding in enumerate(findings, start=1):
            fallback.resolve(finding)
            if progress_callback:
                progress_callback("resolver", finding.component.name, index, len(findings))

        resolved = sum(1 for finding in findings if finding.resolved_license)

        summary = ScanSummary(
            component_count=len(findings),
            violations=0,
            duration_seconds=time.time() - start,
            context={
                "detectors": [detector.name for detector in self.detectors],
                "resolvers": [resolver.name for resolver in self.resolvers],
                "resolved": resolved,
            },
        )

        return ScanReport(findings=findings, summary=summary, errors=[])
