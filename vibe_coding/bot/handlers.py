"""Handlers for Twitch chat commands."""

import asyncio
import logging
from pathlib import Path

from vibe_coding.bot.connection import ChatMessage
from vibe_coding.bot.parser import (
    ParsedApprove,
    ParsedIdea,
    ParsedList,
    ParsedPending,
    ParsedReject,
    ParsedVote,
    MessageParser,
)
from vibe_coding.config import get_config
from vibe_coding.db.models import Complexity, IdeaStatus, Priority
from vibe_coding.db.repository import IdeaRepository, VoteRepository

logger = logging.getLogger(__name__)


class IdeaHandler:
    """Handler for idea-related commands."""

    def __init__(self, db_path: Path | None = None) -> None:
        """Initialize handler.

        Args:
            db_path: Path to SQLite database.
        """
        self._parser = MessageParser()
        self._idea_repo = IdeaRepository(db_path)
        self._vote_repo = VoteRepository(db_path)
        self._config = get_config()
        self._vote_threshold = self._config["vibe_coding"]["vote_threshold"]
        self._channel = self._config["twitch"]["channel"]
        self._pending_notified: set[int] = set()
        self._output_queue: asyncio.Queue[str] = asyncio.Queue()
        self._run_task: asyncio.Task[None] | None = None

    async def start(self) -> None:
        """Start the handler."""
        await self._idea_repo.create_tables()
        self._run_task = asyncio.create_task(self._run_loop())
        logger.info("IdeaHandler started")

    async def stop(self) -> None:
        """Stop the handler."""
        if self._run_task:
            self._run_task.cancel()
            try:
                await self._run_task
            except asyncio.CancelledError:
                pass
        await self._idea_repo.close()
        await self._vote_repo.close()
        logger.info("IdeaHandler stopped")

    async def _run_loop(self) -> None:
        """Main loop for processing commands."""
        while True:
            await asyncio.sleep(0.1)

            pending = await self._idea_repo.get_ideas_by_status(IdeaStatus.PENDING)
            for idea in pending:
                if idea.id and idea.vote_count >= self._vote_threshold:
                    if idea.id not in self._pending_notified:
                        self._pending_notified.add(idea.id)
                        await self._output_queue.put(
                            f"@{idea.author}, idea #{idea.id} reached {idea.vote_count} votes! "
                            f"Type !approve #{idea.id} or !reject #{idea.id}"
                        )

    async def handle(self, message: ChatMessage) -> list[str]:
        """Handle a chat message.

        Args:
            message: Chat message.

        Returns:
            List of response messages.
        """
        parsed = self._parser.parse(message)
        if parsed is None:
            return []

        responses: list[str] = []

        if isinstance(parsed, ParsedIdea):
            responses.extend(await self._handle_idea(message, parsed))
        elif isinstance(parsed, ParsedVote):
            responses.extend(await self._handle_vote(message, parsed))
        elif isinstance(parsed, ParsedApprove):
            responses.extend(await self._handle_approve(message, parsed))
        elif isinstance(parsed, ParsedReject):
            responses.extend(await self._handle_reject(message, parsed))
        elif isinstance(parsed, ParsedList):
            responses.extend(await self._handle_list(message, parsed))
        elif isinstance(parsed, ParsedPending):
            responses.extend(await self._handle_pending(message, parsed))

        return responses

    async def _handle_idea(
        self, message: ChatMessage, parsed: ParsedIdea
    ) -> list[str]:
        """Handle [IDEA] command.

        Args:
            message: Chat message.
            parsed: Parsed idea.

        Returns:
            List of response messages.
        """
        try:
            complexity = Complexity(parsed.complexity)
            priority = Priority(parsed.priority)
        except ValueError:
            return ["Invalid complexity or priority. Use S/M/L/XL and low/medium/high."]

        idea = await self._idea_repo.create_idea(
            description=parsed.description,
            complexity=complexity,
            priority=priority,
            author=message.username,
        )

        logger.info(
            f"New idea #{idea.id}: {parsed.description} "
            f"(complexity={parsed.complexity}, priority={parsed.priority})"
        )

        return [
            f"@{message.username}, idea #{idea.id} created! "
            f"Use !vote +1 or !vote -1 to vote. Need {self._vote_threshold} votes to approve."
        ]

    async def _handle_vote(
        self, message: ChatMessage, parsed: ParsedVote
    ) -> list[str]:
        """Handle !vote command.

        Args:
            message: Chat message.
            parsed: Parsed vote.

        Returns:
            List of response messages.
        """
        idea_id = parsed.idea_id
        if idea_id == 0:
            return ["Please specify an idea ID: !vote #1 +1"]

        idea = await self._idea_repo.get_idea(idea_id)
        if idea is None:
            return [f"@{message.username}, idea #{idea_id} not found."]

        if idea.status != IdeaStatus.PENDING:
            return [
                f"@{message.username}, idea #{idea_id} is already {idea.status.value}."
            ]

        await self._vote_repo.add_vote(idea_id, message.username, parsed.value)
        vote_count = await self._vote_repo.get_vote_count(idea_id)
        await self._idea_repo.update_vote_count(idea_id, vote_count)

        logger.info(f"User {message.username} voted {parsed.value} on idea #{idea_id}")

        return [
            f"@{message.username}, vote recorded! Idea #{idea_id} now has {vote_count} votes."
        ]

    async def _handle_approve(
        self, message: ChatMessage, parsed: ParsedApprove
    ) -> list[str]:
        """Handle !approve command.

        Args:
            message: Chat message.
            parsed: Parsed approve.

        Returns:
            List of response messages.
        """
        idea = await self._idea_repo.get_idea(parsed.idea_id)
        if idea is None:
            return [f"@{message.username}, idea #{parsed.idea_id} not found."]

        await self._idea_repo.update_idea_status(parsed.idea_id, IdeaStatus.APPROVED)
        logger.info(f"Approved: idea #{parsed.idea_id}")

        return [
            f"Approved idea #{parsed.idea_id}: {idea.description}",
            "Adding to execution queue...",
        ]

    async def _handle_reject(
        self, message: ChatMessage, parsed: ParsedReject
    ) -> list[str]:
        """Handle !reject command.

        Args:
            message: Chat message.
            parsed: Parsed reject.

        Returns:
            List of response messages.
        """
        idea = await self._idea_repo.get_idea(parsed.idea_id)
        if idea is None:
            return [f"@{message.username}, idea #{parsed.idea_id} not found."]

        await self._idea_repo.update_idea_status(parsed.idea_id, IdeaStatus.REJECTED)
        logger.info(f"Rejected: idea #{parsed.idea_id}")

        return [f"Rejected idea #{parsed.idea_id}: {idea.description}"]

    async def _handle_list(
        self, message: ChatMessage, parsed: ParsedList
    ) -> list[str]:
        """Handle !list command.

        Args:
            message: Chat message.
            parsed: Parsed list.

        Returns:
            List of response messages.
        """
        ideas = await self._idea_repo.get_all_ideas()
        if not ideas:
            return ["No ideas yet! Use [IDEA] to propose one."]

        lines = ["Current ideas:"]
        for idea in ideas[:5]:
            if idea.id:
                lines.append(
                    f"  #{idea.id}: {idea.description[:50]} "
                    f"({idea.complexity.value}, {idea.status.value}, votes: {idea.vote_count})"
                )

        return lines

    async def _handle_pending(
        self, message: ChatMessage, parsed: ParsedPending
    ) -> list[str]:
        """Handle !pending command.

        Args:
            message: Chat message.
            parsed: Parsed pending.

        Returns:
            List of response messages.
        """
        pending = await self._idea_repo.get_ideas_by_status(IdeaStatus.PENDING)
        if not pending:
            return ["No pending ideas."]

        lines = ["Pending ideas (need 3+ votes):"]
        for idea in pending:
            if idea.id:
                lines.append(
                    f"  #{idea.id}: {idea.description[:50]} "
                    f"({idea.complexity.value}, votes: {idea.vote_count}/{self._vote_threshold})"
                )

        return lines

    async def get_output(self) -> str | None:
        """Get pending output message.

        Returns:
            Message or None.
        """
        try:
            return await asyncio.wait_for(self._output_queue.get(), timeout=0.01)
        except asyncio.TimeoutError:
            return None