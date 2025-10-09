"""
Domain models shared across License Compliance Checker modules.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class ComponentType(str, Enum):
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    GO = "go"
    JAVA = "java"
    GRADLE = "gradle"
    RUST = "rust"
    GENERIC = "generic"


@dataclass(slots=True)
class Component:
    """
    Represents a single software component discovered during scanning.
    """

    type: ComponentType
    name: str
    version: str
    namespace: Optional[str] = None
    path: Optional[Path] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class LicenseEvidence:
    """
    Evidence item returned from a data source or detector.
    """

    source: str
    license_expression: str
    confidence: float
    raw_data: Dict[str, Any] = field(default_factory=dict)
    url: Optional[str] = None


@dataclass(slots=True)
class ComponentFinding:
    """
    Aggregated result for a component after running the resolution chain.
    """

    component: Component
    evidences: List[LicenseEvidence] = field(default_factory=list)
    resolved_license: Optional[str] = None
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
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ScanReport:
    """
    Complete scan output consumed by reporters and the CLI.
    """

    findings: List[ComponentFinding]
    summary: ScanSummary
    errors: List[str] = field(default_factory=list)
