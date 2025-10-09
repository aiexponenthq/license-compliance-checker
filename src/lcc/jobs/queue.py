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

"""Redis-backed job queue for asynchronous processing."""

from __future__ import annotations

import json
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

try:  # pragma: no cover - optional dependency
    import redis
except ImportError:  # pragma: no cover - optional dependency
    redis = None

from lcc.config import LCCConfig


class QueueError(RuntimeError):
    """Raised when queue operations fail."""


@dataclass
class Job:
    id: str
    type: str
    payload: dict[str, Any]
    priority: int = 0
    attempts: int = 0
    max_retries: int = 3
    status: str = "pending"
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "payload": self.payload,
            "priority": self.priority,
            "attempts": self.attempts,
            "max_retries": self.max_retries,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Job:
        return cls(
            id=data["id"],
            type=data["type"],
            payload=data.get("payload", {}),
            priority=int(data.get("priority", 0)),
            attempts=int(data.get("attempts", 0)),
            max_retries=int(data.get("max_retries", 3)),
            status=data.get("status", "pending"),
            created_at=data.get("created_at", datetime.now(UTC).isoformat()),
            updated_at=data.get("updated_at", datetime.now(UTC).isoformat()),
        )


class JobQueue:
    """Redis-backed queue with priority and retry support."""

    def __init__(self, config: LCCConfig, name: str = "lcc") -> None:
        if not config.redis_url or redis is None:
            raise QueueError("Redis is required for JobQueue. Set LCC_REDIS_URL and install redis library.")
        self.config = config
        self.client = redis.Redis.from_url(config.redis_url, decode_responses=True)
        self.prefix = f"{name}:jobs"
        self.queue_key = f"{self.prefix}:queue"
        self.dead_key = f"{self.prefix}:dead"

    def enqueue(self, job_type: str, payload: dict[str, Any], *, priority: int = 0, max_retries: int = 3) -> Job:
        job = Job(id=str(uuid.uuid4()), type=job_type, payload=payload, priority=priority, max_retries=max_retries)
        key = self._job_key(job.id)
        self.client.set(key, json.dumps(job.to_dict()))
        self.client.zadd(self.queue_key, {job.id: priority})
        return job

    def fetch(self) -> Job | None:
        while True:
            with self.client.pipeline() as pipe:
                try:
                    pipe.watch(self.queue_key)
                    result = pipe.zrange(self.queue_key, 0, 0)
                    if not result:
                        pipe.unwatch()
                        return None
                    job_id = result[0]
                    pipe.multi()
                    pipe.zrem(self.queue_key, job_id)
                    pipe.execute()
                except redis.WatchError:  # pragma: no cover - contention
                    continue
                break
        data = self.client.get(self._job_key(job_id))
        if not data:
            return None
        job_dict = json.loads(data)
        job = Job.from_dict(job_dict)
        job.status = "processing"
        job.updated_at = datetime.now(UTC).isoformat()
        self.client.set(self._job_key(job.id), json.dumps(job.to_dict()))
        return job

    def complete(self, job: Job, result: dict[str, Any] | None = None) -> None:
        job.status = "completed"
        job.updated_at = datetime.now(UTC).isoformat()
        data = job.to_dict()
        if result is not None:
            data["result"] = result
        self.client.set(self._job_key(job.id), json.dumps(data))

    def fail(self, job: Job, error_message: str) -> None:
        job.attempts += 1
        job.updated_at = datetime.now(UTC).isoformat()
        if job.attempts > job.max_retries:
            job.status = "dead"
            data = job.to_dict()
            data["error"] = error_message
            self.client.set(self._job_key(job.id), json.dumps(data))
            self.client.rpush(self.dead_key, job.id)
            return

        job.status = "pending"
        data = job.to_dict()
        data["error"] = error_message
        self.client.set(self._job_key(job.id), json.dumps(data))
        self.client.zadd(self.queue_key, {job.id: job.priority})

    def requeue_dead(self, limit: int = 10) -> int:
        count = 0
        for _ in range(limit):
            job_id = self.client.lpop(self.dead_key)
            if job_id is None:
                break
            data = self.client.get(self._job_key(job_id))
            if not data:
                continue
            job = Job.from_dict(json.loads(data))
            job.attempts = 0
            job.status = "pending"
            job.updated_at = datetime.now(UTC).isoformat()
            self.client.set(self._job_key(job.id), json.dumps(job.to_dict()))
            self.client.zadd(self.queue_key, {job.id: job.priority})
            count += 1
        return count

    def stats(self) -> dict[str, Any]:
        return {
            "queued": self.client.zcard(self.queue_key),
            "dead": self.client.llen(self.dead_key),
        }

    def get_job(self, job_id: str) -> dict[str, Any] | None:
        data = self.client.get(self._job_key(job_id))
        return json.loads(data) if data else None

    def _job_key(self, job_id: str) -> str:
        return f"{self.prefix}:{job_id}"


class JobQueueWorker:
    def __init__(
        self,
        queue: JobQueue,
        handler: Callable[[Job], dict[str, Any] | None],
        *,
        poll_interval: float = 1.0,
    ) -> None:
        self.queue = queue
        self.handler = handler
        self.poll_interval = poll_interval
        self._running = False

    def run(self) -> None:
        self._running = True
        while self._running:
            job = self.queue.fetch()
            if job is None:
                time.sleep(self.poll_interval)
                continue
            try:
                result = self.handler(job)
                self.queue.complete(job, result=result)
            except Exception as exc:  # pragma: no cover - job failure path
                self.queue.fail(job, str(exc))

    def stop(self) -> None:
        self._running = False

