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

import logging

from lcc.models import ComponentFinding, ComponentType
from lcc.security.osv_client import OSVClient

logger = logging.getLogger(__name__)

ECOSYSTEM_MAP = {
    ComponentType.PYTHON: "PyPI",
    ComponentType.JAVASCRIPT: "npm",
    ComponentType.GO: "Go",
    ComponentType.RUST: "crates.io",
    ComponentType.RUBY: "RubyGems",
    ComponentType.PHP: "Packagist",
    ComponentType.DOTNET: "NuGet",
    ComponentType.JAVA: "Maven",
    ComponentType.GRADLE: "Maven",
}

class SecurityScanner:
    """
    Scans components for known vulnerabilities using OSV.
    """

    def __init__(self):
        self.osv_client = OSVClient()

    def scan_findings(self, findings: list[ComponentFinding]) -> int:
        """
        Enrich findings with vulnerability data.
        Returns total number of vulnerabilities found.
        """
        vuln_count = 0

        for finding in findings:
            comp = finding.component
            ecosystem = ECOSYSTEM_MAP.get(comp.type)

            if not ecosystem:
                logger.debug(f"Skipping security scan for {comp.name}: unsupported ecosystem {comp.type}")
                continue

            if not comp.version or comp.version == "*":
                logger.debug(f"Skipping security scan for {comp.name}: unknown version")
                continue

            vulns = self.osv_client.query_package(comp.name, comp.version, ecosystem)

            if vulns:
                count = len(vulns)
                logger.info(f"Found {count} vulnerabilities for {comp.name}@{comp.version}")
                vuln_count += count
                # Store in metadata
                comp.metadata.setdefault("security", {})["vulnerabilities"] = vulns

        return vuln_count
