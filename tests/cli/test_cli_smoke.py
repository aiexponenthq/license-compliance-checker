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

"""Smoke tests for the CLI commands that read a scan result.

These invoke the real argument dispatch (`lcc.cli.main.main`) so a
handler signature that does not match the dispatch contract fails here
instead of only at runtime. They cover the SBOM generate/validate and
report generate commands, and prove the generated SBOMs validate.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from lcc.cli.main import main

SCAN_FIXTURE = {
    "scan_id": "smoke-001",
    "timestamp": "2025-01-01T12:00:00",
    "components": [
        {
            "type": "python",
            "name": "requests",
            "version": "2.31.0",
            "namespace": None,
            "metadata": {"description": "HTTP library"},
        }
    ],
    "component_results": [
        {
            "component": {"name": "requests", "version": "2.31.0"},
            "status": "pass",
            "licenses": [
                {
                    "source": "pypi",
                    "license_expression": "Apache-2.0",
                    "confidence": 0.95,
                }
            ],
            "violations": [],
            "warnings": [],
        }
    ],
}


@pytest.fixture
def scan_result(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Write a scan-result JSON fixture and isolate all path config to tmp."""
    for var in ("LCC_CACHE_DIR", "LCC_DB_PATH", "LCC_POLICY_DIR", "LCC_DATA_PATH"):
        monkeypatch.setenv(var, str(tmp_path / var.lower()))
    monkeypatch.setenv("LCC_LLM_PROVIDER", "disabled")

    path = tmp_path / "scan.json"
    path.write_text(json.dumps(SCAN_FIXTURE), encoding="utf-8")
    return path


def _generate(scan_result: Path, out: Path, sbom_format: str) -> int:
    return main(
        [
            "sbom",
            "generate",
            str(scan_result),
            "--output",
            str(out),
            "--format",
            sbom_format,
            "--sbom-format",
            "json",
            "--project-name",
            "smoke",
            "--project-version",
            "1.0.0",
        ]
    )


def test_sbom_generate_cyclonedx(scan_result: Path, tmp_path: Path) -> None:
    out = tmp_path / "cdx.json"
    assert _generate(scan_result, out, "cyclonedx") == 0
    doc = json.loads(out.read_text(encoding="utf-8"))
    assert doc["specVersion"] == "1.5"
    assert any(c["name"] == "requests" for c in doc.get("components", []))


def test_sbom_generate_spdx(scan_result: Path, tmp_path: Path) -> None:
    out = tmp_path / "spdx.json"
    assert _generate(scan_result, out, "spdx") == 0
    doc = json.loads(out.read_text(encoding="utf-8"))
    assert doc["name"] == "smoke 1.0.0"
    assert any(p["name"] == "requests" for p in doc.get("packages", []))


def test_sbom_validate_cyclonedx(scan_result: Path, tmp_path: Path) -> None:
    out = tmp_path / "cdx.json"
    assert _generate(scan_result, out, "cyclonedx") == 0
    assert main(["sbom", "validate", str(out), "--format", "cyclonedx"]) == 0


def test_sbom_validate_spdx(scan_result: Path, tmp_path: Path) -> None:
    out = tmp_path / "spdx.json"
    assert _generate(scan_result, out, "spdx") == 0
    assert main(["sbom", "validate", str(out), "--format", "spdx"]) == 0


def test_report_generate(scan_result: Path, tmp_path: Path) -> None:
    out = tmp_path / "report.html"
    rc = main(["report", "generate", str(scan_result), "--output", str(out), "--format", "html"])
    assert rc == 0
    assert out.exists() and out.stat().st_size > 0
