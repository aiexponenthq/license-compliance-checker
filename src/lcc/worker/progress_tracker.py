"""Redis-based progress tracking for scan operations."""

import json
import time
from typing import Optional
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
        error: Optional[str] = None
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
    
    async def get(self) -> Optional[ScanProgress]:
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


async def get_scan_progress(redis_client: Redis, scan_id: str) -> Optional[ScanProgress]:
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
