from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import fakeredis

from lcc.cache import Cache
from lcc.config import LCCConfig


class CacheTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp_dir.cleanup)

    def make_config(self) -> LCCConfig:
        cfg = LCCConfig()
        cfg.cache_dir = Path(self.tmp_dir.name)
        cfg.redis_url = None
        return cfg

    def test_file_cache_round_trip(self) -> None:
        cache = Cache(self.make_config(), ttl_seconds=60)
        cache.set("github::demo", {"value": 1})
        cached = cache.get("github::demo")
        self.assertEqual(cached, {"value": 1})
        metrics = cache.get_metrics()
        self.assertEqual(metrics["hits"]["file"], 1)
        self.assertEqual(metrics["misses"]["file"], 0)

    def test_layered_cache_populates_redis_from_file(self) -> None:
        cfg = self.make_config()
        cfg.redis_url = "redis://localhost"
        fake_client = fakeredis.FakeRedis(decode_responses=True)
        with mock.patch("lcc.cache.redis.Redis.from_url", return_value=fake_client):
            cache = Cache(cfg, ttl_seconds=60)
            cache.set("github::demo", {"value": 2})
            # First get should hit redis directly
            self.assertEqual(cache.get("github::demo"), {"value": 2})
            metrics = cache.get_metrics()
            self.assertGreaterEqual(metrics["hits"]["redis"], 1)
            self.assertEqual(metrics["misses"]["file"], 0)

    def test_ttl_override_uses_prefix(self) -> None:
        cfg = self.make_config()
        cfg.cache_ttls = {"github": 120}
        cache = Cache(cfg, ttl_seconds=30)
        self.assertEqual(cache._resolve_ttl("github::demo/repo"), 120)
        self.assertEqual(cache._resolve_ttl("npm::leftpad"), 30)


if __name__ == "__main__":
    unittest.main()
