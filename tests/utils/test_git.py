import pytest
from unittest.mock import patch
from pathlib import Path
from lcc.utils.git import (
    clone_github_repo,
    clone_repository,
    extract_project_name_from_url,
    validate_clone_url,
)

def test_extract_project_name_from_url():
    assert extract_project_name_from_url("https://github.com/user/repo.git") == "repo"
    assert extract_project_name_from_url("https://github.com/user/repo") == "repo"
    assert extract_project_name_from_url("https://github.com/user/repo-name.git") == "repo-name"
    assert extract_project_name_from_url("invalid") == "unknown-project"

@patch("lcc.utils.git.Repo.clone_from")
def test_clone_github_repo_success(mock_clone):
    url = "https://github.com/user/repo.git"
    target = Path("/tmp/test")
    
    clone_github_repo(url, target)
    
    mock_clone.assert_called_once_with(url, target, depth=1)

@patch("lcc.utils.git.Repo.clone_from")
def test_clone_github_repo_invalid_url(mock_clone):
    url = "https://gitlab.com/user/repo.git"
    target = Path("/tmp/test")
    
    with pytest.raises(ValueError, match="Invalid GitHub URL"):
        clone_github_repo(url, target)
    
    mock_clone.assert_not_called()


@pytest.mark.parametrize(
    "url",
    [
        "https://github.com/user/repo",
        "https://github.com/user/repo.git",
        "http://github.com/user/repo",
        "https://gitlab.com/user/repo",
    ],
)
def test_validate_clone_url_accepts_http_urls(url):
    assert validate_clone_url(url) == url


@pytest.mark.parametrize(
    "url",
    [
        "file:///etc/passwd",
        "ext::sh -c id",
        "git://github.com/user/repo",
        "ssh://git@github.com/user/repo",
        "-oProxyCommand=id",
        "",
        "   ",
    ],
)
def test_validate_clone_url_rejects_dangerous_urls(url):
    with pytest.raises(ValueError):
        validate_clone_url(url)


def test_validate_clone_url_github_only():
    assert validate_clone_url("https://github.com/user/repo", github_only=True)
    with pytest.raises(ValueError, match="github.com"):
        validate_clone_url("https://gitlab.com/user/repo", github_only=True)


@patch("lcc.utils.git.Repo.clone_from")
def test_clone_repository_rejects_dangerous_url_before_clone(mock_clone):
    with pytest.raises(ValueError):
        clone_repository("ext::sh -c id")
    mock_clone.assert_not_called()
