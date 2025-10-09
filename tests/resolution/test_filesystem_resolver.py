from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from lcc.config import LCCConfig
from lcc.models import Component, ComponentType
from lcc.resolution.filesystem import FileSystemResolver


class FileSystemResolverTests(unittest.TestCase):
    def test_detects_spdx_license(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            license_path = root / "LICENSE"
            license_path.write_text("SPDX-License-Identifier: Apache-2.0\n", encoding="utf-8")
            resolver = FileSystemResolver(LCCConfig())
            component = Component(type=ComponentType.GENERIC, name="root", version="1.0.0", path=root / "dummy")
            component.metadata["project_root"] = str(root)

            evidence = list(resolver.resolve(component))
            self.assertEqual(len(evidence), 1)
            self.assertEqual(evidence[0].license_expression, "Apache-2.0")

    def test_respects_gitignore(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            (root / ".gitignore").write_text("LICENSE-ignored\n", encoding="utf-8")
            (root / "LICENSE-ignored").write_text("SPDX-License-Identifier: MIT\n", encoding="utf-8")
            resolver = FileSystemResolver(LCCConfig())
            component = Component(type=ComponentType.GENERIC, name="root", version="1.0.0")
            component.metadata["project_root"] = str(root)
            evidence = list(resolver.resolve(component))
            self.assertEqual(len(evidence), 0)


if __name__ == "__main__":
    unittest.main()
