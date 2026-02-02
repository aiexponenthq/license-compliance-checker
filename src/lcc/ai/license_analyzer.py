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

    def analyze_file(self, file_path: Path) -> Optional[str]:
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
            # Smart Chunking: Read head and tail to capture licenses at top or bottom
            MAX_SIZE = 5000
            HEAD_SIZE = 2000
            TAIL_SIZE = 1000
            
            file_size = file_path.stat().st_size
            
            if file_size <= MAX_SIZE:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                snippet = content
            else:
                with file_path.open("r", encoding="utf-8", errors="ignore") as f:
                    head = f.read(HEAD_SIZE)
                    
                    # Seek to tail
                    f.seek(max(file_size - TAIL_SIZE, HEAD_SIZE))
                    tail = f.read()
                    
                    snippet = f"{head}\n\n[...SNIP...]\n\n{tail}"
            
            if not snippet.strip():
                return None

            logger.debug(f"Sending {file_path.name} to LLM for analysis (size: {len(snippet)} chars)")
            return self.llm.classify_license(snippet)
            
        except Exception as e:
            logger.warning(f"Failed to analyze file {file_path}: {e}")
            return None
