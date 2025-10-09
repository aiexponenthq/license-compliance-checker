#!/usr/bin/env python
"""Builds an OPA policy bundle from the policy directory."""

from __future__ import annotations

import argparse
import json
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POLICY_DIR = ROOT / "policy"
REGO_DIR = POLICY_DIR / "rego"
DATA_DIR = POLICY_DIR / "data"


def build_bundle(output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(output, "w:gz") as bundle:
        for rego_file in REGO_DIR.glob("*.rego"):
            bundle.add(rego_file, arcname=f"policies/{rego_file.name}")
        for data_file in DATA_DIR.glob("*.json"):
            bundle.add(data_file, arcname=f"data/{data_file.name}")
        manifest = {
            "revision": "v1",
            "roots": ["policies", "data"],
        }
        manifest_path = POLICY_DIR / "manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        try:
            bundle.add(manifest_path, arcname="manifest.json")
        finally:
            manifest_path.unlink(missing_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build OPA policy bundle")
    parser.add_argument("--output", default=str(ROOT / "dist" / "policy.bundle.tar.gz"))
    args = parser.parse_args()
    build_bundle(Path(args.output))
    print(f"Bundle written to {args.output}")


if __name__ == "__main__":
    main()
