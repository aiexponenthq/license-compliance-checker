"""
Comprehensive tests for transitive dependency depth tracking across all 8 detectors.

Each detector now populates these metadata keys on every Component:
  - dependency_depth: int  (0 = direct, 1+ = transitive)
  - is_direct: bool
  - parent_packages: list[str]
  - dependency_source: "manifest" | "lockfile" | "both"
"""

from __future__ import annotations

import json
import textwrap
from pathlib import Path

import pytest

from lcc.detection.python import PythonDetector
from lcc.detection.javascript import JavaScriptDetector
from lcc.detection.go import GoDetector
from lcc.detection.rust import CargoDetector
from lcc.detection.ruby import RubyDetector
from lcc.detection.gradle import GradleDetector
from lcc.detection.java import MavenDetector
from lcc.detection.dotnet import DotNetDetector


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write(path: Path, content: str) -> None:
    """Write content to a file, creating parent dirs as needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content), encoding="utf-8")


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _by_name(components) -> dict:
    """Index components by name for easy lookup."""
    return {c.name: c for c in components}


def _assert_depth_metadata(component, *, is_direct: bool, depth: int, dep_source: str | None = None):
    """Assert the four depth-tracking metadata keys on a component."""
    meta = component.metadata
    assert "is_direct" in meta, f"{component.name}: missing 'is_direct'"
    assert "dependency_depth" in meta, f"{component.name}: missing 'dependency_depth'"
    assert "parent_packages" in meta, f"{component.name}: missing 'parent_packages'"
    assert "dependency_source" in meta, f"{component.name}: missing 'dependency_source'"

    assert meta["is_direct"] is is_direct, (
        f"{component.name}: expected is_direct={is_direct}, got {meta['is_direct']}"
    )
    assert meta["dependency_depth"] == depth, (
        f"{component.name}: expected depth={depth}, got {meta['dependency_depth']}"
    )
    assert isinstance(meta["parent_packages"], list), (
        f"{component.name}: parent_packages should be a list"
    )
    if dep_source is not None:
        assert meta["dependency_source"] == dep_source, (
            f"{component.name}: expected dependency_source={dep_source!r}, got {meta['dependency_source']!r}"
        )


# ===========================================================================
# Python Detector
# ===========================================================================

class TestPythonDepthTracking:
    """Depth tracking tests for PythonDetector."""

    def test_requirements_txt_all_direct(self, tmp_path: Path):
        """Packages from requirements.txt should be is_direct=True, depth=0."""
        _write(tmp_path / "requirements.txt", """\
            requests==2.31.0
            flask==3.0.0
            click==8.1.7
        """)

        detector = PythonDetector()
        components = detector.discover(tmp_path)
        by = _by_name(components)

        for name in ("requests", "flask", "click"):
            assert name in by, f"Expected {name} in components"
            _assert_depth_metadata(by[name], is_direct=True, depth=0, dep_source="manifest")

    def test_pyproject_poetry_direct_vs_transitive(self, tmp_path: Path):
        """Packages declared in pyproject.toml should be direct;
        packages only in poetry.lock should be transitive.

        Note: pyproject.toml uses version specifiers (e.g. ^2.31.0) while
        poetry.lock has exact versions (e.g. 2.31.0). These create separate
        component entries. The lock-versioned entry sources are "lockfile"
        because only poetry.lock contributes an exact version. The manifest
        entry (if any) has the specifier. Both share is_direct/depth since
        they share the same canonical name.
        """
        _write(tmp_path / "pyproject.toml", """\
            [tool.poetry.dependencies]
            python = "^3.11"
            requests = "^2.31.0"
            flask = "^3.0.0"
        """)

        _write(tmp_path / "poetry.lock", """\
            [[package]]
            name = "requests"
            version = "2.31.0"

            [package.dependencies]
            urllib3 = ">=1.21.5"
            certifi = ">=2017.4.17"
            charset-normalizer = ">=2,<4"
            idna = ">=2.5,<4"

            [[package]]
            name = "flask"
            version = "3.0.0"

            [package.dependencies]
            werkzeug = ">=3.0.0"
            jinja2 = ">=3.1.2"

            [[package]]
            name = "urllib3"
            version = "2.1.0"

            [[package]]
            name = "certifi"
            version = "2024.2.2"

            [[package]]
            name = "charset-normalizer"
            version = "3.3.2"

            [[package]]
            name = "idna"
            version = "3.6"

            [[package]]
            name = "werkzeug"
            version = "3.0.1"

            [[package]]
            name = "jinja2"
            version = "3.1.3"

            [package.dependencies]
            markupsafe = ">=2.0"

            [[package]]
            name = "markupsafe"
            version = "2.1.5"
        """)

        detector = PythonDetector()
        components = detector.discover(tmp_path)
        by = _by_name(components)

        # Direct deps from pyproject.toml — look at lock-versioned entries
        # is_direct and depth are keyed by canonical name, not version
        requests_components = [c for c in components if c.name == "requests"]
        for rc in requests_components:
            assert rc.metadata["is_direct"] is True
            assert rc.metadata["dependency_depth"] == 0

        flask_components = [c for c in components if c.name == "flask"]
        for fc in flask_components:
            assert fc.metadata["is_direct"] is True
            assert fc.metadata["dependency_depth"] == 0

        # Transitive deps only in poetry.lock
        for name in ("urllib3", "certifi", "charset-normalizer", "idna"):
            assert name in by, f"Expected transitive dep {name}"
            _assert_depth_metadata(by[name], is_direct=False, depth=1, dep_source="lockfile")

        for name in ("werkzeug", "jinja2"):
            assert name in by, f"Expected transitive dep {name}"
            _assert_depth_metadata(by[name], is_direct=False, depth=1, dep_source="lockfile")

        # markupsafe is a dependency of jinja2, which is transitive itself -> depth 2
        assert "markupsafe" in by
        _assert_depth_metadata(by["markupsafe"], is_direct=False, depth=2, dep_source="lockfile")

    def test_parent_packages_populated(self, tmp_path: Path):
        """Transitive deps should list their parent packages."""
        _write(tmp_path / "pyproject.toml", """\
            [tool.poetry.dependencies]
            python = "^3.11"
            requests = "^2.31.0"
        """)

        _write(tmp_path / "poetry.lock", """\
            [[package]]
            name = "requests"
            version = "2.31.0"

            [package.dependencies]
            urllib3 = ">=1.21.5"

            [[package]]
            name = "urllib3"
            version = "2.1.0"
        """)

        detector = PythonDetector()
        components = detector.discover(tmp_path)
        by = _by_name(components)

        assert by["urllib3"].metadata["parent_packages"] == ["requests"]
        assert by["requests"].metadata["parent_packages"] == []

    def test_pyproject_project_dependencies_direct(self, tmp_path: Path):
        """PEP 621 [project] dependencies should be marked direct."""
        _write(tmp_path / "pyproject.toml", """\
            [project]
            dependencies = [
                "click>=8.0",
                "rich>=13.0",
            ]
        """)

        detector = PythonDetector()
        components = detector.discover(tmp_path)
        by = _by_name(components)

        for name in ("click", "rich"):
            assert name in by
            _assert_depth_metadata(by[name], is_direct=True, depth=0, dep_source="manifest")


# ===========================================================================
# JavaScript Detector
# ===========================================================================

class TestJavaScriptDepthTracking:
    """Depth tracking tests for JavaScriptDetector."""

    def test_package_json_all_direct(self, tmp_path: Path):
        """Dependencies listed in package.json should be is_direct=True, depth=0."""
        _write_json(tmp_path / "package.json", {
            "name": "test-app",
            "version": "1.0.0",
            "dependencies": {
                "express": "^4.18.0",
                "lodash": "^4.17.21",
            },
            "devDependencies": {
                "jest": "^29.0.0",
            },
        })

        detector = JavaScriptDetector()
        components = detector.discover(tmp_path)
        by = _by_name(components)

        for name in ("express", "lodash", "jest"):
            assert name in by, f"Expected {name} in components"
            _assert_depth_metadata(by[name], is_direct=True, depth=0, dep_source="manifest")

    def test_package_lock_v3_direct_vs_transitive(self, tmp_path: Path):
        """package-lock.json v3 should distinguish direct from transitive deps.

        Note: package.json lists express with specifier (no exact version) while
        package-lock.json has the resolved version. These may create separate
        component entries. We verify is_direct and depth on all express entries.
        """
        _write_json(tmp_path / "package.json", {
            "name": "test-app",
            "version": "1.0.0",
            "dependencies": {
                "express": "^4.18.0",
            },
        })

        _write_json(tmp_path / "package-lock.json", {
            "name": "test-app",
            "version": "1.0.0",
            "lockfileVersion": 3,
            "packages": {
                "": {
                    "name": "test-app",
                    "version": "1.0.0",
                    "dependencies": {
                        "express": "^4.18.0",
                    },
                },
                "node_modules/express": {
                    "version": "4.18.2",
                    "license": "MIT",
                    "dependencies": {
                        "body-parser": "1.20.2",
                        "cookie": "0.5.0",
                    },
                },
                "node_modules/body-parser": {
                    "version": "1.20.2",
                    "license": "MIT",
                    "dependencies": {
                        "raw-body": "2.5.2",
                    },
                },
                "node_modules/cookie": {
                    "version": "0.5.0",
                    "license": "MIT",
                },
                "node_modules/raw-body": {
                    "version": "2.5.2",
                    "license": "MIT",
                },
            },
        })

        detector = JavaScriptDetector()
        components = detector.discover(tmp_path)
        by = _by_name(components)

        # express is direct — verify all entries with name "express"
        express_components = [c for c in components if c.name == "express"]
        for ec in express_components:
            assert ec.metadata["is_direct"] is True
            assert ec.metadata["dependency_depth"] == 0

        # body-parser and cookie are transitive (depth 1, parent=express)
        _assert_depth_metadata(by["body-parser"], is_direct=False, depth=1, dep_source="lockfile")
        assert "express" in by["body-parser"].metadata["parent_packages"]

        _assert_depth_metadata(by["cookie"], is_direct=False, depth=1, dep_source="lockfile")
        assert "express" in by["cookie"].metadata["parent_packages"]

        # raw-body is depth 2 (transitive of body-parser which is transitive of express)
        _assert_depth_metadata(by["raw-body"], is_direct=False, depth=2, dep_source="lockfile")
        assert "body-parser" in by["raw-body"].metadata["parent_packages"]

    def test_parent_packages_from_dependency_graph(self, tmp_path: Path):
        """parent_packages should list immediate parents from the dep graph."""
        _write_json(tmp_path / "package.json", {
            "name": "test-app",
            "version": "1.0.0",
            "dependencies": {"a": "^1.0.0", "b": "^1.0.0"},
        })

        _write_json(tmp_path / "package-lock.json", {
            "lockfileVersion": 3,
            "packages": {
                "": {
                    "name": "test-app",
                    "version": "1.0.0",
                    "dependencies": {"a": "^1.0.0", "b": "^1.0.0"},
                },
                "node_modules/a": {
                    "version": "1.0.0",
                    "dependencies": {"shared": "1.0.0"},
                },
                "node_modules/b": {
                    "version": "1.0.0",
                    "dependencies": {"shared": "1.0.0"},
                },
                "node_modules/shared": {
                    "version": "1.0.0",
                },
            },
        })

        detector = JavaScriptDetector()
        components = detector.discover(tmp_path)
        by = _by_name(components)

        # "shared" is reached from both "a" and "b"
        shared_parents = by["shared"].metadata["parent_packages"]
        assert "a" in shared_parents
        assert "b" in shared_parents


# ===========================================================================
# Go Detector
# ===========================================================================

class TestGoDepthTracking:
    """Depth tracking tests for GoDetector."""

    def test_direct_requires(self, tmp_path: Path):
        """Modules without // indirect comment should be is_direct=True, depth=0."""
        _write(tmp_path / "go.mod", """\
            module example.com/myapp

            go 1.21

            require (
                github.com/gin-gonic/gin v1.9.1
                github.com/stretchr/testify v1.8.4
            )
        """)

        detector = GoDetector()
        components = detector.discover(tmp_path)
        by = _by_name(components)

        for name in ("github.com/gin-gonic/gin", "github.com/stretchr/testify"):
            assert name in by
            _assert_depth_metadata(by[name], is_direct=True, depth=0, dep_source="manifest")
            assert by[name].metadata["parent_packages"] == []

    def test_indirect_requires(self, tmp_path: Path):
        """Modules with // indirect comment should be is_direct=False, depth=1."""
        _write(tmp_path / "go.mod", """\
            module example.com/myapp

            go 1.21

            require (
                github.com/gin-gonic/gin v1.9.1
                github.com/mattn/go-isatty v0.0.19 // indirect
                golang.org/x/sys v0.13.0 // indirect
            )
        """)

        detector = GoDetector()
        components = detector.discover(tmp_path)
        by = _by_name(components)

        _assert_depth_metadata(
            by["github.com/gin-gonic/gin"], is_direct=True, depth=0, dep_source="manifest",
        )
        _assert_depth_metadata(
            by["github.com/mattn/go-isatty"], is_direct=False, depth=1, dep_source="manifest",
        )
        _assert_depth_metadata(
            by["golang.org/x/sys"], is_direct=False, depth=1, dep_source="manifest",
        )

    def test_mixed_direct_and_indirect(self, tmp_path: Path):
        """Mixed require block with both direct and indirect modules."""
        _write(tmp_path / "go.mod", """\
            module example.com/myapp

            go 1.21

            require github.com/pkg/errors v0.9.1

            require (
                github.com/sirupsen/logrus v1.9.3
                golang.org/x/text v0.14.0 // indirect
            )
        """)

        detector = GoDetector()
        components = detector.discover(tmp_path)
        by = _by_name(components)

        _assert_depth_metadata(by["github.com/pkg/errors"], is_direct=True, depth=0)
        _assert_depth_metadata(by["github.com/sirupsen/logrus"], is_direct=True, depth=0)
        _assert_depth_metadata(by["golang.org/x/text"], is_direct=False, depth=1)


