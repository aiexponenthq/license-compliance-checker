# Copyright 2025 Ajay Pundhir
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
from pathlib import Path

import requests

logger = logging.getLogger(__name__)

SPDX_TEXT_URL = "https://raw.githubusercontent.com/spdx/license-list-data/main/text/{license_id}.txt"

class LicenseLoader:
    """
    Fetches and caches full license texts.
    """

    def __init__(self, cache_dir: Path | None = None):
        if cache_dir:
            self.cache_dir = cache_dir
        else:
            self.cache_dir = Path.home() / ".lcc" / "licenses"

        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get_license_text(self, license_id: str) -> str | None:
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
