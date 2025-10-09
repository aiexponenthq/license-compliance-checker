from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from lcc.cache import Cache
from lcc.config import LCCConfig
from lcc.models import Component, ComponentType
from lcc.resolution.registries import RegistryResolver


class RegistryResolverTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp_dir.cleanup)
        self.config = LCCConfig(cache_dir=Path(self.tmp_dir.name))
        self.cache = Cache(self.config, ttl_seconds=10)
        self.resolver = RegistryResolver(self.cache, self.config)

    def test_pypi_resolver_returns_license(self) -> None:
        component = Component(type=ComponentType.PYTHON, name="requests", version="2.31.0")
        payload = {"info": {"license": "Apache-2.0", "home_page": "https://example.org"}}

        response = MagicMock()
        response.status_code = 200
        response.json.return_value = payload

        with patch("lcc.resolution.registries.requests.get", return_value=response) as mock_get:
            evidences = list(self.resolver.resolve(component))

        self.assertEqual(len(evidences), 1)
        evidence = evidences[0]
        self.assertEqual(evidence.source, "pypi")
        self.assertEqual(evidence.license_expression, "Apache-2.0")
        mock_get.assert_called_once()

    def test_pypi_resolver_assumes_latest(self) -> None:
        component = Component(type=ComponentType.PYTHON, name="requests", version="*")
        payload = {"info": {"license": "Apache-2.0", "version": "2.31.0"}}

        response = MagicMock()
        response.status_code = 200
        response.json.return_value = payload

        with patch("lcc.resolution.registries.requests.get", return_value=response):
            evidences = list(self.resolver.resolve(component))

        self.assertEqual(len(evidences), 1)
        evidence = evidences[0]
        self.assertEqual(evidence.raw_data.get("assumed_version"), "2.31.0")

    def test_npm_resolver_extracts_license(self) -> None:
        component = Component(type=ComponentType.JAVASCRIPT, name="react", version="18.2.0")
        payload = {"license": "MIT", "homepage": "https://react.dev"}

        response = MagicMock()
        response.status_code = 200
        response.json.return_value = payload

        with patch("lcc.resolution.registries.requests.get", return_value=response) as mock_get:
            evidences = list(self.resolver.resolve(component))

        self.assertEqual(len(evidences), 1)
        evidence = evidences[0]
        self.assertEqual(evidence.source, "npm")
        self.assertEqual(evidence.license_expression, "MIT")
        mock_get.assert_called_once()


if __name__ == "__main__":
    unittest.main()
