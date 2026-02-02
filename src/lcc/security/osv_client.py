
import logging
from typing import Any, Dict, List, Optional
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

    def query_package(self, name: str, version: str, ecosystem: str) -> List[Dict[str, Any]]:
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