# ===========================================================================
# Rust / Cargo Detector
# ===========================================================================

class TestRustDepthTracking:
    """Depth tracking tests for CargoDetector."""

    def test_cargo_toml_direct(self, tmp_path: Path):
        """Packages in Cargo.toml [dependencies] should be is_direct=True."""
        _write(tmp_path / "Cargo.toml", """\
            [package]
            name = "my-crate"
            version = "0.1.0"
            edition = "2021"

            [dependencies]
            serde = "1.0"
            tokio = { version = "1.35", features = ["full"] }

            [dev-dependencies]
            criterion = "0.5"
        """)

        detector = CargoDetector()
        components = detector.discover(tmp_path)
        by = _by_name(components)

        for name in ("serde", "tokio", "criterion"):
            assert name in by, f"Expected {name} in components"
            _assert_depth_metadata(by[name], is_direct=True, depth=0, dep_source="manifest")

    def test_cargo_lock_transitive(self, tmp_path: Path):
        """Packages in Cargo.lock but not in Cargo.toml should be transitive.

        Note: Cargo.toml uses version specifiers (e.g. "1.0") and Cargo.lock
        has exact versions (e.g. "1.0.195"), creating separate component entries.
        Both entries for 'serde' should be marked direct, just with different
        dependency_source values.
        """
        _write(tmp_path / "Cargo.toml", """\
            [package]
            name = "my-crate"
            version = "0.1.0"
            edition = "2021"

            [dependencies]
            serde = "1.0"
        """)

        _write(tmp_path / "Cargo.lock", """\
            [[package]]
            name = "serde"
            version = "1.0.195"
            dependencies = [
                "serde_derive 1.0.195",
            ]

            [[package]]
            name = "serde_derive"
            version = "1.0.195"
            dependencies = [
                "proc-macro2 1.0.78",
                "quote 1.0.35",
                "syn 2.0.48",
            ]

            [[package]]
            name = "proc-macro2"
            version = "1.0.78"

            [[package]]
            name = "quote"
            version = "1.0.35"

            [[package]]
            name = "syn"
            version = "2.0.48"
        """)

        detector = CargoDetector()
        components = detector.discover(tmp_path)
        by = _by_name(components)

        # serde appears in both manifest and lock (with different versions)
        # All entries should be is_direct=True, depth=0
        serde_components = [c for c in components if c.name == "serde"]
        for sc in serde_components:
            assert sc.metadata["is_direct"] is True
            assert sc.metadata["dependency_depth"] == 0

        _assert_depth_metadata(by["serde_derive"], is_direct=False, depth=1, dep_source="lockfile")
        assert "serde" in by["serde_derive"].metadata["parent_packages"]

        # proc-macro2, quote, syn are depth 2 (children of serde_derive)
        for name in ("proc-macro2", "quote", "syn"):
            assert name in by, f"Expected {name} in components"
            _assert_depth_metadata(by[name], is_direct=False, depth=2, dep_source="lockfile")
            assert "serde_derive" in by[name].metadata["parent_packages"]

    def test_cargo_lock_shared_parent(self, tmp_path: Path):
        """A transitive dep reachable from multiple parents should list all."""
        _write(tmp_path / "Cargo.toml", """\
            [package]
            name = "my-crate"
            version = "0.1.0"

            [dependencies]
            alpha = "1.0"
            beta = "1.0"
        """)

        _write(tmp_path / "Cargo.lock", """\
            [[package]]
            name = "alpha"
            version = "1.0.0"
            dependencies = [
                "shared 1.0.0",
            ]

            [[package]]
            name = "beta"
            version = "1.0.0"
            dependencies = [
                "shared 1.0.0",
            ]

            [[package]]
            name = "shared"
            version = "1.0.0"
        """)

        detector = CargoDetector()
        components = detector.discover(tmp_path)
        by = _by_name(components)

        parents = by["shared"].metadata["parent_packages"]
        assert "alpha" in parents
        assert "beta" in parents


