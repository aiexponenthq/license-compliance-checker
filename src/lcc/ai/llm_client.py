"""
LLM Client for interacting with local or remote LLM endpoints.
"""
import logging
from typing import Optional

from openai import AsyncOpenAI, OpenAIError

from lcc.config import LCCConfig

logger = logging.getLogger(__name__)

class LLMClient:
    """
    Client for interacting with LLM APIs using the OpenAI SDK format.
    Compatible with OpenAI, vLLM, Ollama, LocalAI, etc.
    """

    def __init__(self, config: LCCConfig):
        self.enabled = bool(config.llm_endpoint)
        self.model = config.llm_model
        self.client: Optional[AsyncOpenAI] = None
        
        if self.enabled:
            self.client = AsyncOpenAI(
                base_url=config.llm_endpoint,
                api_key=config.llm_api_key
            )
            logger.info(f"LLM Client initialized with endpoint: {config.llm_endpoint}, model: {self.model}")
        else:
            logger.warning("LLM Client disabled: No endpoint configured.")

    async def classify_license(self, text_snippet: str) -> Optional[str]:
        """
        Ask the LLM to identify the license from a text snippet.
        """
        if not self.enabled or not self.client:
            return None

        prompt = (
            "You are a software license compliance expert. "
            "Analyze the following text snippet from a source code file or LICENSE file. "
            "Identify the software license. "
            "Return ONLY the SPDX License Identifier (e.g., 'MIT', 'Apache-2.0', 'GPL-3.0-only'). "
            "If it is proprietary or you cannot determine it with high confidence, return 'UNKNOWN'.\n\n"
            f"Text Snippet:\n{text_snippet[:2000]}\n\n"  # Truncate to avoid context limits
            "SPDX Identifier:"
        )

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that identifies software licenses."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1, # Low temperature for deterministic output
                max_tokens=20,
            )
            content = response.choices[0].message.content.strip()
            # Basic cleanup
            content = content.replace("SPDX Identifier:", "").strip()
            return content
        except OpenAIError as e:
            logger.error(f"LLM API error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error calling LLM: {e}")
            return None
