"""
LLM Client for interacting with local or remote LLM endpoints.
"""
import logging
from typing import Optional

from openai import OpenAI, OpenAIError

from lcc.config import LCCConfig

logger = logging.getLogger(__name__)

class LLMClient:
    """
    Client for interacting with LLM APIs using the OpenAI SDK format.
    Compatible with OpenAI, vLLM, Ollama, LocalAI, etc.
    """

    def __init__(self, config: LCCConfig):
        self.enabled = bool(config.llm_endpoint) or (config.llm_provider == "fireworks" and bool(config.fireworks_api_key))
        self.model = config.llm_model
        self.client: Optional[OpenAI] = None
        self.provider = config.llm_provider
        
        if self.enabled:
            api_key = config.llm_api_key
            base_url = config.llm_endpoint

            if self.provider == "fireworks":
                api_key = config.fireworks_api_key or "invalid"
                base_url = "https://api.fireworks.ai/inference/v1"
                logger.info("Initializing LLM Client with provider: fireworks")
            else:
                logger.info(f"Initializing LLM Client with provider: local (endpoint: {base_url})")

            self.client = OpenAI(
                base_url=base_url,
                api_key=api_key
            )
            logger.info(f"LLM Client ready with model: {self.model}")
        else:
            logger.warning("LLM Client disabled: No endpoint or provider configured.")

    def classify_license(self, text_snippet: str) -> Optional[str]:
        """
        Ask the LLM to identify the license from a text snippet.
        """
        import json

        if not self.enabled or not self.client:
            return None

        system_prompt = (
            "You are a software license compliance expert. "
            "Analyze the provided text snippet (source code header or LICENSE file) and identify the software license.\n"
            "You must respond with a JSON object following this schema:\n"
            "{\n"
            '  "license_id": "SPDX-Identifier (e.g., MIT, Apache-2.0, GPL-3.0-only) or UNKNOWN",\n'
            '  "confidence": 0.0 to 1.0,\n'
            '  "is_proprietary": boolean,\n'
            '  "reasoning": "Brief explanation"\n'
            "}"
        )

        user_prompt = f"Text Snippet:\n{text_snippet[:2000]}"

        try:
            # Prepare kwargs for API call
            kwargs = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.1,
                "max_tokens": 1024,
            }

            # Add response_format if supported (OpenAI / Fireworks)
            # Ollama uses 'format="json"', but the openai-python client handles standards nicely.
            # For strict OpenAI/Fireworks compatibility:
            kwargs["response_format"] = {"type": "json_object"}

            response = self.client.chat.completions.create(**kwargs)
            content = response.choices[0].message.content
            
            if not content:
                logger.warning(f"LLM returned no content. Full response: {response}")
                return None
            
            try:
                data = json.loads(content)
                license_id = data.get("license_id", "UNKNOWN")
                logger.debug(f"AI Analysis Result: {data}")
                
                # Filter out UNKNOWN or low confidence if needed
                if license_id == "UNKNOWN":
                    return None
                    
                return license_id.strip()
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse JSON response: {content}")
                return None
                
        except OpenAIError as e:
            logger.error(f"LLM API error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error calling LLM: {e}")
            return None