# ===========================================================================
# Ruby Detector
# ===========================================================================

class TestRubyDepthTracking:
    """Depth tracking tests for RubyDetector."""

    def test_gemfile_all_direct(self, tmp_path: Path):
        """Gems declared in Gemfile should be is_direct=True."""
        _write(tmp_path / "Gemfile", """\
            source 'https://rubygems.org'

            gem 'rails', '7.0.4'
            gem 'pg'
            gem 'puma', '~> 5.0'
        """)

        detector = RubyDetector()
        components = detector.discover(tmp_path)
        by = _by_name(components)

        for name in ("rails", "pg", "puma"):
            assert name in by, f"Expected {name}"
            _assert_depth_metadata(by[name], is_direct=True, depth=0, dep_source="manifest")

    def test_gemfile_lock_direct_vs_transitive(self, tmp_path: Path):
        """Gems in Gemfile should be direct; gems only in Gemfile.lock transitive."""
        _write(tmp_path / "Gemfile", """\
            source 'https://rubygems.org'

            gem 'rails', '7.0.4'
        """)

        _write(tmp_path / "Gemfile.lock", """\
            GEM
              remote: https://rubygems.org/
              specs:
                rails (7.0.4)
                  actioncable (= 7.0.4)
                  actionpack (= 7.0.4)
                actioncable (7.0.4)
                  activesupport (= 7.0.4)
                actionpack (7.0.4)
                  activesupport (= 7.0.4)
                activesupport (7.0.4)
                  concurrent-ruby (~> 1.0)
                concurrent-ruby (1.2.3)

            PLATFORMS
              ruby

            DEPENDENCIES
              rails (= 7.0.4)
        """)

        detector = RubyDetector()
        components = detector.discover(tmp_path)
        by = _by_name(components)

        # rails is direct and in both manifest + lock
        _assert_depth_metadata(by["rails"], is_direct=True, depth=0, dep_source="both")

        # actioncable, actionpack are transitive (depth 1, parent=rails)
        _assert_depth_metadata(by["actioncable"], is_direct=False, depth=1, dep_source="lockfile")
        assert "rails" in by["actioncable"].metadata["parent_packages"]

        _assert_depth_metadata(by["actionpack"], is_direct=False, depth=1, dep_source="lockfile")
        assert "rails" in by["actionpack"].metadata["parent_packages"]

        # activesupport is depth 2 (child of actioncable or actionpack)
        _assert_depth_metadata(by["activesupport"], is_direct=False, depth=2, dep_source="lockfile")
        activesupport_parents = by["activesupport"].metadata["parent_packages"]
        assert "actioncable" in activesupport_parents or "actionpack" in activesupport_parents

        # concurrent-ruby is depth 3 (child of activesupport)
        _assert_depth_metadata(by["concurrent-ruby"], is_direct=False, depth=3, dep_source="lockfile")
        assert "activesupport" in by["concurrent-ruby"].metadata["parent_packages"]

    def test_gemfile_lock_parent_packages(self, tmp_path: Path):
        """parent_packages should list immediate parents."""
        _write(tmp_path / "Gemfile", """\
            source 'https://rubygems.org'

            gem 'rack'
        """)

        _write(tmp_path / "Gemfile.lock", """\
            GEM
              remote: https://rubygems.org/
              specs:
                rack (3.0.8)
                  rack-test (2.1.0)
                rack-test (2.1.0)
                  rack (>= 1.3)

            PLATFORMS
              ruby

            DEPENDENCIES
              rack
        """)

        detector = RubyDetector()
        components = detector.discover(tmp_path)
        by = _by_name(components)

        assert by["rack"].metadata["parent_packages"] == [] or "rack-test" in by["rack"].metadata["parent_packages"]
        assert "rack" in by["rack-test"].metadata["parent_packages"]


