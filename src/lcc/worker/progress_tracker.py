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

"""Redis-based progress tracking for scan operations."""

import time

from redis.asyncio import Redis

from lcc.worker.progress import ScanProgress, ScanStage, get_stage_progress


class ProgressTracker:
    """Track scan progress in Redis with TTL."""

    def __init__(self, redis_client: Redis, scan_id: str):
        """
        Initialize progress tracker.

        Args:
            redis_client: Redis client instance
            scan_id: Scan ID to track progress for
        """
        self.redis = redis_client
        self.scan_id = scan_id
        self.key = f"scan:progress:{scan_id}"
        self.ttl = 3600  # 1 hour TTL
        self.start_time = time.time()

    async def update(
        self,
        stage: ScanStage,
        message: str,
        components_found: int = 0,
        components_resolved: int = 0,
        error: str | None = None
    ) -> None:
        """
        Update scan progress in Redis.

        Args:
            stage: Current scan stage
            message: Status message
            components_found: Number of components detected
            components_resolved: Number of components with resolved licenses
            error: Error message if any
        """
        elapsed = time.time() - self.start_time

        # Determine status from stage
        if stage == ScanStage.COMPLETE:
            status = "complete"
        elif stage == ScanStage.FAILED:
            status = "failed"
        elif stage == ScanStage.QUEUED:
            status = "queued"
        else:
            status = "running"

        progress = ScanProgress(
            scan_id=self.scan_id,
            status=status,
            current_stage=stage,
            progress_percent=get_stage_progress(stage),
            message=message,
            components_found=components_found,
            components_resolved=components_resolved,
            elapsed_seconds=round(elapsed, 2),
            error=error
        )

        # Store in Redis with TTL
        await self.redis.setex(
            self.key,
            self.ttl,
            progress.model_dump_json()
        )

    async def get(self) -> ScanProgress | None:
        """
        Get current progress from Redis.

        Returns:
            ScanProgress if found, None otherwise
        """
        data = await self.redis.get(self.key)
        if data is None:
            return None

        return ScanProgress.model_validate_json(data)

    async def clear(self) -> None:
        """Clear progress data from Redis."""
        await self.redis.delete(self.key)


async def get_scan_progress(redis_client: Redis, scan_id: str) -> ScanProgress | None:
    """
    Get scan progress from Redis.

    Args:
        redis_client: Redis client instance
        scan_id: Scan ID

    Returns:
        ScanProgress if found, None otherwise
    """
    key = f"scan:progress:{scan_id}"
    data = await redis_client.get(key)

    if data is None:
        return None

    return ScanProgress.model_validate_json(data)
