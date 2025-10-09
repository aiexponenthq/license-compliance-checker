from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from lcc.detection.rust import CargoDetector


CARGO_TOML = """
[package]
name = "demo"
version = "0.1.0"
edition = "2021"
license = "MIT"

[dependencies]
serde = { version = "1.0", features = ["derive"] }

[dev-dependencies]
tokio = "1.0"
"""

CARGO_LOCK = """
[[package]]
name = "serde"
version = "1.0.200"
source = "registry+https://github.com/rust-lang/crates.io-index"
checksum = "abc"

[[package]]
name = "tokio"
version = "1.36.0"
"""


class CargoDetectorTests(unittest.TestCase):
    def test_collects_crates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            (root / "Cargo.toml").write_text(CARGO_TOML, encoding="utf-8")
            (root / "Cargo.lock").write_text(CARGO_LOCK, encoding="utf-8")

            detector = CargoDetector()
            components = detector.discover(root)

            names = {component.name for component in components}
            self.assertIn("demo", names)
            self.assertIn("serde", names)
            self.assertIn("tokio", names)


if __name__ == "__main__":
    unittest.main()