# ===========================================================================
# Gradle Detector
# ===========================================================================

class TestGradleDepthTracking:
    """Depth tracking tests for GradleDetector."""

    def test_build_gradle_all_direct(self, tmp_path: Path):
        """Deps in build.gradle should be is_direct=True, depth=0."""
        _write(tmp_path / "build.gradle", """\
            plugins {
                id 'java'
            }

            dependencies {
                implementation 'com.google.guava:guava:32.1.3-jre'
                testImplementation 'junit:junit:4.13.2'
                api 'org.slf4j:slf4j-api:2.0.9'
            }
        """)

        detector = GradleDetector()
        components = detector.discover(tmp_path)
        by = _by_name(components)

        for name in ("com.google.guava:guava", "junit:junit", "org.slf4j:slf4j-api"):
            assert name in by, f"Expected {name}"
            _assert_depth_metadata(by[name], is_direct=True, depth=0, dep_source="manifest")

    def test_gradle_lockfile_only_transitive(self, tmp_path: Path):
        """Deps only in gradle.lockfile (not in build.gradle) should be transitive."""
        _write(tmp_path / "build.gradle", """\
            dependencies {
                implementation 'com.google.guava:guava:32.1.3-jre'
            }
        """)

        _write(tmp_path / "gradle.lockfile", """\
            # This is a Gradle generated file for dependency locking.
            com.google.guava:guava:32.1.3-jre=compileClasspath
            com.google.guava:failureaccess:1.0.2=compileClasspath
            com.google.guava:listenablefuture:9999.0-empty-to-avoid-conflict-with-guava=compileClasspath
        """)

        detector = GradleDetector()
        components = detector.discover(tmp_path)
        by = _by_name(components)

        _assert_depth_metadata(
            by["com.google.guava:guava"], is_direct=True, depth=0, dep_source="both",
        )

        _assert_depth_metadata(
            by["com.google.guava:failureaccess"], is_direct=False, depth=1, dep_source="lockfile",
        )
        _assert_depth_metadata(
            by["com.google.guava:listenablefuture"], is_direct=False, depth=1, dep_source="lockfile",
        )

    def test_gradle_lockfile_direct_marked_both(self, tmp_path: Path):
        """A dep in both build.gradle and gradle.lockfile should have dep_source=both."""
        _write(tmp_path / "build.gradle", """\
            dependencies {
                implementation 'org.apache.commons:commons-lang3:3.14.0'
            }
        """)

        _write(tmp_path / "gradle.lockfile", """\
            org.apache.commons:commons-lang3:3.14.0=compileClasspath
        """)

        detector = GradleDetector()
        components = detector.discover(tmp_path)
        by = _by_name(components)

        _assert_depth_metadata(
            by["org.apache.commons:commons-lang3"], is_direct=True, depth=0, dep_source="both",
        )


