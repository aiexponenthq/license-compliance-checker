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

"""CLI smoke tests for the Article 53 assess / compliance-pack commands (H5)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from lcc.cli.main import main

SCAN_REPORT = {
    "findings": [
        {
            "component": {
                "type": "ai_model",
                "name": "llama-model",
                "version": "unknown",
                "namespace": None,
                "metadata": {"license_from_card": "llama3.1"},
            },
            "evidences": [
                {
                    "source": "ai-model-card",
                    "license_expression": "LicenseRef-llama-3.1",
                    "confidence": 0.95,
                    "raw_data": {},
                    "url": None,
                }
            ],
            "resolved_license": "LicenseRef-llama-3.1",
            "confidence": 0.95,
        }
    ],
    "summary": {
        "component_count": 1,
        "violations": 0,
        "duration_seconds": 0.0,
        "context": {},
    },
    "errors": [],
}

PACK_FILES = {
    "eu_ai_act_report.json",
    "eu_ai_act_report.html",
    "training_data_summary.json",
    "copyright_policy_template.md",
}


@pytest.fixture
def scan_report(tmp_path: Path) -> Path:
    path = tmp_path / "scan.json"
    path.write_text(json.dumps(SCAN_REPORT), encoding="utf-8")
    return path


def test_assess_console(scan_report: Path) -> None:
    assert main(["assess", str(scan_report)]) == 0


def test_assess_json_to_file(scan_report: Path, tmp_path: Path) -> None:
    out = tmp_path / "assessment.json"
    assert main(["assess", str(scan_report), "--format", "json", "-o", str(out)]) == 0
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["summary"]["total_ai_components"] == 1


def test_assess_html_to_file(scan_report: Path, tmp_path: Path) -> None:
    out = tmp_path / "assessment.html"
    assert main(["assess", str(scan_report), "--format", "html", "-o", str(out)]) == 0
    assert "<html" in out.read_text(encoding="utf-8").lower()


def test_compliance_pack_produces_four_file_spec(scan_report: Path, tmp_path: Path) -> None:
    out = tmp_path / "packs"
    out.mkdir()
    assert main(["compliance-pack", str(scan_report), "-o", str(out)]) == 0
    pack_dirs = list(out.glob("eu-ai-act-compliance-pack-*"))
    assert len(pack_dirs) == 1
    produced = {p.name for p in pack_dirs[0].iterdir()}
    assert produced == PACK_FILES
