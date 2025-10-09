from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from lcc.cache import Cache
from lcc.config import LCCConfig
from lcc.models import Component, ComponentType
from lcc.resolution.scancode import ScanCodeResolver


class ScanCodeResolverTests(unittest.TestCase):
    def test_aggregates_highest_confidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            component = Component(
                type=ComponentType.PYTHON,
                name="sample",
                version="0.1.0",
                metadata={"source_path": tmp_dir},
            )
            config = LCCConfig(cache_dir=Path(tmp_dir) / "cache")
            cache = Cache(config, ttl_seconds=10)
            resolver = ScanCodeResolver(cache, config)

            payload = {
                "files": [
                    {
                        "path": "LICENSE",
                        "licenses": [
                            {"spdx_expression": "MIT", "score": 100.0},
                            {"spdx_expression": "Apache-2.0", "score": 80.0},
                        ],
                    }
                ]
            }

            with patch.object(ScanCodeResolver, "_run_scancode", return_value=payload):
                evidences = list(resolver.resolve(component))

            self.assertEqual(len(evidences), 2)
            best = max(evidences, key=lambda ev: ev.confidence)
            self.assertEqual(best.license_expression, "MIT")
            self.assertGreaterEqual(best.confidence, 0.99)


if __name__ == "__main__":
    unittest.main()
