"""
Service for analyzing files to detect licenses using AI.
"""
import logging
from pathlib import Path
from typing import Optional

from lcc.ai.llm_client import LLMClient

logger = logging.getLogger(__name__)

class LicenseAnalyzer:
    """
    Analyzes file content to detect licenses, leveraging LLMs for difficult cases.
    """

    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

    async def analyze_file(self, file_path: Path) -> Optional[str]:
        """
        Analyze a file to determine its license.
        
        Args:
            file_path: Path to the file to analyze.
            
        Returns:
            SPDX License Identifier or None if undetermined.
        """
        if not self.llm.enabled:
            return None

        if not file_path.exists() or not file_path.is_file():
            return None

        try:
            # Read file content, focusing on the beginning where license headers usually are
            # Limit to 3000 characters to stay within reasonable token limits for the prompt context
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            snippet = content[:3000]
            
            if not snippet.strip():
                return None

            logger.debug(f"Sending {file_path.name} to LLM for analysis")
            return await self.llm.classify_license(snippet)
            
        except Exception as e:
            logger.warning(f"Failed to analyze file {file_path}: {e}")
            return None
