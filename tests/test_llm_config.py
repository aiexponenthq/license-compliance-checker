import os
from unittest.mock import MagicMock, patch

import pytest
from lcc.ai.llm_client import LLMClient
from lcc.config import LCCConfig

def test_llm_client_fireworks_config():
    """Verify LLMClient configures correctly for Fireworks provider."""
    # Setup config
    config = LCCConfig()
    config.llm_provider = "fireworks"
    config.fireworks_api_key = "fw_test_key"
    config.llm_model = "test-model"
    
    # Mock OpenAI to prevent network calls
    with patch("lcc.ai.llm_client.OpenAI") as mock_openai:
        client = LLMClient(config)
        
        assert client.enabled is True
        assert client.provider == "fireworks"
        
        # Check if OpenAI was initialized with Fireworks URL
        mock_openai.assert_called_once()
        call_kwargs = mock_openai.call_args[1]
        assert call_kwargs["base_url"] == "https://api.fireworks.ai/inference/v1"
        assert call_kwargs["api_key"] == "fw_test_key"

def test_llm_client_local_config():
    """Verify LLMClient configures correctly for Local provider."""
    # Setup config
    config = LCCConfig()
    config.llm_provider = "local"
    config.llm_endpoint = "http://localhost:11434/v1"
    config.llm_model = "llama2"
    
    # Mock OpenAI
    with patch("lcc.ai.llm_client.OpenAI") as mock_openai:
        client = LLMClient(config)
        
        assert client.enabled is True
        assert client.provider == "local"
        
        # Check if OpenAI was initialized with Local URL
        mock_openai.assert_called_once()
        call_kwargs = mock_openai.call_args[1]
        assert call_kwargs["base_url"] == "http://localhost:11434/v1"
