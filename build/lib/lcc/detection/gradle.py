"""
Gradle ecosystem detector implementation.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, Iterable, List, MutableMapping, Optional, Sequence, Tuple

from lcc.detection.base import Detector
from lcc.models import Component, ComponentType


DependencySpec = Tuple[str, Optional[str], Dict[str, object]]


class GradleDetector(Detector):
    """
    Detects Gradle components by parsing build.gradle and metadata files.
    """

    DEPENDENCY_REGEX = re.compile(
        r"""(?P<config>implementation|api|compileOnly|runtimeOnly|testImplementation|testCompile|kapt|annotationProcessor)\s*\(?["'](?P<notation>[^"']+)["']\)?""",
        re.IGNORECASE,
    )
    MAP_STYLE_REGEX = re.compile(
        r"""(?P<config>implementation|api|compileOnly|runtimeOnly|testImplementation|testCompile)\s*\(\s*(?P<map>['"].+?['"]\s*:\s*['"].+?['"].*?)\)""",
        re.IGNORECASE | re.DOTALL,
    )

    def __init__(self) -> None:
        super().__init__(name="gradle")

    def supports(self, project_root: Path) -> bool:  # pragma: no cover - simple predicate
        return any(
            (project_root / candidate).exists()
            for candidate in ("build.gradle", "build.gradle.kts", "settings.gradle", "settings.gradle.kts")
        ) or any(project_root.glob("**/build.gradle*"))

    def discover(self, project_root: Path) -> Sequence[Component]:
        components: Dict[Tuple[str, str], Component] = {}

        for build_file in self._collect_build_files(project_root):
            for name, version, metadata in self._parse_build_file(build_file):
                key = (name, version or "*")
                if key not in components:
                    components[key] = Component(
                        type=ComponentType.GRADLE,
                        name=name,
                        version=version or "*",
                        metadata={"sources": []},
                        path=build_file,
                    )
                    components[key].metadata["project_root"] = str(project_root)
                source_entry = {"source": str(build_file.relative_to(project_root)), **metadata}
                source_entry["project_root"] = str(project_root)
                components[key].metadata.setdefault("sources", []).append(source_entry)

        for lock_file in project_root.glob("**/gradle.lockfile"):
            for name, version, metadata in self._parse_lock_file(lock_file):
                key = (name, version or "*")
                if key not in components:
                    components[key] = Component(
                        type=ComponentType.GRADLE,
                        name=name,
                        version=version or "*",
                        metadata={"sources": []},
                        path=lock_file,
                    )
                    components[key].metadata["project_root"] = str(project_root)
                source_entry = {"source": str(lock_file.relative_to(project_root)), **metadata}
                source_entry["project_root"] = str(project_root)
                components[key].metadata.setdefault("sources", []).append(source_entry)

        return list(components.values())

    def _collect_build_files(self, project_root: Path) -> Iterable[Path]:
        candidates = [
            "build.gradle",
            "build.gradle.kts",
            "settings.gradle",
            "settings.gradle.kts",
        ]
        for candidate in candidates:
            path = project_root / candidate
            if path.exists():
                yield path
        for pattern in ("**/build.gradle", "**/build.gradle.kts"):
            yield from project_root.glob(pattern)

    def _parse_build_file(self, path: Path) -> Iterable[DependencySpec]:
        content = path.read_text(encoding="utf-8", errors="ignore")
        results: List[DependencySpec] = []

        for match in self.DEPENDENCY_REGEX.finditer(content):
            config = match.group("config")
            notation = match.group("notation")
            parts = notation.split(":")
            if len(parts) >= 3:
                group, artifact, version = parts[0], parts[1], parts[2]
            elif len(parts) == 2:
                group, artifact = parts
                version = None
            else:
                continue
            metadata: Dict[str, object] = {"configuration": config}
            if len(parts) > 3:
                metadata["classifier"] = parts[3]
            results.append((f"{group}:{artifact}", version, metadata))

        for match in self.MAP_STYLE_REGEX.finditer(content):
            mapping = match.group("map")
            attributes = self._parse_map_notation(mapping)
            group = attributes.get("group")
            name = attributes.get("name")
            version = attributes.get("version")
            if group and name:
                metadata = {k: v for k, v in attributes.items() if k not in {"group", "name", "version"}}
                metadata["configuration"] = match.group("config")
                results.append((f"{group}:{name}", version, metadata))

        return results

    def _parse_lock_file(self, path: Path) -> Iterable[DependencySpec]:
        results: List[DependencySpec] = []
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("=")
            if len(parts) != 2:
                continue
            coordinates, meta = parts
            coord_parts = coordinates.split(":")
            if len(coord_parts) < 3:
                continue
            group, artifact, version = coord_parts[:3]
            metadata: Dict[str, object] = {"source": "gradle.lockfile"}
            if meta:
                metadata["metadata"] = meta
            results.append((f"{group}:{artifact}", version, metadata))
        return results

    def _parse_map_notation(self, mapping: str) -> Dict[str, str]:
        result: Dict[str, str] = {}
        for fragment in mapping.split(","):
            if ":" not in fragment:
                continue
            key, value = fragment.split(":", 1)
            key = key.strip(" \"'")
            value = value.strip(" \"'")
            result[key] = value
        return result
