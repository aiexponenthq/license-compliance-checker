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

"""
High-level orchestration for running scans.
"""

from __future__ import annotations

import time
from collections.abc import Callable, Iterable
from pathlib import Path

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
        progress_callback: Callable[[str, str, int, int], None] | None = None,
        check_vulnerabilities: bool = False,
    ) -> ScanReport:
        start = time.time()
        findings: list[ComponentFinding] = []
        for index, detector in enumerate(self.detectors, start=1):
            # Pass config to detector for exclusion pattern checking
            detector.set_config(self.config)
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

        # Security Scan
        vuln_count = 0
        if check_vulnerabilities:
            from lcc.security.scanner import SecurityScanner
            security_scanner = SecurityScanner()
            if progress_callback:
                progress_callback("security", "OSV", 1, 1)
            vuln_count = security_scanner.scan_findings(findings)

        summary = ScanSummary(
            component_count=len(findings),
            violations=0,
            duration_seconds=time.time() - start,
            context={
                "detectors": [detector.name for detector in self.detectors],
                "resolvers": [resolver.name for resolver in self.resolvers],
                "resolved": resolved,
                "vulnerabilities": vuln_count,
            },
        )

        return ScanReport(findings=findings, summary=summary, errors=[])
