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
Async database repository for Scan operations.
"""
from datetime import datetime
from typing import Any

from sqlalchemy import delete, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from lcc.database.models import Component, Scan


class ScanRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_scan(self, scan: Scan) -> Scan:
        self.session.add(scan)
        await self.session.commit()
        await self.session.refresh(scan)
        return scan

    async def update_scan(self, scan_id: str, **kwargs) -> Scan | None:
        scan = await self.get_scan(scan_id)
        if not scan:
            return None

        for key, value in kwargs.items():
            setattr(scan, key, value)

        if "updated_at" not in kwargs:
            scan.updated_at = datetime.utcnow()

        await self.session.commit()
        await self.session.refresh(scan)
        return scan

    async def get_scan(self, scan_id: str) -> Scan | None:
        stmt = select(Scan).where(Scan.id == scan_id).options(selectinload(Scan.components))
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def list_scans(self, limit: int = 50, offset: int = 0) -> list[Scan]:
        stmt = select(Scan).order_by(desc(Scan.created_at)).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def delete_all_scans(self) -> int:
        """Delete all scans and their associated components."""
        # Delete components first (cascade should handle this, but explicit is safer)
        await self.session.execute(delete(Component))

        # Delete scans
        result = await self.session.execute(delete(Scan))
        await self.session.commit()
        return result.rowcount

    async def get_dashboard_summary(self) -> dict[str, Any]:
        # Total Scans
        total_scans = await self.session.scalar(select(func.count(Scan.id)))

        # Unique Projects
        unique_projects = await self.session.scalar(select(func.count(func.distinct(Scan.project_name))))

        # Status counts
        violations = await self.session.scalar(select(func.sum(Scan.violations_count))) or 0
        warnings = await self.session.scalar(select(func.sum(Scan.warnings_count))) or 0

        # Pending (running/queued)
        pending = await self.session.scalar(
            select(func.count(Scan.id)).where(Scan.status.in_(["queued", "running"]))
        ) or 0

        # High Risk Projects (latest scan is violation)
        # This is complex in SQL, simplifying for now: count scans with violation status
        # Ideally we want distinct projects where the *latest* scan is a violation.
        # For MVP, let's just count scans with status='violation' or 'failed'
        # But better to stick to the requirement "High Risk Projects".

        # Subquery to get latest scan per project
        subq = (
            select(
                Scan.project_name,
                func.max(Scan.created_at).label("max_created_at")
            )
            .group_by(Scan.project_name)
            .subquery()
        )

        stmt_latest = (
            select(Scan)
            .join(subq, (Scan.project_name == subq.c.project_name) & (Scan.created_at == subq.c.max_created_at))
        )
        latest_scans_result = await self.session.execute(stmt_latest)
        latest_scans = latest_scans_result.scalars().all()

        high_risk_count = sum(1 for s in latest_scans if s.violations_count > 0)

        # License Distribution (from latest scans)
        license_counts: dict[str, int] = {}
        for scan in latest_scans:
            if scan.report and "licenseDistribution" in scan.report:
                # If report has pre-calculated distribution
                for item in scan.report["licenseDistribution"]:
                    lic = item.get("license", "UNKNOWN")
                    count = item.get("count", 0)
                    license_counts[lic] = license_counts.get(lic, 0) + count
            else:
                # Fallback: aggregate from components if loaded (might be expensive if not eager loaded)
                # For now, assume report JSON has it or skip
                pass

        distribution = [
            {"license": k, "count": v}
            for k, v in sorted(license_counts.items(), key=lambda x: x[1], reverse=True)
        ]

        # Trend (last 6 months)
        # Simplified: just get last 6 months of scans and aggregate in python
        # or use date truncation in SQL (dialect specific).
        # Let's use Python aggregation for DB independence (SQLite/PG)
        trend_data = []
        # ... implementation of trend omitted for brevity, can add if needed

        return {
            "totalScans": total_scans,
            "totalProjects": unique_projects,
            "totalViolations": violations,
            "totalWarnings": warnings,
            "pendingScans": pending,
            "highRiskProjects": high_risk_count,
            "licenseDistribution": distribution,
            "trend": trend_data,
        }