# ===========================================================================
# Java / Maven Detector
# ===========================================================================

class TestJavaDepthTracking:
    """Depth tracking tests for MavenDetector."""

    def test_pom_xml_all_direct(self, tmp_path: Path):
        """All deps in pom.xml should be is_direct=True, depth=0 (no lock file)."""
        _write(tmp_path / "pom.xml", """\
            <?xml version="1.0" encoding="UTF-8"?>
            <project xmlns="http://maven.apache.org/POM/4.0.0"
                     xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                     xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
                <modelVersion>4.0.0</modelVersion>
                <groupId>com.example</groupId>
                <artifactId>my-app</artifactId>
                <version>1.0.0</version>

                <dependencies>
                    <dependency>
                        <groupId>com.google.guava</groupId>
                        <artifactId>guava</artifactId>
                        <version>32.1.3-jre</version>
                    </dependency>
                    <dependency>
                        <groupId>org.slf4j</groupId>
                        <artifactId>slf4j-api</artifactId>
                        <version>2.0.9</version>
                    </dependency>
                    <dependency>
                        <groupId>junit</groupId>
                        <artifactId>junit</artifactId>
                        <version>4.13.2</version>
                        <scope>test</scope>
                    </dependency>
                </dependencies>
            </project>
        """)

        detector = MavenDetector()
        components = detector.discover(tmp_path)
        by = _by_name(components)

        for name in ("com.google.guava:guava", "org.slf4j:slf4j-api", "junit:junit"):
            assert name in by, f"Expected {name}"
            _assert_depth_metadata(by[name], is_direct=True, depth=0, dep_source="manifest")
            assert by[name].metadata["parent_packages"] == []

    def test_pom_xml_with_dependency_management(self, tmp_path: Path):
        """Managed deps should also be direct."""
        _write(tmp_path / "pom.xml", """\
            <?xml version="1.0" encoding="UTF-8"?>
            <project>
                <groupId>com.example</groupId>
                <artifactId>parent-app</artifactId>
                <version>1.0.0</version>

                <dependencyManagement>
                    <dependencies>
                        <dependency>
                            <groupId>org.springframework</groupId>
                            <artifactId>spring-core</artifactId>
                            <version>6.1.3</version>
                        </dependency>
                    </dependencies>
                </dependencyManagement>

                <dependencies>
                    <dependency>
                        <groupId>org.apache.commons</groupId>
                        <artifactId>commons-lang3</artifactId>
                        <version>3.14.0</version>
                    </dependency>
                </dependencies>
            </project>
        """)

        detector = MavenDetector()
        components = detector.discover(tmp_path)
        by = _by_name(components)

        _assert_depth_metadata(
            by["org.springframework:spring-core"], is_direct=True, depth=0, dep_source="manifest",
        )
        _assert_depth_metadata(
            by["org.apache.commons:commons-lang3"], is_direct=True, depth=0, dep_source="manifest",
        )


