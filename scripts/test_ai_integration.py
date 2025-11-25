#!/usr/bin/env python3
"""
Script to test AI integration with a real LLM endpoint.
Usage:
    export LCC_LLM_ENDPOINT=http://localhost:11434/v1
    export LCC_LLM_MODEL=qwen2.5:72b
    python scripts/test_ai_integration.py
"""
import os
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from lcc.config import LCCConfig
from lcc.ai.llm_client import LLMClient

print("Starting test script...", flush=True)

def main():
    endpoint = os.getenv("LCC_LLM_ENDPOINT")
    if not endpoint:
        print("Error: LCC_LLM_ENDPOINT environment variable is not set.")
        print("Example: export LCC_LLM_ENDPOINT=http://localhost:11434/v1")
        return

    model = os.getenv("LCC_LLM_MODEL", "qwen2.5:72b")
    print(f"Testing connection to LLM at {endpoint} using model {model}...")

    config = LCCConfig(
        llm_endpoint=endpoint,
        llm_model=model,
        llm_api_key=os.getenv("LCC_LLM_API_KEY", "dummy")
    )
    
    client = LLMClient(config)
    
    sample_license_text = """
    MIT License

    Copyright (c) 2023 Example Corp

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.
    """
    
    print("\nSending sample MIT license text for classification...")
    try:
        result = client.classify_license(sample_license_text)
        print(f"\nResult: {result}")
        
        if result and "MIT" in result:
            print("✅ SUCCESS: Correctly identified MIT license.")
        else:
            print("⚠️  WARNING: Did not identify as MIT. Check the model output.")
            
    except Exception as e:
        print(f"\n❌ ERROR: Failed to communicate with LLM: {e}")

if __name__ == "__main__":
    main()
