"""
Git helper utilities for scanning remote repositories.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional


class GitError(RuntimeError):
    """Raised when Git operations fail."""


def clone_repository(url: str, ref: Optional[str] = None, depth: int = 1) -> Path:
    """
    Clone a Git repository into a temporary directory and checkout the provided ref.
    """

    target_dir = Path(tempfile.mkdtemp(prefix="lcc-git-"))
    clone_cmd = ["git", "clone", url, str(target_dir)]
    if depth > 0:
        clone_cmd.insert(2, f"--depth={depth}")
    result = subprocess.run(clone_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        shutil.rmtree(target_dir, ignore_errors=True)
        raise GitError(result.stderr.strip() or "Failed to clone repository")
    if ref:
        checkout = subprocess.run(
            ["git", "checkout", ref],
            cwd=str(target_dir),
            capture_output=True,
            text=True,
        )
        if checkout.returncode != 0:
            shutil.rmtree(target_dir, ignore_errors=True)
            raise GitError(checkout.stderr.strip() or f"Failed to checkout {ref}")
        subprocess.run(["git", "submodule", "update", "--init", "--recursive"], cwd=str(target_dir))
    return target_dir


def cleanup_repository(path: Path) -> None:
    """Remove a cloned repository directory."""

    shutil.rmtree(path, ignore_errors=True)