# ===========================================================================
# .NET Detector
# ===========================================================================

class TestDotNetDepthTracking:
    """Depth tracking tests for DotNetDetector."""

    def test_csproj_all_direct(self, tmp_path: Path):
        """PackageReference in .csproj should be is_direct=True, depth=0."""
        _write(tmp_path / "MyApp.csproj", """\
            <Project Sdk="Microsoft.NET.Sdk">
                <PropertyGroup>
                    <TargetFramework>net8.0</TargetFramework>
                </PropertyGroup>
                <ItemGroup>
                    <PackageReference Include="Newtonsoft.Json" Version="13.0.3" />
                    <PackageReference Include="Serilog" Version="3.1.1" />
                    <PackageReference Include="xunit" Version="2.6.6" />
                </ItemGroup>
            </Project>
        """)

        detector = DotNetDetector()
        components = detector.discover(tmp_path)
        by = _by_name(components)

        for name in ("Newtonsoft.Json", "Serilog", "xunit"):
            assert name in by, f"Expected {name}"
            _assert_depth_metadata(by[name], is_direct=True, depth=0, dep_source="manifest")
            assert by[name].metadata["parent_packages"] == []

    def test_packages_config_all_direct(self, tmp_path: Path):
        """Legacy packages.config deps should be is_direct=True, depth=0."""
        _write(tmp_path / "packages.config", """\
            <?xml version="1.0" encoding="utf-8"?>
            <packages>
                <package id="Newtonsoft.Json" version="13.0.1" targetFramework="net472" />
                <package id="NUnit" version="3.14.0" targetFramework="net472" />
            </packages>
        """)

        detector = DotNetDetector()
        components = detector.discover(tmp_path)
        by = _by_name(components)

        for name in ("Newtonsoft.Json", "NUnit"):
            assert name in by, f"Expected {name}"
            _assert_depth_metadata(by[name], is_direct=True, depth=0, dep_source="manifest")

    def test_paket_dependencies_all_direct(self, tmp_path: Path):
        """Paket dependencies should be is_direct=True, depth=0."""
        _write(tmp_path / "paket.dependencies", """\
            source https://api.nuget.org/v3/index.json

            nuget FSharp.Core >= 4.7.2
            nuget Newtonsoft.Json ~> 13.0
            nuget Serilog 2.10.0
        """)

        detector = DotNetDetector()
        components = detector.discover(tmp_path)
        by = _by_name(components)

        for name in ("FSharp.Core", "Newtonsoft.Json", "Serilog"):
            assert name in by, f"Expected {name}"
            _assert_depth_metadata(by[name], is_direct=True, depth=0, dep_source="manifest")


