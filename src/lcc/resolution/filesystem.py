"""
Local filesystem resolver scanning license artefacts.
"""

from __future__ import annotations

import fnmatch
import io
from pathlib import Path
from typing import Iterable, List, Optional

from lcc.config import LCCConfig
from lcc.models import Component, LicenseEvidence
from lcc.resolution.base import Resolver


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
        evidences: List[LicenseEvidence] = []
        for candidate in self._iter_license_files(root):
            if self._ignored(candidate, root, ignore_patterns):
                continue
            expression = self._detect_spdx_identifier(candidate)
            evidences.append(
                LicenseEvidence(
                    source="filesystem",
                    license_expression=expression or "UNKNOWN",
                    confidence=0.4 if expression else 0.2,
                    raw_data={"path": str(candidate.relative_to(root))},
                    url=None,
                )
            )
        return evidences

    def _resolve_root(self, component: Component) -> Optional[Path]:
        if component.path:
            return component.path.parent
        project_root = component.metadata.get("project_root")
        if project_root:
            return Path(project_root)
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

    def _load_gitignore(self, root: Path) -> List[str]:
        patterns: List[str] = []
        gitignore = root / ".gitignore"
        if not gitignore.exists():
            return patterns
        for line in gitignore.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            patterns.append(line)
        return patterns

    def _ignored(self, path: Path, root: Path, patterns: List[str]) -> bool:
        relative = path.relative_to(root)
        for pattern in patterns:
            if fnmatch.fnmatch(str(relative), pattern):
                return True
        return False

    def _detect_spdx_identifier(self, path: Path) -> Optional[str]:
        try:
            with path.open("r", encoding="utf-8") as handle:
                return self._extract_identifier(handle)
        except UnicodeDecodeError:
            with path.open("rb") as handle:
                content = handle.read().decode("utf-8", errors="ignore")
                return self._extract_identifier(io.StringIO(content))
        except OSError:
            return None

    def _extract_identifier(self, handle: io.TextIOBase) -> Optional[str]:
        for line in handle:
            line = line.strip()
            if "SPDX-License-Identifier:" in line:
                _, _, identifier = line.partition("SPDX-License-Identifier:")
                return identifier.strip()
        return None
