"""Scan progress tracking models and utilities."""

from enum import Enum
from typing import Optional
from pydantic import BaseModel


class ScanStage(str, Enum):
    """Stages of a scan operation."""
    QUEUED = "queued"
    INITIALIZING = "initializing"
    CLONING = "cloning"
    DETECTING_COMPONENTS = "detecting_components"
    PARSING_MANIFESTS = "parsing_manifests"
    RESOLVING_LICENSES = "resolving_licenses"
    EVALUATING_POLICY = "evaluating_policy"
    GENERATING_REPORT = "generating_report"
    COMPLETE = "complete"
    FAILED = "failed"


class ScanProgress(BaseModel):
    """Progress information for a running scan."""
    scan_id: str
    status: str  # queued, running, complete, failed
    current_stage: ScanStage
    progress_percent: int  # 0-100
    message: str
    components_found: int = 0
    components_resolved: int = 0
    elapsed_seconds: float = 0.0
    error: Optional[str] = None


# Stage to progress percentage mapping
STAGE_PROGRESS = {
    ScanStage.QUEUED: 0,
    ScanStage.INITIALIZING: 5,
    ScanStage.CLONING: 15,
    ScanStage.DETECTING_COMPONENTS: 30,
    ScanStage.PARSING_MANIFESTS: 50,
    ScanStage.RESOLVING_LICENSES: 70,
    ScanStage.EVALUATING_POLICY: 85,
    ScanStage.GENERATING_REPORT: 95,
    ScanStage.COMPLETE: 100,
    ScanStage.FAILED: 0,
}


def get_stage_progress(stage: ScanStage) -> int:
    """Get progress percentage for a given stage."""
    return STAGE_PROGRESS.get(stage, 0)
