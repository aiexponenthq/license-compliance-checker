from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from lcc.cli.main import determine_targets


class DetermineTargetsTests(unittest.TestCase):
    def test_recursive_discovers_manifest_directories(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            base = Path(tmp_dir)
            (base / "project").mkdir()
            (base / "project" / "package.json").write_text("{}", encoding="utf-8")
            subdir = base / "project" / "sub"
            subdir.mkdir()
            (subdir / "requirements.txt").write_text("requests==2.0.0", encoding="utf-8")

            targets = determine_targets(base / "project", manifests=[], recursive=False, exclude_patterns=[])
            self.assertEqual(targets, [ (base / "project").resolve() ])

            recursive_targets = determine_targets(base / "project", manifests=[], recursive=True, exclude_patterns=[])
            self.assertIn((base / "project").resolve(), recursive_targets)
            self.assertIn(subdir.resolve(), recursive_targets)

    def test_manifest_argument_prioritises_parent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            manifest_path = Path(tmp_dir) / "proj" / "go.mod"
            manifest_path.parent.mkdir(parents=True)
            manifest_path.write_text("module example.com/app", encoding="utf-8")

            targets = determine_targets(Path(tmp_dir), manifests=[str(manifest_path)], recursive=False, exclude_patterns=[])
            self.assertEqual(targets, [manifest_path.parent.resolve()])


if __name__ == "__main__":
    unittest.main()
