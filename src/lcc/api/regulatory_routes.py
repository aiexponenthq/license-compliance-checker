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

"""
EU AI Act regulatory compliance API endpoints.

Provides endpoints for running EU AI Act assessments on completed scans
and downloading compliance packs as ZIP archives.
"""

from __future__ import annotations

import io
import tempfile
import zipfile
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from lcc.auth.core import User, get_current_active_user
from lcc.database.repository import ScanRepository
from lcc.database.session import get_db
from lcc.models import (
    Component,
    ComponentFinding,
    ComponentType,
    LicenseEvidence,
)
from lcc.regulatory.eu_ai_act import EUAIActAssessor
from lcc.regulatory.reporter import generate_compliance_pack

router = APIRouter(prefix="/regulatory", tags=["regulatory"])


def _get_repository(session: AsyncSession = Depends(get_db)) -> ScanRepository:
    return ScanRepository(session)


def _deserialize_findings(report_data: dict) -> list[ComponentFinding]:
    """Reconstruct ComponentFinding objects from stored report JSON."""
    findings: list[ComponentFinding] = []
    for item in report_data.get("findings", []):
        component_data = item.get("component", {})
        component_type = component_data.get("type", ComponentType.GENERIC.value)
        try:
            component_type_enum = ComponentType(component_type)
        except ValueError:
            component_type_enum = ComponentType.GENERIC

        component = Component(
            type=component_type_enum,
            name=component_data.get("name", ""),
            version=component_data.get("version", "*"),
            namespace=component_data.get("namespace"),
            path=Path(component_data["path"]) if component_data.get("path") else None,
            metadata=component_data.get("metadata", {}),
        )
        evidences = [
            LicenseEvidence(
                source=evidence.get("source", ""),
                license_expression=evidence.get("license_expression", "UNKNOWN"),
                confidence=float(evidence.get("confidence", 0.0)),
                raw_data=evidence.get("raw_data", {}),
                url=evidence.get("url"),
            )
            for evidence in item.get("evidences", [])
        ]
        finding = ComponentFinding(
            component=component,
            evidences=evidences,
            resolved_license=item.get("resolved_license"),
            confidence=float(item.get("confidence", 0.0)),
        )
        findings.append(finding)
    return findings


@router.get("/assess/{scan_id}")
async def assess_scan(
    scan_id: str,
    repo: ScanRepository = Depends(_get_repository),
    current_user: User = Depends(get_current_active_user),
) -> JSONResponse:
    """Run EU AI Act assessment on a completed scan."""
    scan = await repo.get_scan(scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    if not scan.report:
        raise HTTPException(
            status_code=400,
            detail="Scan has no report data. Ensure the scan has completed successfully.",
        )

    # Deserialize findings from the stored report
    findings = _deserialize_findings(scan.report)

    # Run EU AI Act assessment
    assessor = EUAIActAssessor()
    report = assessor.assess_scan(findings)

    return JSONResponse(content=report.to_dict())


@router.get("/compliance-pack/{scan_id}")
async def download_compliance_pack(
    scan_id: str,
    repo: ScanRepository = Depends(_get_repository),
    current_user: User = Depends(get_current_active_user),
) -> StreamingResponse:
    """Generate and download EU AI Act Compliance Pack as a ZIP file."""
    scan = await repo.get_scan(scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    if not scan.report:
        raise HTTPException(
            status_code=400,
            detail="Scan has no report data. Ensure the scan has completed successfully.",
        )

    # Deserialize findings and build the canonical four-file compliance pack, so
    # the API download and `lcc compliance-pack` produce identical artifacts.
    findings = _deserialize_findings(scan.report)
    report = EUAIActAssessor().assess_scan(findings)

    zip_buffer = io.BytesIO()
    with tempfile.TemporaryDirectory() as tmp:
        pack_dir = generate_compliance_pack(report, findings, Path(tmp))
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for entry in sorted(pack_dir.iterdir()):
                zf.write(entry, arcname=entry.name)

    zip_buffer.seek(0)

    filename = f"eu-ai-act-compliance-pack-{scan_id[:8]}.zip"
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )
