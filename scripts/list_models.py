
import os
import sys
import requests
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from lcc.config import load_config

def main():
    config = load_config()
    api_key = config.fireworks_api_key
    
    if not api_key:
        print("No API key found in .env")
        return

    url = "https://api.fireworks.ai/inference/v1/models"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json"
    }
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        models = response.json().get("data", [])
        print(f"Found {len(models)} models:")
        for m in models:
            if "llama" in m["id"] or "qwen" in m["id"]:
                print(f" - {m['id']}")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    main()
