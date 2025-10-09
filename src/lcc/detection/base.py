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
Detection subsystem interfaces.
"""

from __future__ import annotations

import abc
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import TYPE_CHECKING

from lcc.models import Component

if TYPE_CHECKING:
    from lcc.config import LCCConfig


class DetectorError(RuntimeError):
    """Raised when a detector encounters an unrecoverable error."""


class Detector(abc.ABC):
    """
    Base class for language-specific detectors.
    """

    name: str
    config: LCCConfig | None

    def __init__(self, name: str) -> None:
        self.name = name
        self.config = None

    def set_config(self, config: LCCConfig) -> None:
        """Set the configuration for this detector."""
        self.config = config

    def _is_excluded(self, path: Path, project_root: Path) -> bool:
        """Check if a path should be excluded based on config patterns."""
        if not self.config or not self.config.exclude_patterns:
            return False
        try:
            rel_path = path.relative_to(project_root)
        except ValueError:
            return False
        for pattern in self.config.exclude_patterns:
            # Check if any part of the path matches the pattern
            if rel_path.match(pattern):
                return True
            # Also check if any parent directory matches
            for parent in rel_path.parents:
                if parent.match(pattern):
                    return True
        return False

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

