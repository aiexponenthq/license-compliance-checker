"""
Reporting subsystem abstraction.
"""

from __future__ import annotations

import abc
from typing import Protocol

from lcc.models import ScanReport


class Reporter(Protocol):
    """
    Reporter protocol implemented by JSON, console and other format writers.
    """

    def render(self, report: ScanReport) -> str:
        """Return the rendered representation of the report."""


class StreamingReporter(abc.ABC):
    """
    Streaming reporter that writes to a target like stdout or a file handle.
    """

    @abc.abstractmethod
    def write(self, report: ScanReport) -> None:
        """Emit the report to the configured output sink."""

