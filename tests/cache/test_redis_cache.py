from __future__ import annotations

import json
import time
import unittest

import fakeredis

from lcc.cache import Cache
from lcc.config import LCCConfig


class RedisCacheTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fake = fakeredis.FakeRedis(decode_responses=True)

    def test_uses_redis_when_configured(self) -> None:
        config = LCCConfig()
        config.redis_url = "redis://localhost"

        # Monkey patch redis.Redis.from_url to return fake instance
        from lcc import cache as cache_module

        original_from_url = cache_module.redis.Redis.from_url  # type: ignore[attr-defined]
        cache_module.redis.Redis.from_url = lambda *args, **kwargs: self.fake  # type: ignore[assignment]
        try:
            cache = Cache(config, ttl_seconds=1)
            cache.set("foo", {"bar": 1})
            self.assertEqual(cache.get("foo"), {"bar": 1})
            time.sleep(1.1)
            self.assertIsNone(cache.get("foo"))
        finally:
            cache_module.redis.Redis.from_url = original_from_url  # type: ignore[attr-defined]


if __name__ == "__main__":
    unittest.main()
