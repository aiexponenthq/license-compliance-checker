"""
Background tasks for the LCC worker.
"""
import asyncio
import shutil
import tempfile
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from lcc.config import load_config
from lcc.database.session import AsyncSessionLocal
from lcc.database.repository import ScanRepository
from lcc.database.models import Scan, Component
from lcc.factory import build_detectors, build_resolvers
from lcc.scanner import Scanner
from lcc.cache import Cache
from lcc.utils.git import clone_github_repo

async def run_scan_task(ctx: Dict[str, Any], scan_id: str, repo_url: Optional[str] = None, path: Optional[str] = None) -> None:
    """
    Execute a license scan in the background.
    """
    config = load_config()
    cache = Cache(config)
    
    # Build scanner
    detectors = build_detectors()
    resolvers = build_resolvers(config, cache)
    scanner = Scanner(detectors, resolvers, config)
    
    async with AsyncSessionLocal() as session:
        repo = ScanRepository(session)
        scan = await repo.get_scan(scan_id)
        
        if not scan:
            print(f"Scan {scan_id} not found in database.")
            return

        # Update status to running
        await repo.update_scan(scan_id, status="running")
        
        temp_dir = None
        project_path = None
        
        try:
            if repo_url:
                temp_dir = tempfile.mkdtemp(prefix="lcc_repo_")
                clone_github_repo(repo_url, Path(temp_dir))
                project_path = Path(temp_dir)
            elif path:
                project_path = Path(path)
                if not project_path.exists():
                    raise FileNotFoundError(f"Path {path} does not exist")
            else:
                raise ValueError("Neither repo_url nor path provided")

            # Run synchronous scan in a thread pool to avoid blocking the async worker
            # Since Scanner.scan is blocking, we wrap it.
            loop = asyncio.get_running_loop()
            report = await loop.run_in_executor(None, scanner.scan, project_path)
            
            # Process results
            # Convert report findings to Component models
            components = []
            for finding in report.findings:
                comp = Component(
                    scan_id=scan_id,
                    type=finding.component.type.value,
                    name=finding.component.name,
                    version=finding.component.version,
                    license_expression=finding.resolved_license,
                    license_confidence=finding.confidence,
                    metadata_=finding.component.metadata,
                    evidence=[{"source": e.source, "license": e.license_expression, "confidence": e.confidence} for e in finding.evidences]
                )
                components.append(comp)
            
            # Update scan with results
            # We need to serialize the report summary and full report
            # For now, just storing basic stats and the full JSON report
            
            # Note: The original report object is complex. We might want to serialize it to dict.
            # Assuming report has a to_dict or similar, or we construct it.
            # The existing code uses a JSONReporter or similar.
            # Let's just store the raw findings count for now and the full report as a dict if possible.
            # Since ScanReport is a dataclass, we can use asdict (if imported) or just rely on what we have.
            
            # Simplified report storage for MVP
            report_dict = {
                "findings": [
                    {
                        "component": {
                            "name": f.component.name,
                            "version": f.component.version,
                            "type": f.component.type.value
                        },
                        "resolved_license": f.resolved_license,
                        "confidence": f.confidence
                    } for f in report.findings
                ],
                "summary": {
                    "component_count": report.summary.component_count,
                    "violations": report.summary.violations
                }
            }

            scan.components = components
            scan.status = "complete"
            scan.components_count = report.summary.component_count
            scan.violations_count = report.summary.violations
            scan.report = report_dict
            scan.duration_seconds = report.summary.duration_seconds
            
            await session.commit()

        except Exception as e:
            traceback.print_exc()
            await repo.update_scan(scan_id, status="failed", report={"error": str(e)})
        finally:
            if temp_dir and Path(temp_dir).exists():
                shutil.rmtree(temp_dir)
