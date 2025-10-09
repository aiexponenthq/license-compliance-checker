from __future__ import annotations

import unittest

import fakeredis

from lcc.config import LCCConfig
from lcc.jobs.queue import JobQueue, JobQueueWorker, QueueError


class JobQueueTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fake = fakeredis.FakeRedis(decode_responses=True)

    def _queue(self) -> JobQueue:
        config = LCCConfig()
        config.redis_url = "redis://localhost"
        from lcc.jobs import queue as queue_module

        original_from_url = queue_module.redis.Redis.from_url  # type: ignore[attr-defined]
        queue_module.redis.Redis.from_url = lambda *args, **kwargs: self.fake  # type: ignore[assignment]
        self.addCleanup(lambda: setattr(queue_module.redis.Redis, "from_url", original_from_url))  # type: ignore[attr-defined]
        return JobQueue(config)

    def test_enqueue_and_fetch(self) -> None:
        queue = self._queue()
        job = queue.enqueue("scan", {"path": "./"})
        fetched = queue.fetch()
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.id, job.id)
        queue.complete(fetched)
        self.assertEqual(queue.get_job(job.id)["status"], "completed")

    def test_retry_and_dead_letter(self) -> None:
        queue = self._queue()
        job = queue.enqueue("scan", {}, max_retries=1)
        fetched = queue.fetch()
        queue.fail(fetched, "error")
        fetched2 = queue.fetch()
        queue.fail(fetched2, "error")
        dead = queue.stats()["dead"]
        self.assertEqual(dead, 1)
        requeued = queue.requeue_dead()
        self.assertEqual(requeued, 1)


if __name__ == "__main__":
    unittest.main()
