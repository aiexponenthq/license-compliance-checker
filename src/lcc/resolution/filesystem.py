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
Local filesystem resolver scanning license artefacts.
"""

from __future__ import annotations

import fnmatch
import io
import re
from collections.abc import Iterable
from pathlib import Path

from lcc.config import LCCConfig
from lcc.models import Component, LicenseEvidence
from lcc.resolution.base import Resolver

# License signatures, most specific first. Each is matched on word
# boundaries so a short identifier (GPL) is not detected inside a longer one
# (LGPL, AGPL), and full license names are preferred over bare abbreviations.
_LICENSE_SIGNATURES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"gnu affero general public license"), "AGPL"),
    (re.compile(r"gnu lesser general public license"), "LGPL"),
    (re.compile(r"gnu general public license"), "GPL"),
    (re.compile(r"apache license"), "Apache-2.0"),
    (re.compile(r"apache software license"), "Apache-2.0"),
    (re.compile(r"\bmit license\b"), "MIT"),
    (re.compile(r"bsd 3-clause|\bbsd-3-clause\b"), "BSD-3-Clause"),
    (re.compile(r"bsd 2-clause|\bbsd-2-clause\b"), "BSD-2-Clause"),
    (re.compile(r"mozilla public license"), "MPL-2.0"),
    (re.compile(r"eclipse public license"), "EPL-2.0"),
    (re.compile(r"creative commons"), "CC"),
    (re.compile(r"\bisc license\b"), "ISC"),
    (re.compile(r"\bthe unlicense\b|\bunlicense\b"), "Unlicense"),
    (re.compile(r"\bagpl\b"), "AGPL"),
    (re.compile(r"\blgpl\b"), "LGPL"),
    (re.compile(r"\bgpl\b"), "GPL"),
]


class FileSystemResolver(Resolver):
    """
    Scans local directories for common license artefacts.
    """

    LICENSE_GLOBS = [
        "LICENSE",
        "LICENSE.*",
        "LICENCE",
        "COPYING*",
        "NOTICE*",
        "*.license",
        "README*",
    ]

    def __init__(self, config: LCCConfig) -> None:
        super().__init__(name="filesystem")
        self.config = config

    def resolve(self, component: Component) -> Iterable[LicenseEvidence]:
        root = self._resolve_root(component)
        if root is None or not root.exists():
            return []

        ignore_patterns = self._load_gitignore(root)
        evidences: list[LicenseEvidence] = []
        for candidate in self._iter_license_files(root):
            if self._ignored(candidate, root, ignore_patterns):
                continue
            expression = self._detect_spdx_identifier(candidate)
            # Higher confidence if we detected a specific license (not UNKNOWN)
            confidence = 0.7 if expression and expression != "UNKNOWN" else 0.2
            evidences.append(
                LicenseEvidence(
                    source="filesystem",
                    license_expression=expression or "UNKNOWN",
                    confidence=confidence,
                    raw_data={"path": str(candidate.relative_to(root))},
                    url=None,
                )
            )
        return evidences

    def _resolve_root(self, component: Component) -> Path | None:
        if component.path:
            return Path(component.path).parent
        # Do not fallback to project_root for components without a path (e.g. dependencies).
        # This prevents scanning the entire repo for external packages.
        return None

    def _iter_license_files(self, root: Path) -> Iterable[Path]:
        seen: set[Path] = set()
        for pattern in self.LICENSE_GLOBS:
            for candidate in root.glob(pattern):
                if candidate not in seen:
                    seen.add(candidate)
                    yield candidate
        for pattern in self.LICENSE_GLOBS:
            for candidate in root.glob(f"**/{pattern}"):
                if candidate not in seen:
                    seen.add(candidate)
                    yield candidate

    def _load_gitignore(self, root: Path) -> list[str]:
        patterns: list[str] = []
        gitignore = root / ".gitignore"
        if not gitignore.exists():
            return patterns
        for line in gitignore.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            patterns.append(line)
        return patterns

    def _ignored(self, path: Path, root: Path, patterns: list[str]) -> bool:
        # Check explicit config exclusions (glob patterns)
        if self.config.exclude_patterns:
            for pattern in self.config.exclude_patterns:
                if path.match(pattern):
                    return True
                try:
                    if path.relative_to(root).match(pattern):
                        return True
                except ValueError:
                    pass

        relative = path.relative_to(root)
        return any(fnmatch.fnmatch(str(relative), pattern) for pattern in patterns)

    def _detect_spdx_identifier(self, path: Path) -> str | None:
        try:
            with path.open("r", encoding="utf-8") as handle:
                return self._extract_identifier(handle)
        except UnicodeDecodeError:
            with path.open("rb") as handle:
                content = handle.read().decode("utf-8", errors="ignore")
                return self._extract_identifier(io.StringIO(content))
        except OSError:
            return None

    def _extract_identifier(self, handle: io.TextIOBase) -> str | None:
        # Read first 2000 characters to detect license
        content_chars = []
        char_count = 0
        for line in handle:
            content_chars.append(line)
            char_count += len(line)
            if char_count > 2000:
                break

        content = "".join(content_chars)
        content_lower = content.lower()

        # First, check for SPDX identifier
        for line in content_chars:
            line = line.strip()
            if "SPDX-License-Identifier:" in line:
                _, _, identifier = line.partition("SPDX-License-Identifier:")
                return identifier.strip()

        # Identify the license from its signatures. The signature that appears
        # earliest in the text wins, because a LICENSE file leads with its own
        # license name; a license merely referenced later (for example a bundled
        # dependency) does not override the file's declared license.
        best_position: int | None = None
        best_id: str | None = None
        for regex, spdx_id in _LICENSE_SIGNATURES:
            match = regex.search(content_lower)
            if match is not None and (best_position is None or match.start() < best_position):
                best_position = match.start()
                best_id = spdx_id

        return best_id
