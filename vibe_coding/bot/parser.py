"""Message parser for Twitch chat commands."""

import re
from dataclasses import dataclass
from typing import Literal

from vibe_coding.bot.connection import ChatMessage


@dataclass
class ParsedIdea:
    """Parsed idea from chat message."""

    description: str
    complexity: str
    priority: str


@dataclass
class ParsedVote:
    """Parsed vote command."""

    idea_id: int
    value: Literal[1, -1]


@dataclass
class ParsedApprove:
    """Parsed approve command."""

    idea_id: int


@dataclass
class ParsedReject:
    """Parsed reject command."""

    idea_id: int


@dataclass
class ParsedList:
    """Parsed list command."""


@dataclass
class ParsedPending:
    """Parsed pending command."""


class MessageParser:
    """Parser for Twitch chat messages."""

    IDEA_PATTERN = re.compile(
        r"^\[IDEA\]\s*(.+?)"
        r"(?:,\s*Complexity:\s*([SMLXL]))?"
        r"(?:,\s*Priority:\s*(low|medium|high))?$",
        re.IGNORECASE,
    )

    VOTE_PATTERN = re.compile(r"^!(?:vote)\s*#?(\d+)?\s*([+-])1$", re.IGNORECASE)

    APPROVE_PATTERN = re.compile(r"^!approve\s*#?(\d+)$", re.IGNORECASE)

    REJECT_PATTERN = re.compile(r"^!reject\s*#?(\d+)$", re.IGNORECASE)

    LIST_PATTERN = re.compile(r"^!list$", re.IGNORECASE)

    PENDING_PATTERN = re.compile(r"^!pending$", re.IGNORECASE)

    def parse(self, message: ChatMessage) -> (
        ParsedIdea
        | ParsedVote
        | ParsedApprove
        | ParsedReject
        | ParsedList
        | ParsedPending
        | None
    ):
        """Parse a chat message.

        Args:
            message: Chat message to parse.

        Returns:
            Parsed command or None if no match.
        """
        text = message.message.strip()

        idea = self._parse_idea(text)
        if idea:
            return idea

        vote = self._parse_vote(text)
        if vote:
            return vote

        approve = self._parse_approve(text)
        if approve:
            return approve

        reject = self._parse_reject(text)
        if reject:
            return reject

        if self.LIST_PATTERN.match(text):
            return ParsedList()

        if self.PENDING_PATTERN.match(text):
            return ParsedPending()

        return None

    def _parse_idea(self, text: str) -> ParsedIdea | None:
        """Parse [IDEA] message.

        Args:
            text: Message text.

        Returns:
            Parsed idea or None.
        """
        match = self.IDEA_PATTERN.match(text)
        if not match:
            return None

        description = match.group(1).strip()
        complexity = (match.group(2) or "M").upper()
        priority = (match.group(3) or "medium").lower()

        return ParsedIdea(
            description=description,
            complexity=complexity,
            priority=priority,
        )

    def _parse_vote(self, text: str) -> ParsedVote | None:
        """Parse !vote command.

        Args:
            text: Message text.

        Returns:
            Parsed vote or None.
        """
        match = self.VOTE_PATTERN.match(text)
        if not match:
            return None

        idea_id_str = match.group(1)
        value_str = match.group(2)

        idea_id = int(idea_id_str) if idea_id_str else 0
        value: Literal[1, -1] = 1 if value_str == "+" else -1

        return ParsedVote(idea_id=idea_id, value=value)

    def _parse_approve(self, text: str) -> ParsedApprove | None:
        """Parse !approve command.

        Args:
            text: Message text.

        Returns:
            Parsed approve or None.
        """
        match = self.APPROVE_PATTERN.match(text)
        if not match:
            return None

        idea_id = int(match.group(1))
        return ParsedApprove(idea_id=idea_id)

    def _parse_reject(self, text: str) -> ParsedReject | None:
        """Parse !reject command.

        Args:
            text: Message text.

        Returns:
            Parsed reject or None.
        """
        match = self.REJECT_PATTERN.match(text)
        if not match:
            return None

        idea_id = int(match.group(1))
        return ParsedReject(idea_id=idea_id)