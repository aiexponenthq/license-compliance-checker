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
from urllib.parse import urlparse

from git import GitCommandError, Repo

logger = logging.getLogger(__name__)

# git accepts local transports (file://, ext::, the git-remote-ext helper) and
# treats a leading dash as a command-line option. A clone URL that reaches
# Repo.clone_from unchecked is therefore an SSRF / command-injection vector.
_ALLOWED_CLONE_SCHEMES = {"http", "https"}


class GitError(Exception):
    """Base exception for Git operations."""
    pass


def validate_clone_url(repo_url: str, *, github_only: bool = False) -> str:
    """Validate a repository URL before it is handed to git.

    Args:
        repo_url: The URL to clone.
        github_only: When True, restrict the host to github.com.

    Returns:
        The stripped, validated URL.

    Raises:
        ValueError: If the URL uses a disallowed scheme or host, looks like a
            command-line option, or contains control characters.
    """
    if not isinstance(repo_url, str) or not repo_url.strip():
        raise ValueError("Repository URL must be a non-empty string")

    url = repo_url.strip()

    if url.startswith("-"):
        raise ValueError(f"Invalid repository URL: {repo_url!r} looks like an option")
    if any(char in url for char in "\r\n\t "):
        raise ValueError("Repository URL must not contain whitespace or control characters")

    parsed = urlparse(url)
    if parsed.scheme.lower() not in _ALLOWED_CLONE_SCHEMES:
        raise ValueError(
            f"Unsupported URL scheme {parsed.scheme!r}. Only http and https are allowed."
        )
    if not parsed.hostname:
        raise ValueError("Repository URL must include a host")
    if github_only and parsed.hostname.lower() not in ("github.com", "www.github.com"):
        raise ValueError("Only github.com repositories are allowed")

    return url

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

    repo_url = validate_clone_url(repo_url)
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