# ===========================================================================
# Cross-cutting: all detectors set the 4 metadata keys
# ===========================================================================

class TestAllDetectorsSetMetadataKeys:
    """Verify every detector always sets the 4 depth-tracking metadata keys."""

    def test_python_always_sets_keys(self, tmp_path: Path):
        _write(tmp_path / "requirements.txt", "requests==2.31.0\n")
        for c in PythonDetector().discover(tmp_path):
            assert "is_direct" in c.metadata
            assert "dependency_depth" in c.metadata
            assert "parent_packages" in c.metadata
            assert "dependency_source" in c.metadata

    def test_javascript_always_sets_keys(self, tmp_path: Path):
        _write_json(tmp_path / "package.json", {
            "name": "x", "version": "1.0.0",
            "dependencies": {"lodash": "^4.17.21"},
        })
        for c in JavaScriptDetector().discover(tmp_path):
            assert "is_direct" in c.metadata
            assert "dependency_depth" in c.metadata
            assert "parent_packages" in c.metadata
            assert "dependency_source" in c.metadata

    def test_go_always_sets_keys(self, tmp_path: Path):
        _write(tmp_path / "go.mod", """\
            module example.com/x

            go 1.21

            require github.com/pkg/errors v0.9.1
        """)
        for c in GoDetector().discover(tmp_path):
            assert "is_direct" in c.metadata
            assert "dependency_depth" in c.metadata
            assert "parent_packages" in c.metadata
            assert "dependency_source" in c.metadata

    def test_rust_always_sets_keys(self, tmp_path: Path):
        _write(tmp_path / "Cargo.toml", """\
            [package]
            name = "x"
            version = "0.1.0"

            [dependencies]
            serde = "1.0"
        """)
        for c in CargoDetector().discover(tmp_path):
            assert "is_direct" in c.metadata
            assert "dependency_depth" in c.metadata
            assert "parent_packages" in c.metadata
            assert "dependency_source" in c.metadata

    def test_ruby_always_sets_keys(self, tmp_path: Path):
        _write(tmp_path / "Gemfile", """\
            source 'https://rubygems.org'
            gem 'rails'
        """)
        for c in RubyDetector().discover(tmp_path):
            assert "is_direct" in c.metadata
            assert "dependency_depth" in c.metadata
            assert "parent_packages" in c.metadata
            assert "dependency_source" in c.metadata

    def test_gradle_always_sets_keys(self, tmp_path: Path):
        _write(tmp_path / "build.gradle", """\
            dependencies {
                implementation 'com.google.guava:guava:32.1.3-jre'
            }
        """)
        for c in GradleDetector().discover(tmp_path):
            assert "is_direct" in c.metadata
            assert "dependency_depth" in c.metadata
            assert "parent_packages" in c.metadata
            assert "dependency_source" in c.metadata

    def test_maven_always_sets_keys(self, tmp_path: Path):
        _write(tmp_path / "pom.xml", """\
            <?xml version="1.0" encoding="UTF-8"?>
            <project>
                <groupId>com.example</groupId>
                <artifactId>x</artifactId>
                <version>1.0.0</version>
                <dependencies>
                    <dependency>
                        <groupId>junit</groupId>
                        <artifactId>junit</artifactId>
                        <version>4.13.2</version>
                    </dependency>
                </dependencies>
            </project>
        """)
        for c in MavenDetector().discover(tmp_path):
            assert "is_direct" in c.metadata
            assert "dependency_depth" in c.metadata
            assert "parent_packages" in c.metadata
            assert "dependency_source" in c.metadata

    def test_dotnet_always_sets_keys(self, tmp_path: Path):
        _write(tmp_path / "MyApp.csproj", """\
            <Project Sdk="Microsoft.NET.Sdk">
                <ItemGroup>
                    <PackageReference Include="Newtonsoft.Json" Version="13.0.3" />
                </ItemGroup>
            </Project>
        """)
        for c in DotNetDetector().discover(tmp_path):
            assert "is_direct" in c.metadata
            assert "dependency_depth" in c.metadata
            assert "parent_packages" in c.metadata
            assert "dependency_source" in c.metadata


