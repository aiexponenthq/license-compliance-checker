from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from lcc.detection.javascript import JavaScriptDetector


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class JavaScriptDetectorTests(unittest.TestCase):
    def test_supports_multiple_manifests(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            _write_json(
                tmp_path / "package.json",
                {
                    "name": "root-app",
                    "version": "1.0.0",
                    "license": "MIT",
                    "workspaces": ["packages/*"],
                    "dependencies": {"react": "^18.2.0", "@scope/lib": "1.0.0"},
                    "devDependencies": {"typescript": "^5.0.0"},
                },
            )
            _write_json(
                tmp_path / "packages" / "shared" / "package.json",
                {"name": "@scope/shared", "version": "0.1.0", "dependencies": {"lodash": "^4.17.21"}},
            )
            _write_json(
                tmp_path / "package-lock.json",
                {
                    "packages": {
                        "": {"name": "root-app", "version": "1.0.0"},
                        "node_modules/react": {"version": "18.2.0", "license": "MIT"},
                        "node_modules/@scope/lib": {"version": "1.0.0"},
                    }
                },
            )
            _write_text(
                tmp_path / "yarn.lock",
                """
react@^18.2.0:
  version "18.2.0"
  resolved "https://registry.yarnpkg.com/react-18.2.0.tgz"
  integrity sha512-abc
""",
            )
            _write_text(
                tmp_path / "pnpm-lock.yaml",
                """
packages:
  /react/18.2.0:
    resolution: {integrity: sha512-xyz}
    license: MIT
  /@scope/lib/1.0.0:
    resolution: {integrity: sha512-def}
""",
            )
            node_modules = tmp_path / "node_modules" / "react"
            _write_json(
                node_modules / "package.json",
                {"name": "react", "version": "18.2.0", "license": "MIT", "bundledDependencies": ["scheduler"]},
            )

            detector = JavaScriptDetector()
            components = detector.discover(tmp_path)
            by_name = {component.name: component for component in components}

            self.assertIn("react", by_name)
            react_sources = [source["source"] for source in by_name["react"].metadata["sources"]]
            self.assertIn("package-lock.json", react_sources)
            self.assertTrue(any("yarn.lock" in source for source in react_sources))
            self.assertEqual(by_name["react"].metadata["licenses"], ["MIT"])

            self.assertIn("@scope/lib", by_name)
            self.assertTrue(
                any("pnpm-lock.yaml" in source["source"] for source in by_name["@scope/lib"].metadata["sources"])
            )

            self.assertIn("@scope/shared", by_name)
            self.assertTrue(
                by_name["@scope/shared"].metadata["sources"][0]["source"].endswith("packages/shared/package.json")
            )


if __name__ == "__main__":
    unittest.main()
