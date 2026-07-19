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


class LicenseDetectionTests(unittest.TestCase):
    """License identification from LICENSE file contents (resolver correctness)."""

    def _detect(self, text: str) -> str | None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            (root / "LICENSE").write_text(text, encoding="utf-8")
            resolver = FileSystemResolver(LCCConfig())
            component = Component(
                type=ComponentType.GENERIC,
                name="LICENSE",
                version="*",
                path=root / "LICENSE",
            )
            evidence = list(resolver.resolve(component))
            self.assertEqual(len(evidence), 1)
            return evidence[0].license_expression

    # --- the two reported bugs ---

    def test_lgpl_is_not_misread_as_gpl(self) -> None:
        # "gpl" must not match inside "lgpl"; the full name must win.
        self.assertEqual(
            self._detect("GNU LESSER GENERAL PUBLIC LICENSE\nVersion 3\n"), "LGPL"
        )

    def test_primary_license_wins_over_a_mentioned_one(self) -> None:
        # A file that is MIT but references Apache for bundled deps stays MIT.
        text = "MIT License\n\nPermission is hereby granted. Bundled deps use the Apache License 2.0."
        self.assertEqual(self._detect(text), "MIT")

    # --- word-boundary safety ---

    def test_mit_not_detected_inside_other_words(self) -> None:
        # "commit"/"limit" contain "mit" but are not the MIT license.
        self.assertIsNone_or_unknown(self._detect("Contribution guide: how to commit and stay within the limit."))

    def assertIsNone_or_unknown(self, value: str | None) -> None:
        self.assertIn(value, (None, "UNKNOWN", "unknown"))

    def test_gpl_word_boundary(self) -> None:
        # A bare "LGPL" mention must resolve to LGPL, never GPL.
        self.assertEqual(self._detect("This library is licensed under the LGPL.\n"), "LGPL")

    # --- full license matrix ---

    def test_common_licenses(self) -> None:
        cases = {
            "MIT License\n\nPermission is hereby granted": "MIT",
            "Apache License\nVersion 2.0, January 2004": "Apache-2.0",
            "GNU GENERAL PUBLIC LICENSE\nVersion 3": "GPL",
            "GNU AFFERO GENERAL PUBLIC LICENSE\nVersion 3": "AGPL",
            "BSD 3-Clause License\nCopyright": "BSD-3-Clause",
            "BSD 2-Clause License\nCopyright": "BSD-2-Clause",
            "Mozilla Public License Version 2.0": "MPL-2.0",
            "Eclipse Public License - v 2.0": "EPL-2.0",
            "ISC License\n\nPermission to use": "ISC",
        }
        for text, expected in cases.items():
            with self.subTest(expected=expected):
                self.assertEqual(self._detect(text), expected)

    # --- priority + fallback ---

    def test_spdx_identifier_beats_body_text(self) -> None:
        text = "SPDX-License-Identifier: BSD-2-Clause\n\nGNU GENERAL PUBLIC LICENSE"
        self.assertEqual(self._detect(text), "BSD-2-Clause")

    def test_no_license_text_is_unknown(self) -> None:
        self.assertIsNone_or_unknown(self._detect("Copyright 2025 Someone. All rights reserved.\n"))


if __name__ == "__main__":
    unittest.main()
