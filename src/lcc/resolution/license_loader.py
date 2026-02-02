
import logging
import os
from pathlib import Path
from typing import Optional
import requests

logger = logging.getLogger(__name__)

SPDX_TEXT_URL = "https://raw.githubusercontent.com/spdx/license-list-data/main/text/{license_id}.txt"

class LicenseLoader:
    """
    Fetches and caches full license texts.
    """

    def __init__(self, cache_dir: Optional[Path] = None):
        if cache_dir:
            self.cache_dir = cache_dir
        else:
            self.cache_dir = Path.home() / ".lcc" / "licenses"
        
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get_license_text(self, license_id: str) -> Optional[str]:
        """
        Get the full text for a given SPDX identifier.
        Checks local cache first, then fetches from SPDX repo.
        """
        if not license_id or license_id == "UNKNOWN":
            return None

        # Check cache
        cache_file = self.cache_dir / f"{license_id}.txt"
        if cache_file.exists():
            logger.debug(f"Loaded {license_id} from cache")
            return cache_file.read_text(encoding="utf-8")

        # Fetch from network
        try:
            url = SPDX_TEXT_URL.format(license_id=license_id)
            logger.info(f"Fetching license text for {license_id} from {url}")
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                text = response.text
                cache_file.write_text(text, encoding="utf-8")
                return text
            else:
                logger.warning(f"License text not found for {license_id} (Status: {response.status_code})")
                return None
        except Exception as e:
            logger.warning(f"Failed to fetch license text for {license_id}: {e}")
            return None
