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

from collections import defaultdict

from lcc.config import load_config
from lcc.models import ComponentFinding, ScanReport
from lcc.resolution.license_loader import LicenseLoader


class AttributionReporter:
    """
    Generates a consolidated Attribution / NOTICE file.
    Groups components by license and includes the license text.
    """

    def render(self, report: ScanReport) -> str:
        """Render the attribution report."""

        # 0. Initialize Loader
        config = load_config()
        # Ensure config.cache_dir is a Path object or passed correctly if LicenseLoader expects it.
        # LicenseLoader expects Optional[Path]. config.cache_dir is likely a Path.
        loader = LicenseLoader(cache_dir=config.cache_dir)

        # 1. Group components by license
        by_license: dict[str, list[ComponentFinding]] = defaultdict(list)

        for finding in report.findings:
            license_id = finding.resolved_license or "UNKNOWN"
            by_license[license_id].append(finding)

        # 2. Sort licenses alphabetically
        sorted_licenses = sorted(by_license.keys())

        # 3. Build Output
        lines = []
        lines.append("OPEN SOURCE SOFTWARE NOTICE")
        lines.append("=" * 30)
        lines.append("")
        lines.append("This software includes external components subject to the following")
        lines.append("license terms:")
        lines.append("")

        # Table of Contents
        lines.append("List of Components:")
        lines.append("-" * 20)
        for license_id in sorted_licenses:
            findings = by_license[license_id]
            for f in findings:
                comp = f.component
                lines.append(f"  * {comp.name} {comp.version} ({license_id})")
        lines.append("")
        lines.append("=" * 60)
        lines.append("")

        # License Details
        for license_id in sorted_licenses:
            findings = by_license[license_id]
            lines.append(f"License: {license_id}")
            lines.append("-" * (9 + len(license_id)))
            lines.append("")
            lines.append("Used by:")
            for f in findings:
                comp = f.component
                lines.append(f"  * {comp.name} {comp.version}")

            lines.append("")
            lines.append("Terms:")

            # Fetch text
            text = loader.get_license_text(license_id)
            if text:
                lines.append(text)
            else:
                lines.append(f"[Full text for {license_id} not available in local cache or upstream]")
                lines.append("Please see component source for full license details.")

            lines.append("")
            lines.append("*" * 60)
            lines.append("")

        return "\n".join(lines)
