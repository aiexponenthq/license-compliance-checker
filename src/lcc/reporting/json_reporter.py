"""
JSON reporter.
"""

from __future__ import annotations

import json
from dataclasses import asdict

from lcc.models import ScanReport
from lcc.reporting.base import Reporter


class JSONReporter(Reporter):
    """
    Serializes the ScanReport to JSON, preserving dataclass structure.
    """

    def render(self, report: ScanReport) -> str:
        return json.dumps(asdict(report), indent=2, sort_keys=True, default=str)

