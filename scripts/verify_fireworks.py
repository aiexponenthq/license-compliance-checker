#!/usr/bin/env python3
"""
Verification script for Fireworks AI integration.
Run this to confirm that the API key and client are working correctly.
"""
import logging
import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from lcc.config import load_config
from lcc.ai.llm_client import LLMClient

# Calculate relative path to .env file from the script location
# implementation assumes script is in scripts/ and project root is parent
project_root = Path(__file__).parent.parent
env_path = project_root / ".env"

# Force load .env if it exists, just to be sure, though config does it too
try:
    from dotenv import load_dotenv
    load_dotenv(env_path)
    print(f"Loaded environment from {env_path}")
except ImportError:
    print("python-dotenv not installed, relying on environment variables")

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("verification")

def main():
    print("-" * 50)
    print("Fireworks AI Verification")
    print("-" * 50)

    # 1. Load Config
    try:
        config = load_config()
        print(f"Loaded Configuration:")
        print(f"  Provider: {config.llm_provider}")
        print(f"  Model:    {config.llm_model}")
        print(f"  Endpoint: {config.llm_endpoint or 'Default (Fireworks)'}")
        
        if config.llm_provider != "fireworks":
            print("\nERROR: LCC_LLM_PROVIDER is not set to 'fireworks'.")
            print("Please check your .env file.")
            sys.exit(1)
            
        if not config.fireworks_api_key:
            print("\nERROR: LCC_FIREWORKS_API_KEY is missing.")
            print("Please check your .env file.")
            sys.exit(1)
            
    except Exception as e:
        print(f"\nERROR loading config: {e}")
        sys.exit(1)

    # 2. Initialize Client
    try:
        client = LLMClient(config)
        if not client.enabled:
             print("\nERROR: LLMClient is disabled despite correct config.")
             sys.exit(1)
        print("Client initialized successfully.")
    except Exception as e:
        print(f"\nERROR initializing client: {e}")
        sys.exit(1)

    # 3. Send Test Request
    print("\nSending test request to Fireworks AI...")
    
    sample_text = """
    MIT License
    Copyright (c) 2024 Example Corp
    Permission is hereby granted, free of charge, to any person obtaining a copy...
    """
    
    start_time = time.time()
    try:
        result = client.classify_license(sample_text)
        duration = time.time() - start_time
        
        print(f"\nRequest completed in {duration:.2f} seconds.")
        print(f"Result: {result}")
        
        if "MIT" in str(result):
            print("\nSUCCESS: License correctly identified as MIT.")
        else:
            print(f"\nWARNING: Unexpected result. Expected 'MIT', got '{result}'.")
            
    except Exception as e:
        print(f"\nERROR during API call: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
