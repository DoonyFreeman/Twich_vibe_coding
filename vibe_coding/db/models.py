"""Database models for Vibe Coding."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class Complexity(str, Enum):
    """Complexity levels for ideas."""

    S = "S"
    M = "M"
    L = "L"
    XL = "XL"


class Priority(str, Enum):
    """Priority levels for ideas."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class IdeaStatus(str, Enum):
    """Status values for ideas."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


@dataclass
class Idea:
    """Idea model representing a feature request from chat."""

    id: int | None
    description: str
    complexity: Complexity
    priority: Priority
    status: IdeaStatus
    vote_count: int
    author: str
    created_at: str
    updated_at: str
    approved_at: str | None = None
    completed_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert idea to dictionary.

        Returns:
            Dictionary representation of the idea.
        """
        return {
            "id": self.id,
            "description": self.description,
            "complexity": self.complexity.value,
            "priority": self.priority.value,
            "status": self.status.value,
            "vote_count": self.vote_count,
            "author": self.author,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "approved_at": self.approved_at,
            "completed_at": self.completed_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Idea":
        """Create idea from dictionary.

        Args:
            data: Dictionary with idea data.

        Returns:
            Idea instance.
        """
        return cls(
            id=data["id"],
            description=data["description"],
            complexity=Complexity(data["complexity"]),
            priority=Priority(data["priority"]),
            status=IdeaStatus(data["status"]),
            vote_count=data["vote_count"],
            author=data["author"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            approved_at=data.get("approved_at"),
            completed_at=data.get("completed_at"),
        )


@dataclass
class Vote:
    """Vote model representing a user's vote on an idea."""

    id: int | None
    idea_id: int
    username: str
    value: int
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        """Convert vote to dictionary.

        Returns:
            Dictionary representation of the vote.
        """
        return {
            "id": self.id,
            "idea_id": self.idea_id,
            "username": self.username,
            "value": self.value,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Vote":
        """Create vote from dictionary.

        Args:
            data: Dictionary with vote data.

        Returns:
            Vote instance.
        """
        return cls(
            id=data["id"],
            idea_id=data["idea_id"],
            username=data["username"],
            value=data["value"],
            created_at=data["created_at"],
        )