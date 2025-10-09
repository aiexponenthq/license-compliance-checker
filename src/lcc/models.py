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
Domain models shared across License Compliance Checker modules.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Any


class ComponentType(StrEnum):
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    GO = "go"
    JAVA = "java"
    GRADLE = "gradle"
    RUST = "rust"
    RUBY = "ruby"
    DOTNET = "dotnet"
    PHP = "php"
    AI_MODEL = "ai_model"
    DATASET = "dataset"
    GENERIC = "generic"


@dataclass(slots=True)
class Component:
    """
    Represents a single software component discovered during scanning.
    """

    type: ComponentType
    name: str
    version: str
    namespace: str | None = None
    path: Path | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class LicenseEvidence:
    """
    Evidence item returned from a data source or detector.
    """

    source: str
    license_expression: str
    confidence: float
    raw_data: dict[str, Any] = field(default_factory=dict)
    url: str | None = None


@dataclass(slots=True)
class ComponentFinding:
    """
    Aggregated result for a component after running the resolution chain.
    """

    component: Component
    evidences: list[LicenseEvidence] = field(default_factory=list)
    resolved_license: str | None = None
    confidence: float = 0.0


@dataclass(slots=True)
class ScanSummary:
    """
    Summary statistics for a scan run.
    """

    component_count: int
    violations: int
    generated_at: datetime = field(default_factory=datetime.utcnow)
    duration_seconds: float = 0.0
    context: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ScanReport:
    """
    Complete scan output consumed by reporters and the CLI.
    """

    findings: list[ComponentFinding]
    summary: ScanSummary
    errors: list[str] = field(default_factory=list)


class Status(StrEnum):
    """Component compliance status."""

    PASS = "pass"
    WARNING = "warning"
    VIOLATION = "violation"
    ERROR = "error"


@dataclass(slots=True)
class ComponentResult:
    """
    Component result with policy evaluation status.
    Used by SBOM generators and API.
    """

    component: Component
    status: Status
    licenses: list[LicenseEvidence] = field(default_factory=list)
    violations: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ScanResult:
    """
    Scan result with all components and their evaluation results.
    Used by SBOM generators and API.
    """

    components: list[Component]
    component_results: list[ComponentResult]
    scan_id: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
