from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from lcc.cache import Cache
from lcc.config import LCCConfig
from lcc.models import Component, ComponentType
from lcc.resolution.github import GitHubResolver


class GitHubResolverTests(unittest.TestCase):
    def test_uses_repository_metadata(self) -> None:
        component = Component(
            type=ComponentType.JAVASCRIPT,
            name="react",
            version="18.2.0",
            metadata={"repository": "https://github.com/facebook/react"},
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            config = LCCConfig(cache_dir=Path(tmp_dir))
            cache = Cache(config, ttl_seconds=10)
            resolver = GitHubResolver(cache, config)

            payload = {
                "license": {"spdx_id": "MIT"},
                "download_url": "https://raw.githubusercontent.com/facebook/react/main/LICENSE",
            }
            response = MagicMock()
            response.status_code = 200
            response.json.return_value = payload

            with patch("lcc.resolution.github.requests.get", return_value=response) as mock_get:
                evidences = list(resolver.resolve(component))

            self.assertEqual(len(evidences), 1)
            evidence = evidences[0]
            self.assertEqual(evidence.license_expression, "MIT")
            self.assertEqual(evidence.source, "github")
            self.assertTrue(evidence.url.endswith("LICENSE"))
            mock_get.assert_called_once()


if __name__ == "__main__":
    unittest.main()
