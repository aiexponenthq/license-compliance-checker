"""
Detection subsystem interfaces.
"""

from __future__ import annotations

import abc
from pathlib import Path
from typing import Iterable, Sequence

from lcc.models import Component


class DetectorError(RuntimeError):
    """Raised when a detector encounters an unrecoverable error."""


class Detector(abc.ABC):
    """
    Base class for language-specific detectors.
    """

    name: str

    def __init__(self, name: str) -> None:
        self.name = name

    @abc.abstractmethod
    def supports(self, project_root: Path) -> bool:
        """
        Return True if the detector can operate on the project root.
        """

    @abc.abstractmethod
    def discover(self, project_root: Path) -> Sequence[Component]:
        """
        Discover components managed by the ecosystem.
        """


DetectorCollection = Iterable[Detector]

