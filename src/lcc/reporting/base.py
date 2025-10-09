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

