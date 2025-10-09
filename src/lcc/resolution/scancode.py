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
Wrapper around ScanCode Toolkit results.
"""

from __future__ import annotations

import json
import subprocess
import tempfile
from collections.abc import Iterable
from pathlib import Path

from lcc.cache import Cache
from lcc.config import LCCConfig
from lcc.models import Component, LicenseEvidence
from lcc.resolution.base import Resolver


class ScanCodeResolver(Resolver):
    """
    Executes ScanCode Toolkit to obtain deep license findings.
    """

    def __init__(self, cache: Cache, config: LCCConfig, binary: str = "scancode") -> None:
        super().__init__(name="scancode")
        self.cache = cache
        self.config = config
        self.binary = binary

    def resolve(self, component: Component) -> Iterable[LicenseEvidence]:
        target_path = self._locate_source_path(component)
        if not target_path or not target_path.exists():
            return []

        cache_key = self._cache_key(target_path)
        payload = self.cache.get(cache_key)
        if payload is None:
            payload = self._run_scancode(target_path)
            if payload is not None:
                self.cache.set(cache_key, payload)

        if not payload:
            return []

        return self._extract_evidences(payload)

    def _locate_source_path(self, component: Component) -> Path | None:
        path_value = component.metadata.get("source_path")
        if isinstance(path_value, str):
            return Path(path_value)
        for source in component.metadata.get("sources", []):
            if isinstance(source, dict) and isinstance(source.get("path"), str):
                return Path(source["path"])
        return None

    def _cache_key(self, path: Path) -> str:
        try:
            mtime = path.stat().st_mtime
        except FileNotFoundError:
            mtime = 0
        return f"scancode::{path.resolve()}::{mtime}"

    def _run_scancode(self, target_path: Path) -> dict | None:
        timeout = float(self.config.timeouts.get("scancode", self.config.timeouts.get("default", 600.0)))
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "scancode.json"
            command = [
                self.binary,
                "--quiet",
                "--license",
                "--json-pp",
                str(output_path),
                str(target_path),
            ]
            try:
                result = subprocess.run(
                    command,
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                )
            except FileNotFoundError:
                return None
            except subprocess.TimeoutExpired:
                return None

            if result.returncode != 0:
                return None

            try:
                return json.loads(output_path.read_text(encoding="utf-8"))
            except (FileNotFoundError, json.JSONDecodeError):
                return None

    def _extract_evidences(self, payload: dict) -> Iterable[LicenseEvidence]:
        findings: dict[str, LicenseEvidence] = {}
        files = payload.get("files", [])
        for file_entry in files or []:
            licenses = file_entry.get("licenses", [])
            for license_entry in licenses or []:
                expression = license_entry.get("spdx_expression") or license_entry.get("license_expression")
                if not isinstance(expression, str) or not expression:
                    continue
                score = license_entry.get("score")
                if isinstance(score, (int, float)):
                    confidence = max(0.0, min(1.0, float(score) / 100.0))
                else:
                    confidence = 0.5
                existing = findings.get(expression)
                if existing and existing.confidence >= confidence:
                    continue
                findings[expression] = LicenseEvidence(
                    source="scancode",
                    license_expression=expression,
                    confidence=confidence,
                    raw_data=license_entry,
                    url=None,
                )
        return list(findings.values())
