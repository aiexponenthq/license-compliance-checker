"""Scan progress tracking for real-time updates."""

from __future__ import annotations

import time
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class ScanStage(str, Enum):
    """Scan execution stages."""
    QUEUED = "queued"
    CLONING = "cloning"
    DETECTING = "detecting"
    PARSING = "parsing"
    RESOLVING = "resolving"
    EVALUATING = "evaluating"
    REPORTING = "reporting"
    COMPLETE = "complete"
    FAILED = "failed"


class StageInfo(BaseModel):
    """Information about a completed stage."""
    stage: ScanStage
    name: str
    duration_seconds: float
    completed_at: datetime


class ScanProgress(BaseModel):
    """Scan progress information."""
    scan_id: str
    status: ScanStage
    stage_name: str
    progress_percent: int = Field(ge=0, le=100)
    elapsed_seconds: float
    estimated_remaining_seconds: Optional[float] = None

    # Stage tracking
    stages_completed: List[StageInfo] = Field(default_factory=list)
    current_stage_start: Optional[datetime] = None

    # Component tracking
    components_found: int = 0
    components_resolved: int = 0

    # Messages
    current_message: Optional[str] = None
    error_message: Optional[str] = None

    # Timestamps
    started_at: datetime
    updated_at: datetime


class ProgressTracker:
    """Track scan progress in memory."""

    def __init__(self):
        self._progress: Dict[str, ScanProgress] = {}

    def start_scan(self, scan_id: str) -> None:
        """Initialize progress tracking for a scan."""
        now = datetime.now(timezone.utc)
        self._progress[scan_id] = ScanProgress(
            scan_id=scan_id,
            status=ScanStage.QUEUED,
            stage_name="Scan Queued",
            progress_percent=0,
            elapsed_seconds=0.0,
            started_at=now,
            updated_at=now,
            current_stage_start=now
        )

    def update_stage(
        self,
        scan_id: str,
        stage: ScanStage,
        stage_name: str,
        message: Optional[str] = None
    ) -> None:
        """Update current scan stage."""
        if scan_id not in self._progress:
            return

        progress = self._progress[scan_id]
        now = datetime.now(timezone.utc)

        # Complete previous stage
        if progress.current_stage_start and progress.status != stage:
            duration = (now - progress.current_stage_start).total_seconds()
            progress.stages_completed.append(StageInfo(
                stage=progress.status,
                name=progress.stage_name,
                duration_seconds=duration,
                completed_at=now
            ))

        # Update to new stage
        progress.status = stage
        progress.stage_name = stage_name
        progress.current_stage_start = now
        progress.updated_at = now
        progress.elapsed_seconds = (now - progress.started_at).total_seconds()

        if message:
            progress.current_message = message

        # Update progress percentage based on stage
        stage_progress = {
            ScanStage.QUEUED: 0,
            ScanStage.CLONING: 10,
            ScanStage.DETECTING: 25,
            ScanStage.PARSING: 40,
            ScanStage.RESOLVING: 60,
            ScanStage.EVALUATING: 80,
            ScanStage.REPORTING: 90,
            ScanStage.COMPLETE: 100,
            ScanStage.FAILED: 0
        }
        progress.progress_percent = stage_progress.get(stage, 0)

        # Estimate remaining time based on average stage durations
        progress.estimated_remaining_seconds = self._estimate_remaining(progress)

    def update_components(
        self,
        scan_id: str,
        found: Optional[int] = None,
        resolved: Optional[int] = None
    ) -> None:
        """Update component counts."""
        if scan_id not in self._progress:
            return

        progress = self._progress[scan_id]
        if found is not None:
            progress.components_found = found
        if resolved is not None:
            progress.components_resolved = resolved

        progress.updated_at = datetime.now(timezone.utc)

        # Update progress within resolving stage
        if progress.status == ScanStage.RESOLVING and progress.components_found > 0:
            resolve_progress = (progress.components_resolved / progress.components_found) * 20
            progress.progress_percent = 60 + int(resolve_progress)

    def set_error(self, scan_id: str, error: str) -> None:
        """Mark scan as failed with error."""
        if scan_id not in self._progress:
            return

        progress = self._progress[scan_id]
        progress.status = ScanStage.FAILED
        progress.stage_name = "Scan Failed"
        progress.error_message = error
        progress.updated_at = datetime.now(timezone.utc)
        progress.progress_percent = 0

    def complete_scan(self, scan_id: str) -> None:
        """Mark scan as complete."""
        self.update_stage(
            scan_id,
            ScanStage.COMPLETE,
            "Scan Complete",
            "Scan completed successfully"
        )

    def get_progress(self, scan_id: str) -> Optional[ScanProgress]:
        """Get current progress for a scan."""
        progress = self._progress.get(scan_id)
        if progress:
            # Update elapsed time
            now = datetime.now(timezone.utc)
            progress.elapsed_seconds = (now - progress.started_at).total_seconds()
            progress.updated_at = now
        return progress

    def remove_progress(self, scan_id: str) -> None:
        """Remove progress tracking (after completion)."""
        self._progress.pop(scan_id, None)

    def _estimate_remaining(self, progress: ScanProgress) -> Optional[float]:
        """Estimate remaining time based on completed stages."""
        # Average durations for each stage (in seconds)
        avg_durations = {
            ScanStage.CLONING: 30.0,
            ScanStage.DETECTING: 15.0,
            ScanStage.PARSING: 20.0,
            ScanStage.RESOLVING: 60.0,
            ScanStage.EVALUATING: 10.0,
            ScanStage.REPORTING: 5.0
        }

        # Stages still to complete
        all_stages = [
            ScanStage.CLONING,
            ScanStage.DETECTING,
            ScanStage.PARSING,
            ScanStage.RESOLVING,
            ScanStage.EVALUATING,
            ScanStage.REPORTING
        ]

        try:
            current_index = all_stages.index(progress.status)
            remaining_stages = all_stages[current_index + 1:]
        except (ValueError, IndexError):
            return None

        # Sum up estimated time for remaining stages
        estimated = sum(avg_durations.get(stage, 0) for stage in remaining_stages)

        # Add time for current stage completion (assume 50% done)
        if progress.current_stage_start:
            elapsed_in_stage = (datetime.now(timezone.utc) - progress.current_stage_start).total_seconds()
            current_stage_estimate = avg_durations.get(progress.status, 0)
            estimated += max(0, current_stage_estimate - elapsed_in_stage)

        return max(1.0, estimated)


# Global progress tracker instance
progress_tracker = ProgressTracker()
