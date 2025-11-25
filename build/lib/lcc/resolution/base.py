"""
Resolution subsystem interfaces for external data sources.
"""

from __future__ import annotations

import abc
from typing import Iterable, Optional

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

    def healthcheck(self) -> Optional[str]:
        """
        Return None when the resolver is healthy; otherwise a diagnostics message.
        """
        return None


ResolverChain = Iterable[Resolver]

