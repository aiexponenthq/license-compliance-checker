"""
Resolver that uses AI to detect licenses from file content.
"""
import asyncio
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
        path = component.path
        if not path:
            # Try to construct path from metadata if available
            # Some detectors might put relative path in component.path and root in metadata
            project_root = component.metadata.get("project_root")
            if project_root and component.path:
                try:
                    path = Path(project_root) / component.path
                except Exception:
                    pass
        
        if not path or not isinstance(path, Path) or not path.exists() or not path.is_file():
            return

        try:
            # Since this method is synchronous but the analyzer is async,
            # and we expect this to run in a thread (via run_in_executor),
            # we can use asyncio.run() to execute the async logic.
            # NOTE: This assumes we are NOT in the main event loop thread.
            license_id = asyncio.run(self.analyzer.analyze_file(path))
            
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
