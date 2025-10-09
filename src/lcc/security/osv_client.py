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
from typing import Any

import requests

logger = logging.getLogger(__name__)

OSV_QUERY_URL = "https://api.osv.dev/v1/query"

class OSVClient:
    """
    Client for querying the OSV.dev API for vulnerabilities.
    """

    def __init__(self, timeout: float = 10.0):
        self.timeout = timeout
        self.session = requests.Session()

    def query_package(self, name: str, version: str, ecosystem: str) -> list[dict[str, Any]]:
        """
        Query OSV for vulnerabilities affecting a specific package version.

        Args:
            name: Package name (e.g., "requests")
            version: Package version (e.g., "2.19.0")
            ecosystem: Package ecosystem (e.g., "PyPI", "npm", "Go")

        Returns:
            List of vulnerability dictionaries.
        """
        payload = {
            "version": version,
            "package": {
                "name": name,
                "ecosystem": ecosystem
            }
        }

        try:
            response = self.session.post(OSV_QUERY_URL, json=payload, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            return data.get("vulns", [])
        except requests.RequestException as e:
            logger.warning(f"OSV query failed for {ecosystem}/{name}@{version}: {e}")
            return []
