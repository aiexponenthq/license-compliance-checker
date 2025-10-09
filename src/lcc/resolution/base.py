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
Resolution subsystem interfaces for external data sources.
"""

from __future__ import annotations

import abc
from collections.abc import Iterable

from lcc.models import Component, LicenseEvidence


class ResolutionError(RuntimeError):
    """Raised when a resolver fails."""


class Resolver(abc.ABC):
    """
    Base class for license information resolvers.
    """

    name: str

    def __init__(self, name: str) -> None:
        self.name = name

    @abc.abstractmethod
    def resolve(self, component: Component) -> Iterable[LicenseEvidence]:
        """
        Yield LicenseEvidence objects for the provided component.
        """

    def healthcheck(self) -> str | None:
        """
        Return None when the resolver is healthy; otherwise a diagnostics message.
        """
        return None


ResolverChain = Iterable[Resolver]

