"""Tests for agent task queue."""

import pytest
from pathlib import Path

from vibe_coding.agent_queue import AgentTaskQueue


@pytest.fixture
def tmp_queue_path(tmp_path: Path) -> Path:
    """Create temporary queue file."""
    return tmp_path / "task_queue.txt"


class TestAgentTaskQueue:
    """Tests for AgentTaskQueue."""

    def test_init(self) -> None:
        """Test initialization."""
        queue = AgentTaskQueue()
        assert queue is not None

    def test_get_next_task_empty(self, tmp_queue_path: Path) -> None:
        """Test getting next task when queue is empty."""
        tmp_queue_path.touch()
        queue = AgentTaskQueue()
        result = queue.get_next_task()
        assert result is None

    def test_complete_task(self, tmp_path: Path) -> None:
        """Test completing task removes from queue."""
        queue_path = tmp_path / "task_queue.txt"
        queue_path.write_text("1|test idea|M|medium\n2|another|L|high\n")

        queue = AgentTaskQueue()
        queue._queue_path = queue_path
        result = queue.complete_task(1)

        assert result is True
        remaining = queue_path.read_text()
        assert "1|" not in remaining
        assert "2|" in remaining

    def test_get_next_task(self, tmp_path: Path) -> None:
        """Test getting next task from queue."""
        queue_path = tmp_path / "task_queue.txt"
        queue_path.write_text("42|Test feature|M|high\n")

        queue = AgentTaskQueue()
        queue._queue_path = queue_path
        result = queue.get_next_task()

        assert result is not None
        assert result["idea_id"] == 42
        assert result["description"] == "Test feature"