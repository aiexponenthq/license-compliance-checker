"""
Maven ecosystem detector implementation.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from lcc.detection.base import Detector
from lcc.models import Component, ComponentType


DependencySpec = Tuple[str, Optional[str], Dict[str, object]]


class MavenDetector(Detector):
    """
    Detects Maven components by parsing pom.xml files.
    """

    def __init__(self) -> None:
        super().__init__(name="maven")

    def supports(self, project_root: Path) -> bool:  # pragma: no cover - simple predicate
        return any(project_root.glob("pom.xml")) or any(project_root.glob("**/pom.xml"))

    def discover(self, project_root: Path) -> Sequence[Component]:
        visited: set[Path] = set()
        components: Dict[Tuple[str, str], Component] = {}

        for pom_path in self._walk_poms(project_root):
            if pom_path in visited:
                continue
            visited.add(pom_path)
            for name, version, metadata in self._parse_pom(pom_path):
                key = (name, version or "*")
                if key not in components:
                    components[key] = Component(
                        type=ComponentType.JAVA,
                        name=name,
                        version=version or "*",
                        metadata={"sources": []},
                        path=pom_path,
                    )
                    components[key].metadata["project_root"] = str(project_root)
                source_entry = {"source": str(pom_path.relative_to(project_root)), **metadata}
                source_entry["project_root"] = str(project_root)
                components[key].metadata.setdefault("sources", []).append(source_entry)

        return list(components.values())

    def _walk_poms(self, project_root: Path) -> Iterable[Path]:
        for pom in project_root.glob("pom.xml"):
            yield pom
        for pom in project_root.glob("**/pom.xml"):
            yield pom

    def _parse_pom(self, path: Path) -> Iterable[DependencySpec]:
        try:
            tree = ET.parse(path)
        except ET.ParseError:
            return []
        root = tree.getroot()
        namespace = self._detect_namespace(root)

        data: List[DependencySpec] = []

        project_group = self._text(root.find(self._ns(namespace, "groupId")))
        project_artifact = self._text(root.find(self._ns(namespace, "artifactId")))
        project_version = self._text(root.find(self._ns(namespace, "version")))

        parent = root.find(self._ns(namespace, "parent"))
        if parent is not None:
            if not project_group:
                project_group = self._text(parent.find(self._ns(namespace, "groupId")))
            if not project_version:
                project_version = self._text(parent.find(self._ns(namespace, "version")))

        if project_group and project_artifact:
            metadata = {
                "type": "project",
                "packaging": self._text(root.find(self._ns(namespace, "packaging"))) or "jar",
            }
            data.append((f"{project_group}:{project_artifact}", project_version, metadata))

        for deps in root.findall(self._ns(namespace, "dependencies")):
            data.extend(self._parse_dependencies(deps, namespace, scope="runtime"))

        dep_mgmt = root.find(self._ns(namespace, "dependencyManagement"))
        if dep_mgmt is not None:
            for deps in dep_mgmt.findall(self._ns(namespace, "dependencies")):
                data.extend(self._parse_dependencies(deps, namespace, scope="managed"))

        build = root.find(self._ns(namespace, "build"))
        if build is not None:
            plugins = build.find(self._ns(namespace, "plugins"))
            if plugins is not None:
                data.extend(self._parse_dependencies(plugins, namespace, scope="plugin"))

        return data

    def _parse_dependencies(
        self,
        parent: ET.Element,
        namespace: Optional[str],
        scope: str,
    ) -> Iterable[DependencySpec]:
        dependencies = []
        for dependency in parent.findall(self._ns(namespace, "dependency")):
            group = self._text(dependency.find(self._ns(namespace, "groupId")))
            artifact = self._text(dependency.find(self._ns(namespace, "artifactId")))
            version = self._text(dependency.find(self._ns(namespace, "version")))
            if not group or not artifact:
                continue
            metadata: Dict[str, object] = {
                "scope": self._text(dependency.find(self._ns(namespace, "scope"))) or scope,
            }
            classifier = self._text(dependency.find(self._ns(namespace, "classifier")))
            if classifier:
                metadata["classifier"] = classifier
            optional = self._text(dependency.find(self._ns(namespace, "optional")))
            if optional:
                metadata["optional"] = optional.lower() == "true"
            repositories = parent.find(self._ns(namespace, "repositories"))
            if repositories is not None:
                metadata["repositories"] = [
                    self._text(repo.find(self._ns(namespace, "url")))
                    for repo in repositories.findall(self._ns(namespace, "repository"))
                ]
            dependencies.append((f"{group}:{artifact}", version, metadata))
        return dependencies

    def _detect_namespace(self, element: ET.Element) -> Optional[str]:
        if element.tag.startswith("{"):
            return element.tag.split("}")[0][1:]
        return None

    def _ns(self, namespace: Optional[str], tag: str) -> str:
        return f"{{{namespace}}}{tag}" if namespace else tag

    def _text(self, element: Optional[ET.Element]) -> Optional[str]:
        if element is None:
            return None
        text = element.text or ""
        return text.strip() or None
