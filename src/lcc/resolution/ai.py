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
Resolver that uses AI to detect licenses from file content.
"""

import contextlib
import logging
from collections.abc import Iterable
from pathlib import Path

from lcc.ai.license_analyzer import LicenseAnalyzer
from lcc.ai.llm_client import LLMClient
from lcc.config import LCCConfig
from lcc.models import Component, LicenseEvidence
from lcc.resolution.base import Resolver

logger = logging.getLogger(__name__)

class AIResolver(Resolver):
    """
    Resolver that uses LLMs to analyze file content for license information.
    """

    def __init__(self, config: LCCConfig) -> None:
        super().__init__(name="ai-llm")
        self.client = LLMClient(config)
        self.analyzer = LicenseAnalyzer(self.client)

    def resolve(self, component: Component) -> Iterable[LicenseEvidence]:
        if not self.client.enabled:
            return

        # We need a path to analyze
        path = None
        if component.path:
            # Check if it's already absolute
            p = Path(component.path)
            if p.is_absolute() and p.exists():
                path = p
            else:
                # Try to construct path from metadata if available
                project_root = component.metadata.get("project_root")
                if project_root:
                    with contextlib.suppress(Exception):
                        path = Path(project_root) / component.path

        if not path or not isinstance(path, Path) or not path.exists() or not path.is_file():
            return

        try:
            # Synchronous call to analyzer
            license_id = self.analyzer.analyze_file(path)

            if license_id and license_id != "UNKNOWN":
                yield LicenseEvidence(
                    source="ai-llm",
                    license_expression=license_id,
                    confidence=0.75,  # Conservative confidence for AI
                    url=None
                )
        except RuntimeError as e:
            # If we are already in a loop (unlikely given current architecture), log it
            logger.warning(f"Could not run AI analysis for {component.name}: {e}")
        except Exception as e:
            logger.error(f"AI resolution failed for {component.name}: {e}")
