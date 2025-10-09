import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from lcc.ai.llm_client import LLMClient
from lcc.config import LCCConfig

@pytest.mark.asyncio
async def test_llm_client_classify():
    config = LCCConfig(llm_endpoint="http://localhost:8000", llm_api_key="dummy")
    client = LLMClient(config)
    
    # Mock the client.chat.completions.create method
    # Since client.client is AsyncOpenAI, we need to mock its structure
    with patch.object(client.client.chat.completions, "create", new_callable=AsyncMock) as mock_create:
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "MIT"
        mock_create.return_value = mock_response
        
        result = await client.classify_license("some text")
        assert result == "MIT"
        mock_create.assert_called_once()

@pytest.mark.asyncio
async def test_llm_client_disabled():
    config = LCCConfig(llm_endpoint=None)
    client = LLMClient(config)
    assert not client.enabled
    result = await client.classify_license("text")
    assert result is None

@pytest.mark.asyncio
async def test_llm_client_error():
    config = LCCConfig(llm_endpoint="http://localhost:8000", llm_api_key="dummy")
    client = LLMClient(config)
    
    with patch.object(client.client.chat.completions, "create", new_callable=AsyncMock) as mock_create:
        mock_create.side_effect = Exception("API Error")
        
        result = await client.classify_license("text")
        assert result is None
