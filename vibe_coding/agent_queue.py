"""Agent integration module for task queue."""

import asyncio
import logging
from pathlib import Path
from typing import Any

from vibe_coding.config import get_config
from vibe_coding.db.models import Idea, IdeaStatus
from vibe_coding.db.repository import IdeaRepository

log = logging.getLogger(__name__)


class AgentTaskQueue:
    """File-based task queue for Agent integration."""

    def __init__(self, db_path: Path | None = None) -> None:
        """Initialize task queue.

        Args:
            db_path: Path to SQLite database.
        """
        self._config = get_config()
        self._agent_config = self._config["agent"]
        self._db_path = db_path or Path(self._config["database"]["path"])
        self._queue_path = Path(self._agent_config["task_queue_path"])
        self._repo = IdeaRepository(self._db_path)
        self._running = False

    async def start(self) -> None:
        """Start monitoring for approved tasks."""
        await self._repo.create_tables()
        log.info("AgentTaskQueue started")
        self._running = True
        asyncio.create_task(self._monitor_loop())

    async def stop(self) -> None:
        """Stop monitoring."""
        self._running = False
        await self._repo.close()
        log.info("AgentTaskQueue stopped")

    async def _monitor_loop(self) -> None:
        """Monitor for approved tasks and add to queue."""
        while self._running:
            await self._check_approved_tasks()
            await asyncio.sleep(5)

    async def _check_approved_tasks(self) -> None:
        """Check for newly approved tasks."""
        approved = await self._repo.get_ideas_by_status(IdeaStatus.APPROVED)

        for idea in approved:
            if idea.id:
                await self._add_to_queue(idea)

    async def _add_to_queue(self, idea: Idea) -> None:
        """Add approved idea to task queue.

        Args:
            idea: Approved idea to queue.
        """
        self._queue_path.parent.mkdir(parents=True, exist_ok=True)

        line = f"{idea.id}|{idea.description}|{idea.complexity.value}|{idea.priority.value}\n"

        existing = []
        if self._queue_path.exists():
            existing = self._queue_path.read_text().strip().split("\n")

        task_exists = any(line.startswith(f"{idea.id}|") for line in existing if line)
        if task_exists:
            return

        with self._queue_path.open("a") as f:
            f.write(line)

        log.info(f"Added idea #{idea.id} to task queue")

    def get_next_task(self) -> dict[str, Any] | None:
        """Get next task from queue.

        Returns:
            Task dict or None if queue empty.
        """
        if not self._queue_path.exists():
            return None

        lines = self._queue_path.read_text().strip().split("\n")
        if not lines or not lines[0]:
            return None

        first_line = lines[0]
        parts = first_line.split("|")
        if len(parts) < 4:
            return None

        return {
            "idea_id": int(parts[0]),
            "description": parts[1],
            "complexity": parts[2],
            "priority": parts[3],
        }

    def complete_task(self, idea_id: int) -> bool:
        """Mark task as completed and remove from queue.

        Args:
            idea_id: Completed idea ID.

        Returns:
            True if removed successfully.
        """
        if not self._queue_path.exists():
            return False

        lines = self._queue_path.read_text().strip().split("\n")
        new_lines = [line for line in lines if not line.startswith(f"{idea_id}|")]

        self._queue_path.write_text("\n".join(new_lines))
        log.info(f"Completed task #{idea_id}")
        return True


async def main() -> None:
    """Main entry point for agent queue monitoring."""
    logging.basicConfig(level=logging.INFO)

    queue = AgentTaskQueue()
    await queue.start()

    try:
        while True:
            await asyncio.sleep(60)
    except KeyboardInterrupt:
        await queue.stop()


if __name__ == "__main__":
    asyncio.run(main())