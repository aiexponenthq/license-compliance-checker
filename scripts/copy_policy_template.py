#!/usr/bin/env python
"""Copy a policy template into the user's policy directory."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from lcc.config import load_config
from lcc.policy.base import PolicyManager

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = ROOT / "policy" / "templates"


def list_templates() -> None:
    for template in TEMPLATE_DIR.glob("*.yaml"):
        print(template.stem)


def copy_template(template: str, dest: Path) -> Path:
    src = TEMPLATE_DIR / f"{template}.yaml"
    if not src.exists():
        raise FileNotFoundError(f"Template '{template}' not found in {TEMPLATE_DIR}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(src, dest)
    return dest


def main() -> None:
    parser = argparse.ArgumentParser(description="Copy policy templates")
    parser.add_argument("template", nargs="?", help="Template name (omit to list)")
    parser.add_argument("--output", help="Output file path")
    parser.add_argument("--config", help="Config file path")
    args = parser.parse_args()

    if not args.template:
        list_templates()
        return

    config = load_config(Path(args.config)) if args.config else load_config()
    manager = PolicyManager(config)
    target = manager.policy_dir / f"{args.template}.yaml"
    if args.output:
        target = Path(args.output)
    copied = copy_template(args.template, target)
    print(f"Template copied to {copied}")


if __name__ == "__main__":
    main()
