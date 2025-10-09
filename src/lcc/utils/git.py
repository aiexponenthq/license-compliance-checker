# Copyright 2025 Ajay Pundhir
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Git utilities for cloning and managing repositories.
"""
import logging
import re
import shutil
from pathlib import Path

from git import GitCommandError, Repo

logger = logging.getLogger(__name__)

class GitError(Exception):
    """Base exception for Git operations."""
    pass

def clone_github_repo(repo_url: str, target_dir: Path) -> None:
    """
    Clone a GitHub repository to the target directory using GitPython.

    Args:
        repo_url: GitHub repository URL (e.g., https://github.com/user/repo)
        target_dir: Path where the repository will be cloned

    Raises:
        ValueError: If URL is invalid
        GitError: If cloning fails
    """
    # Extract and validate GitHub URL
    github_pattern = r"^https?://(www\.)?github\.com/([\w-]+)/([\w.-]+)"
    match = re.match(github_pattern, repo_url)

    if not match:
        raise ValueError(f"Invalid GitHub URL format: {repo_url}. Expected: https://github.com/user/repo")

    # Extract owner and repo name, normalize to base URL
    owner = match.group(2)
    repo_name = match.group(3).replace('.git', '')
    normalized_url = f"https://github.com/{owner}/{repo_name}.git"

    try:
        # Clone with depth=1 for faster cloning (shallow clone)
        Repo.clone_from(normalized_url, target_dir, depth=1)
    except GitCommandError as e:
        raise GitError(f"Failed to clone repository: {e}") from e

def clone_repository(repo_url: str, ref: str | None = None, depth: int = 1) -> Path:
    """
    Clone a repository to a temporary directory.

    Args:
        repo_url: Repository URL
        ref: Optional branch/tag/commit to checkout
        depth: Clone depth

    Returns:
        Path to cloned repository
    """
    import tempfile
    target_dir = Path(tempfile.mkdtemp(prefix="lcc_repo_"))

    try:
        # If it's a GitHub URL, we can use the specific logic if needed,
        # but Repo.clone_from handles most git URLs.
        # The original clone_github_repo was specific, but clone_repository is generic.

        # If ref is provided, we might need to fetch specific ref.
        # For simplicity in this phase, we'll just clone default branch if ref is None.

        kwargs = {"depth": depth} if depth > 0 else {}
        if ref:
            kwargs["branch"] = ref

        Repo.clone_from(repo_url, target_dir, **kwargs)
        return target_dir
    except GitCommandError as e:
        cleanup_repository(target_dir)
        raise GitError(f"Failed to clone {repo_url}: {e}") from e
    except Exception as e:
        cleanup_repository(target_dir)
        raise GitError(f"Unexpected error cloning {repo_url}: {e}") from e

def cleanup_repository(path: Path) -> None:
    """
    Remove a cloned repository directory.
    """
    if path.exists():
        try:
            shutil.rmtree(path)
        except Exception as e:
            logger.warning(f"Failed to clean up repository at {path}: {e}")

def extract_project_name_from_url(repo_url: str) -> str:
    """Extract project name from GitHub URL."""
    match = re.search(r"github\.com/([\w-]+)/([\w.-]+)", repo_url)
    if match:
        repo_name = match.group(2)
        return repo_name.replace(".git", "")
    return "unknown-project"
