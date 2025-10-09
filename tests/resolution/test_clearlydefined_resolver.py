from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from lcc.cache import Cache
from lcc.config import LCCConfig
from lcc.models import Component, ComponentType
from lcc.resolution.clearlydefined import ClearlyDefinedResolver


class ClearlyDefinedResolverTests(unittest.TestCase):
    def test_resolves_license_expression(self) -> None:
        component = Component(type=ComponentType.JAVASCRIPT, name="react", version="18.2.0")
        with tempfile.TemporaryDirectory() as tmp_dir:
            config = LCCConfig(cache_dir=Path(tmp_dir))
            cache = Cache(config, ttl_seconds=10)
            resolver = ClearlyDefinedResolver(cache, config)

            payload = {
                "licensed": {
                    "declared": "MIT",
                },
                "scores": {"legal": 85},
                "described": {"urls": {"registry": "https://example.org"}},
            }

            response = MagicMock()
            response.status_code = 200
            response.json.return_value = payload

            with patch("lcc.resolution.clearlydefined.requests.get", return_value=response) as mock_get:
                evidences = list(resolver.resolve(component))
                # Second call should hit cache
                evidences_cached = list(resolver.resolve(component))

            self.assertEqual(len(evidences), 1)
            evidence = evidences[0]
            self.assertEqual(evidence.license_expression, "MIT")
            self.assertAlmostEqual(evidence.confidence, 0.85, places=2)
            self.assertEqual(evidence.url, "https://example.org")

            # Cache prevents an additional network call
            mock_get.assert_called_once()
            self.assertEqual(evidences_cached[0].license_expression, "MIT")


if __name__ == "__main__":
    unittest.main()
