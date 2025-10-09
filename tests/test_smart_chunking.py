
import os
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

# Ensure lcc is importable
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from lcc.ai.license_analyzer import LicenseAnalyzer
from lcc.ai.llm_client import LLMClient

def test_smart_chunking(tmp_path):
    """Verify that LicenseAnalyzer reads head and tail for large files."""
    
    # 1. Create a large file (approx 10KB)
    # Head has "Starting Content"
    # Middle is padding
    # Tail has "Ending License"
    
    file_path = tmp_path / "large_file.c"
    
    head_content = "/* Starting Content" + ("." * 1980) + "*/" # ~2KB
    middle_padding = " " * 8000
    tail_content = "/* Ending License: MIT */" 
    
    full_content = head_content + middle_padding + tail_content
    file_path.write_text(full_content)
    
    # 2. Mock LLM Client
    mock_llm = MagicMock(spec=LLMClient)
    mock_llm.enabled = True
    
    analyzer = LicenseAnalyzer(mock_llm)
    
    # 3. Analyze
    analyzer.analyze_file(file_path)
    
    # 4. Verify what was sent to LLM
    mock_llm.classify_license.assert_called_once()
    snippet = mock_llm.classify_license.call_args[0][0]
    
    # Assertions
    assert "Starting Content" in snippet
    assert "Ending License: MIT" in snippet
    assert "[...SNIP...]" in snippet
    
    # Verify length is reasonable (Head 2000 + Tail 1000 + separator)
    assert len(snippet) < 3200 

def test_small_file_no_chunking(tmp_path):
    """Verify small files are read fully."""
    file_path = tmp_path / "small.c"
    content = "Small file content"
    file_path.write_text(content)
    
    mock_llm = MagicMock(spec=LLMClient)
    mock_llm.enabled = True
    
    analyzer = LicenseAnalyzer(mock_llm)
    analyzer.analyze_file(file_path)
    
    mock_llm.classify_license.assert_called_once()
    snippet = mock_llm.classify_license.call_args[0][0]
    
    assert snippet == content
    assert "[...SNIP...]" not in snippet
