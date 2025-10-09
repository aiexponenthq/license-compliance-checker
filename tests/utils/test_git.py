import pytest
from unittest.mock import patch
from pathlib import Path
from lcc.utils.git import clone_github_repo, extract_project_name_from_url

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
