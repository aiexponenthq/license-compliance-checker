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
JSON reporter.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any

from lcc.models import (
    Component,
    ComponentResult,
    ComponentType,
    LicenseEvidence,
    ScanReport,
    ScanResult,
    Status,
)
from lcc.reporting.base import Reporter


class JSONReporter(Reporter):
    """
    Serializes the ScanReport to JSON, preserving dataclass structure.
    """

    def render(self, report: ScanReport) -> str:
        return json.dumps(asdict(report), indent=2, sort_keys=True, default=str)


def deserialize_scan_result(data: dict[str, Any]) -> ScanResult:
    """
    Deserialize a ScanResult from JSON data.

    Args:
        data: Dictionary from JSON

    Returns:
        ScanResult object
    """
    # Deserialize components
    components = []
    for comp_data in data.get("components", []):
        comp = Component(
            type=ComponentType(comp_data["type"]),
            name=comp_data["name"],
            version=comp_data["version"],
            namespace=comp_data.get("namespace"),
            path=Path(comp_data["path"]) if comp_data.get("path") else None,
            metadata=comp_data.get("metadata", {}),
        )
        components.append(comp)

    # Deserialize component results
    component_results = []
    for cr_data in data.get("component_results", []):
        # Find matching component
        component = next(
            (
                c
                for c in components
                if c.name == cr_data["component"]["name"]
                and c.version == cr_data["component"]["version"]
            ),
            None,
        )

        if not component:
            continue

        # Deserialize license evidence
        licenses = []
        for lic_data in cr_data.get("licenses", []):
            lic = LicenseEvidence(
                source=lic_data["source"],
                license_expression=lic_data["license_expression"],
                confidence=lic_data["confidence"],
                raw_data=lic_data.get("raw_data", {}),
            )
            licenses.append(lic)

        cr = ComponentResult(
            component=component,
            status=Status(cr_data["status"]),
            licenses=licenses,
            violations=cr_data.get("violations", []),
            warnings=cr_data.get("warnings", []),
        )
        component_results.append(cr)

    # Create ScanResult
    scan_result = ScanResult(
        components=components,
        component_results=component_results,
        scan_id=data.get("scan_id", "unknown"),
        timestamp=datetime.fromisoformat(data["timestamp"])
        if "timestamp" in data
        else datetime.now(),
    )

    return scan_result

