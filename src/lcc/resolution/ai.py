"""
Resolver that uses AI to detect licenses from file content.
"""

import logging
from pathlib import Path
from typing import Iterable

from lcc.config import LCCConfig
from lcc.models import Component, LicenseEvidence
from lcc.resolution.base import Resolver
from lcc.ai.llm_client import LLMClient
from lcc.ai.license_analyzer import LicenseAnalyzer

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
                    try:
                        path = Path(project_root) / component.path
                    except Exception:
                        pass
        
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
