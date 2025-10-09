from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from lcc.utils.git import GitError, cleanup_repository, clone_repository


class GitUtilsTests(unittest.TestCase):
    def test_clone_local_repository(self) -> None:
        with tempfile.TemporaryDirectory() as repo_dir:
            repo_path = Path(repo_dir)
            subprocess.run(["git", "init"], cwd=repo_dir, check=True, stdout=subprocess.DEVNULL)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_dir, check=True)
            subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_dir, check=True)
            (repo_path / "README.md").write_text("example", encoding="utf-8")
            subprocess.run(["git", "add", "README.md"], cwd=repo_dir, check=True, stdout=subprocess.DEVNULL)
            subprocess.run(
                ["git", "commit", "-m", "init"],
                cwd=repo_dir,
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            clone_path = clone_repository(repo_dir)
            try:
                self.assertTrue((clone_path / "README.md").exists())
            finally:
                cleanup_repository(clone_path)

    def test_clone_invalid_repository(self) -> None:
        with self.assertRaises(GitError):
            clone_repository("/nonexistent/path/to/repo.git", depth=0)


if __name__ == "__main__":
    unittest.main()
