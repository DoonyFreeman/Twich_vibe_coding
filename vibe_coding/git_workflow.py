"""Git workflow utilities for Vibe Coding."""

import logging
import shutil
import subprocess
from pathlib import Path
from typing import Any

from vibe_coding.config import get_config

log = logging.getLogger(__name__)


def get_git_executable() -> Path:
    """Get git executable path.

    Returns:
        Path to git.
    """
    return Path(shutil.which("git") or "/usr/bin/git")


def is_git_repo() -> bool:
    """Check if current directory is a git repository.

    Returns:
        True if git repo.
    """
    git = get_git_executable()
    result = subprocess.run(
        [git, "rev-parse", "--git-dir"],
        capture_output=True,
    )
    return result.returncode == 0


def get_current_branch() -> str | None:
    """Get current git branch.

    Returns:
        Branch name or None.
    """
    git = get_git_executable()
    result = subprocess.run(
        [git, "branch", "--show-current"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def create_branch(branch_name: str) -> bool:
    """Create and checkout a new branch.

    Args:
        branch_name: Name of branch to create.

    Returns:
        True if successful.
    """
    git = get_git_executable()

    result = subprocess.run(
        [git, "checkout", "-b", branch_name],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        log.error(f"Failed to create branch {branch_name}: {result.stderr}")
        return False

    log.info(f"Created and checked out branch: {branch_name}")
    return True


def checkout_branch(branch_name: str) -> bool:
    """Checkout an existing branch.

    Args:
        branch_name: Name of branch.

    Returns:
        True if successful.
    """
    git = get_git_executable()

    result = subprocess.run(
        [git, "checkout", branch_name],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        log.error(f"Failed to checkout branch {branch_name}: {result.stderr}")
        return False

    log.info(f"Checked out branch: {branch_name}")
    return True


def branch_exists(branch_name: str) -> bool:
    """Check if branch exists.

    Args:
        branch_name: Branch name.

    Returns:
        True if exists.
    """
    git = get_git_executable()

    result = subprocess.run(
        [git, "rev-parse", "--verify", f"refs/heads/{branch_name}"],
        capture_output=True,
    )
    return result.returncode == 0


def get_branch_name(idea_id: int, description: str) -> str:
    """Generate branch name from idea.

    Args:
        idea_id: Idea ID.
        description: Idea description.

    Returns:
        Branch name.
    """
    config = get_config()
    prefix = config["agent"]["branch_prefix"]

    slug = description.lower()
    slug = slug.replace(" ", "-")
    slug = "".join(c for c in slug if c.isalnum() or c == "-")
    slug = slug[:50]

    return f"{prefix}{idea_id}-{slug}"


def commit_changes(message: str, files: list[str] | None = None) -> bool:
    """Commit changes.

    Args:
        message: Commit message.
        files: Files to commit (None for all).

    Returns:
        True if successful.
    """
    git = get_git_executable()

    if files:
        for f in files:
            result = subprocess.run(
                [git, "add", f],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                log.error(f"Failed to add {f}: {result.stderr}")
                return False
    else:
        subprocess.run([git, "add", "-A"], capture_output=True)

    result = subprocess.run(
        [git, "commit", "-m", message],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        log.error(f"Failed to commit: {result.stderr}")
        return False

    log.info(f"Committed: {message}")
    return True


def push_branch(branch_name: str) -> bool:
    """Push branch to remote.

    Args:
        branch_name: Branch name.

    Returns:
        True if successful.
    """
    git = get_git_executable()

    result = subprocess.run(
        [git, "push", "-u", "origin", branch_name],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        log.error(f"Failed to push: {result.stderr}")
        return False

    log.info(f"Pushed branch: {branch_name}")
    return True


def create_pull_request(
    title: str,
    body: str,
    base_branch: str | None = None,
) -> dict[str, Any] | None:
    """Create a pull request using gh CLI.

    Args:
        title: PR title.
        body: PR body.
        base_branch: Base branch (default from config).

    Returns:
        Dict with PR info or None.
    """
    if base_branch is None:
        config = get_config()
        base_branch = config["agent"]["base_branch"]

    gh = shutil.which("gh")
    if not gh:
        log.error("gh CLI not found")
        return None

    result = subprocess.run(
        [gh, "pr", "create", "--title", title, "--body", body, "--base", base_branch],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        log.error(f"Failed to create PR: {result.stderr}")
        return None

    pr_url = result.stdout.strip()
    log.info(f"Created PR: {pr_url}")

    return {"url": pr_url, "title": title, "body": body}


async def execute_git_workflow(idea_id: int, description: str, complexity: str) -> dict[str, Any]:
    """Execute full git workflow for an idea.

    Args:
        idea_id: Idea ID.
        description: Idea description.
        complexity: Complexity level.

    Returns:
        Result dict with success status and PR info.
    """
    config = get_config()
    branch_prefix = config["agent"]["branch_prefix"]
    base_branch = config["agent"]["base_branch"]

    branch_name = get_branch_name(idea_id, description)

    current = get_current_branch()
    if current and current != base_branch:
        checkout_branch(base_branch)

    if branch_exists(branch_name):
        checkout_branch(branch_name)
    else:
        create_branch(branch_name)

    return {
        "success": True,
        "branch": branch_name,
        "message": f"Created branch: {branch_name}",
    }