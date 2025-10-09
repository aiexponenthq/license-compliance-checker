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

"""Cache utilities with optional Redis backend."""

from __future__ import annotations

import hashlib
import json
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

try:  # pragma: no cover - optional dependency
    import redis
except ImportError:  # pragma: no cover - optional dependency
    redis = None

from lcc.config import LCCConfig


class BaseCache:
    def get(self, key: str) -> Any | None:  # pragma: no cover - interface
        raise NotImplementedError

    def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:  # pragma: no cover - interface
        raise NotImplementedError

    def get_or_fetch(self, key: str, fetcher: Callable[[], Any]) -> Any:
        cached = self.get(key)
        if cached is not None:
            return cached
        value = fetcher()
        self.set(key, value)
        return value


class FileCache(BaseCache):
    def __init__(self, cache_dir: Path, ttl_seconds: int) -> None:
        self.cache_dir = cache_dir
        self.default_ttl = ttl_seconds

    def _key_path(self, key: str) -> Path:
        digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
        return self.cache_dir / f"{digest}.json"

    def get(self, key: str) -> Any | None:
        path = self._key_path(key)
        if not path.exists():
            return None
        try:
            with path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except json.JSONDecodeError:
            path.unlink(missing_ok=True)
            return None
        if isinstance(payload, dict) and "value" in payload and "expires_at" in payload:
            expires_at = payload.get("expires_at")
            if isinstance(expires_at, (int, float)) and expires_at < time.time():
                path.unlink(missing_ok=True)
                return None
            return payload.get("value")
        # Backwards compatibility with older cache entries without metadata
        if self.default_ttl > 0 and time.time() - path.stat().st_mtime > self.default_ttl:
            path.unlink(missing_ok=True)
            return None
        return payload

    def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        path = self._key_path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        ttl = self.default_ttl if ttl_seconds is None else ttl_seconds
        if ttl and ttl > 0:
            payload = {"value": value, "expires_at": time.time() + ttl}
        else:
            payload = {"value": value, "expires_at": None}
        with path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle)


class RedisCache(BaseCache):
    def __init__(self, url: str, ttl_seconds: int) -> None:
        if redis is None:  # pragma: no cover - optional dependency
            raise RuntimeError("redis package is required for RedisCache")
        self.client = redis.Redis.from_url(url, decode_responses=True)
        self.default_ttl = ttl_seconds

    def get(self, key: str) -> Any | None:
        data = self.client.get(key)
        if data is None:
            return None
        try:
            payload = json.loads(data)
        except json.JSONDecodeError:  # pragma: no cover - defensive
            return data
        if isinstance(payload, dict) and "value" in payload:
            return payload.get("value")
        return payload

    def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        payload = json.dumps({"value": value})
        ttl = self.default_ttl if ttl_seconds is None else ttl_seconds
        if ttl and ttl > 0:
            self.client.setex(key, ttl, payload)
        else:
            self.client.set(key, payload)


class Cache(BaseCache):
    """Layered cache that combines Redis and file-based persistence with metrics."""

    def __init__(self, config: LCCConfig, ttl_seconds: int = 3600) -> None:
        self.config = config
        self.ttl_seconds = ttl_seconds
        self.metrics = {
            "hits": {"redis": 0, "file": 0},
            "misses": {"redis": 0, "file": 0},
            "writes": {"redis": 0, "file": 0},
        }

        self.redis_backend: RedisCache | None = None
        if config.redis_url and redis is not None:
            try:
                self.redis_backend = RedisCache(config.redis_url, ttl_seconds)
            except Exception:  # pragma: no cover - fallback
                self.redis_backend = None

        cache_dir = config.cache_dir
        try:
            cache_dir.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            fallback = Path.cwd() / ".lcc-cache"
            fallback.mkdir(parents=True, exist_ok=True)
            cache_dir = fallback
            self.config.cache_dir = fallback
        self.file_backend = FileCache(cache_dir, ttl_seconds)

    def get(self, key: str) -> Any | None:
        value: Any | None = None
        if self.redis_backend is not None:
            value = self.redis_backend.get(key)
            if value is not None:
                self.metrics["hits"]["redis"] += 1
                return value
            self.metrics["misses"]["redis"] += 1

        value = self.file_backend.get(key)
        if value is not None:
            self.metrics["hits"]["file"] += 1
            if self.redis_backend is not None:
                ttl = self._resolve_ttl(key)
                self.redis_backend.set(key, value, ttl)
                self.metrics["writes"]["redis"] += 1
            return value

        self.metrics["misses"]["file"] += 1
        return None

    def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        ttl = ttl_seconds if ttl_seconds is not None else self._resolve_ttl(key)
        self.file_backend.set(key, value, ttl)
        self.metrics["writes"]["file"] += 1
        if self.redis_backend is not None:
            self.redis_backend.set(key, value, ttl)
            self.metrics["writes"]["redis"] += 1

    def get_or_fetch(self, key: str, fetcher: Callable[[], Any]) -> Any:
        cached = self.get(key)
        if cached is not None:
            return cached
        value = fetcher()
        self.set(key, value)
        return value

    def get_metrics(self) -> dict[str, dict[str, int]]:
        return {
            category: metrics.copy()
            for category, metrics in self.metrics.items()
        }

    def _resolve_ttl(self, key: str) -> int:
        overrides = getattr(self.config, "cache_ttls", {}) or {}
        prefix = key.split("::", 1)[0]
        return int(overrides.get(prefix, self.ttl_seconds))
