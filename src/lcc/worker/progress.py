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

"""Scan progress tracking models and utilities."""

from enum import StrEnum

from pydantic import BaseModel


class ScanStage(StrEnum):
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
    error: str | None = None


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