# ===========================================================================
# Edge cases
# ===========================================================================

class TestDepthTrackingEdgeCases:
    """Edge cases for depth tracking across detectors."""

    def test_python_no_lockfile_all_direct(self, tmp_path: Path):
        """Without a lock file, all deps should be direct with depth 0."""
        _write(tmp_path / "requirements.txt", """\
            requests==2.31.0
            flask==3.0.0
        """)
        components = PythonDetector().discover(tmp_path)
        for c in components:
            assert c.metadata["is_direct"] is True
            assert c.metadata["dependency_depth"] == 0

    def test_javascript_no_lockfile_all_direct(self, tmp_path: Path):
        """Without a lock file, all deps should be direct with depth 0."""
        _write_json(tmp_path / "package.json", {
            "name": "x", "version": "1.0.0",
            "dependencies": {"lodash": "^4.17.21"},
        })
        components = JavaScriptDetector().discover(tmp_path)
        by = _by_name(components)
        assert by["lodash"].metadata["is_direct"] is True
        assert by["lodash"].metadata["dependency_depth"] == 0

    def test_rust_no_lockfile_all_direct(self, tmp_path: Path):
        """Without Cargo.lock, all Cargo.toml deps should be direct."""
        _write(tmp_path / "Cargo.toml", """\
            [package]
            name = "x"
            version = "0.1.0"

            [dependencies]
            serde = "1.0"
        """)
        components = CargoDetector().discover(tmp_path)
        by = _by_name(components)
        assert by["serde"].metadata["is_direct"] is True
        assert by["serde"].metadata["dependency_depth"] == 0

    def test_ruby_no_lockfile_all_direct(self, tmp_path: Path):
        """Without Gemfile.lock, Gemfile deps should be direct."""
        _write(tmp_path / "Gemfile", """\
            source 'https://rubygems.org'
            gem 'rails'
        """)
        components = RubyDetector().discover(tmp_path)
        by = _by_name(components)
        assert by["rails"].metadata["is_direct"] is True
        assert by["rails"].metadata["dependency_depth"] == 0

    def test_go_single_line_require_indirect(self, tmp_path: Path):
        """Single-line require with // indirect should be marked transitive."""
        _write(tmp_path / "go.mod", """\
            module example.com/x

            go 1.21

            require golang.org/x/sys v0.13.0 // indirect
        """)
        components = GoDetector().discover(tmp_path)
        by = _by_name(components)
        _assert_depth_metadata(by["golang.org/x/sys"], is_direct=False, depth=1)

    def test_python_poetry_group_deps_are_direct(self, tmp_path: Path):
        """Poetry group dependencies should be treated as direct."""
        _write(tmp_path / "pyproject.toml", """\
            [tool.poetry.dependencies]
            python = "^3.11"
            requests = "^2.31.0"

            [tool.poetry.group.dev.dependencies]
            pytest = "^7.0"

            [tool.poetry.group.docs.dependencies]
            mkdocs = "^1.5"
        """)

        _write(tmp_path / "poetry.lock", """\
            [[package]]
            name = "requests"
            version = "2.31.0"

            [[package]]
            name = "pytest"
            version = "7.4.4"

            [[package]]
            name = "mkdocs"
            version = "1.5.3"
        """)

        components = PythonDetector().discover(tmp_path)
        by = _by_name(components)

        _assert_depth_metadata(by["requests"], is_direct=True, depth=0)
        _assert_depth_metadata(by["pytest"], is_direct=True, depth=0)
        _assert_depth_metadata(by["mkdocs"], is_direct=True, depth=0)

    def test_gradle_no_lockfile_all_direct(self, tmp_path: Path):
        """Without gradle.lockfile, build.gradle deps should be direct."""
        _write(tmp_path / "build.gradle", """\
            dependencies {
                implementation 'org.apache.commons:commons-lang3:3.14.0'
            }
        """)
        components = GradleDetector().discover(tmp_path)
        by = _by_name(components)
        assert by["org.apache.commons:commons-lang3"].metadata["is_direct"] is True
        assert by["org.apache.commons:commons-lang3"].metadata["dependency_depth"] == 0
        assert by["org.apache.commons:commons-lang3"].metadata["dependency_source"] == "manifest"
