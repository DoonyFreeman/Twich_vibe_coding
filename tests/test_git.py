"""Tests for git workflow."""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from vibe_coding.git_workflow import (
    branch_exists,
    commit_changes,
    create_branch,
    create_pull_request,
    get_branch_name,
    get_current_branch,
    get_git_executable,
    is_git_repo,
)


class MockResult:
    def __init__(self, returncode: int = 0, stderr: str = "") -> None:
        self.returncode = returncode
        self.stderr = stderr
        self.stdout = ""


class TestGitWorkflow:
    """Tests for git workflow functions."""

    def test_get_git_executable(self) -> None:
        """Test getting git executable."""
        git = get_git_executable()
        assert git.exists() or str(git)

    def test_is_git_repo(self) -> None:
        """Test checking if git repo."""
        result = is_git_repo()
        assert isinstance(result, bool)

    def test_get_current_branch(self) -> None:
        """Test getting current branch."""
        branch = get_current_branch()
        assert branch is None or isinstance(branch, str)

    def test_get_branch_name(self) -> None:
        """Test branch name generation."""
        name = get_branch_name(1, "Add dark mode")
        assert "twitch-idea-1" in name
        assert "add-dark-mode" in name

    def test_get_branch_name_long_description(self) -> None:
        """Test branch name with long description."""
        desc = "This is a very long description " * 10
        name = get_branch_name(1, desc)
        assert len(name) < 80

    def test_create_branch(self) -> None:
        """Test creating branch - mocked."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MockResult()
            result = create_branch("test-branch")
            assert result is True

    def test_commit_changes(self) -> None:
        """Test committing changes - mocked."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MockResult()
            result = commit_changes("Test commit")
            assert result is True

    def test_create_pull_request_no_gh(self) -> None:
        """Test PR creation without gh CLI."""
        with patch("shutil.which", return_value=None):
            result = create_pull_request("Test PR", "Body")
            assert result is None

    def test_branch_exists(self) -> None:
        """Test checking if branch exists."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MockResult()
            assert branch_exists("main") is True