"""Tests for CLI commands."""

import pytest
from pathlib import Path
from unittest.mock import patch, AsyncMock

from typer.testing import CliRunner

from vibe_coding.cli.main import app


runner = CliRunner()


@pytest.fixture
def mock_db_path(tmp_path: Path) -> Path:
    """Create temporary database path."""
    return tmp_path / "test.db"


@pytest.fixture
def mock_config() -> dict:
    """Mock configuration."""
    return {
        "vibe_coding": {"vote_threshold": 3, "bot_nick": "VibeTCoder"},
        "twitch": {"channel": "test_channel"},
        "database": {"path": "test.db"},
        "agent": {"task_queue_path": "task_queue.txt"},
    }


class TestIdeasCommand:
    """Tests for ideas command."""

    def test_ideas_help(self) -> None:
        """Test ideas command help."""
        result = runner.invoke(app, ["ideas", "--help"])
        assert result.exit_code == 0
        assert "List all ideas" in result.stdout

    def test_ideas_empty(self) -> None:
        """Test ideas with no ideas returns empty message."""
        with patch("vibe_coding.cli.main.IdeaRepository") as mock_repo:
            mock_instance = AsyncMock()
            mock_instance.create_tables = AsyncMock()
            mock_instance.get_all_ideas = AsyncMock(return_value=[])
            mock_instance.close = AsyncMock()
            mock_repo.return_value = mock_instance

            result = runner.invoke(app, ["ideas"])
            assert result.exit_code == 0


class TestApproveCommand:
    """Tests for approve command."""

    def test_approve_help(self) -> None:
        """Test approve command help."""
        result = runner.invoke(app, ["approve", "--help"])
        assert result.exit_code == 0
        assert "Approve an idea" in result.stdout


class TestRejectCommand:
    """Tests for reject command."""

    def test_reject_help(self) -> None:
        """Test reject command help."""
        result = runner.invoke(app, ["reject", "--help"])
        assert result.exit_code == 0
        assert "Reject an idea" in result.stdout


class TestPendingCommand:
    """Tests for pending command."""

    def test_pending_help(self) -> None:
        """Test pending command help."""
        result = runner.invoke(app, ["pending", "--help"])
        assert result.exit_code == 0
        assert "Show pending ideas" in result.stdout


class TestStatsCommand:
    """Tests for stats command."""

    def test_stats_help(self) -> None:
        """Test stats command help."""
        result = runner.invoke(app, ["stats", "--help"])
        assert result.exit_code == 0
        assert "statistics" in result.stdout.lower()


class TestMainHelp:
    """Tests for main app."""

    def test_main_help(self) -> None:
        """Test main help."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "Vibe Coding" in result.stdout
        assert "ideas" in result.stdout
        assert "approve" in result.stdout
        assert "reject" in result.stdout
        assert "pending" in result.stdout
        assert "stats" in result.stdout

    def test_unknown_command(self) -> None:
        """Test unknown command."""
        result = runner.invoke(app, ["unknown"])
        assert result.exit_code != 0