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
Fallback resolution chain controller.
"""

from __future__ import annotations

from collections.abc import Iterable

from lcc.models import ComponentFinding
from lcc.resolution.base import Resolver


class FallbackResolver:
    """
    Executes resolvers in priority order and aggregates evidence.
    """

    def __init__(self, resolvers: Iterable[Resolver]) -> None:
        self.resolvers = list(resolvers)

    def resolve(self, finding: ComponentFinding) -> None:
        seen: set[tuple[str, str]] = set()
        resolution_path: list[str] = []
        for resolver in self.resolvers:
            try:
                evidences = list(resolver.resolve(finding.component))
            except Exception as exc:  # pragma: no cover - safety net
                finding.component.metadata.setdefault("resolver_errors", []).append({
                    "resolver": resolver.name,
                    "error": str(exc),
                })
                continue
            if evidences:
                resolution_path.append(resolver.name)
            for evidence in evidences:
                key = (evidence.source, evidence.license_expression)
                if key in seen:
                    continue
                seen.add(key)
                finding.evidences.append(evidence)
                assumed = evidence.raw_data.get("assumed_version") if isinstance(evidence.raw_data, dict) else None
                if assumed and finding.component.version in (None, "*"):
                    assumption = {"type": "version", "value": assumed, "source": evidence.source}
                    assumptions = finding.component.metadata.setdefault("assumptions", [])
                    if assumption not in assumptions:
                        assumptions.append(assumption)
                    finding.component.metadata.setdefault("assumed_version", assumed)
                    # Actually update the component version with the assumed version
                    finding.component.version = assumed
                    finding.component.metadata["version_source"] = "assumed_from_" + evidence.source
        if resolution_path:
            finding.component.metadata.setdefault("resolution_path", resolution_path)
        if finding.evidences:
            best = max(finding.evidences, key=lambda ev: ev.confidence)
            finding.resolved_license = best.license_expression
            finding.confidence = best.confidence
        else:
            finding.resolved_license = None
            finding.confidence = 0.0
