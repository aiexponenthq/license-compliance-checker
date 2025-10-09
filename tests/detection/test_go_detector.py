from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from lcc.detection.go import GoDetector


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class GoDetectorTests(unittest.TestCase):
    def test_reads_manifests(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            _write(
                tmp_path / "go.mod",
                """
module example.com/app

go 1.21

require (
    github.com/pkg/errors v0.9.1 // indirect
    github.com/sirupsen/logrus v1.9.0
)

replace github.com/pkg/errors => github.com/pkg/errors v0.9.1
replace example.com/internal => ./internal
                """,
            )
            _write(
                tmp_path / "go.sum",
                """
github.com/pkg/errors v0.9.1 h1:abcdef
github.com/pkg/errors v0.9.1/go.mod h1:ghijkl
github.com/sirupsen/logrus v1.9.0 h1:mnopqr
                """,
            )
            _write(
                tmp_path / "vendor" / "modules.txt",
                """
# github.com/sirupsen/logrus v1.9.0
## explicit
                """,
            )
            _write(
                tmp_path / "go.work",
                """
go 1.21

use ./tools
                """,
            )
            _write(
                tmp_path / "tools" / "go.mod",
                """
module example.com/tools

go 1.21

require golang.org/x/sys v0.13.0
                """,
            )

            detector = GoDetector()
            components = detector.discover(tmp_path)
            by_name = {component.name: component for component in components}

            self.assertIn("github.com/pkg/errors", by_name)
            self.assertTrue(
                any(source.get("source") == "go.mod" for source in by_name["github.com/pkg/errors"].metadata["sources"])
            )
            self.assertTrue(
                any(source.get("source") == "go.sum" for source in by_name["github.com/pkg/errors"].metadata["sources"])
            )

            logrus = by_name["github.com/sirupsen/logrus"]
            self.assertTrue(any(source.get("vendor") for source in logrus.metadata["sources"]))

            golang_sys = by_name["golang.org/x/sys"]
            self.assertTrue(
                any(str(source.get("module_prefix")) == "tools" for source in golang_sys.metadata["sources"])
            )


if __name__ == "__main__":
    unittest.main()
