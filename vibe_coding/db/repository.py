"""Database repository for CRUD operations on ideas and votes."""

import aiosqlite
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from vibe_coding.config import get_config
from vibe_coding.db.models import (
    Complexity,
    Idea,
    IdeaStatus,
    Priority,
    Vote,
)


class IdeaRepository:
    """Repository for managing ideas in the database."""

    def __init__(self, db_path: Path | None = None) -> None:
        """Initialize repository with database path.

        Args:
            db_path: Path to SQLite database. If None, uses config.yaml.
        """
        if db_path is None:
            config = get_config()
            db_path = Path(config["database"]["path"])
        self._db_path = db_path
        self._connection: aiosqlite.Connection | None = None

    async def _get_connection(self) -> aiosqlite.Connection:
        """Get or create database connection.

        Returns:
            SQLite connection.
        """
        if self._connection is None:
            self._connection = await aiosqlite.connect(str(self._db_path))
            self._connection.row_factory = aiosqlite.Row
        return self._connection

    async def close(self) -> None:
        """Close database connection."""
        if self._connection is not None:
            await self._connection.close()
            self._connection = None

    async def create_tables(self) -> None:
        """Create database tables if they don't exist."""
        from vibe_coding.db.schema import (
            CREATE_IDEAS_INDEX,
            CREATE_IDEAS_TABLE,
            CREATE_VOTES_INDEX,
            CREATE_VOTES_TABLE,
        )

        conn = await self._get_connection()
        await conn.executescript(CREATE_IDEAS_TABLE)
        await conn.executescript(CREATE_VOTES_TABLE)
        await conn.execute(CREATE_IDEAS_INDEX)
        await conn.execute(CREATE_VOTES_INDEX)
        await conn.commit()

    async def create_idea(
        self,
        description: str,
        complexity: Complexity,
        priority: Priority,
        author: str,
    ) -> Idea:
        """Create a new idea.

        Args:
            description: Idea description.
            complexity: Complexity level.
            priority: Priority level.
            author: Username who created the idea.

        Returns:
            Created idea with ID assigned.
        """
        now = datetime.now(timezone.utc).isoformat()
        conn = await self._get_connection()
        cursor = await conn.execute(
            """INSERT INTO ideas (description, complexity, priority, status, vote_count, author, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                description,
                complexity.value,
                priority.value,
                IdeaStatus.PENDING.value,
                0,
                author,
                now,
                now,
            ),
        )
        await conn.commit()
        idea_id = cursor.lastrowid

        return Idea(
            id=idea_id,
            description=description,
            complexity=complexity,
            priority=priority,
            status=IdeaStatus.PENDING,
            vote_count=0,
            author=author,
            created_at=now,
            updated_at=now,
        )

    async def get_idea(self, idea_id: int) -> Idea | None:
        """Get idea by ID.

        Args:
            idea_id: Idea ID.

        Returns:
            Idea if found, None otherwise.
        """
        conn = await self._get_connection()
        cursor = await conn.execute(
            "SELECT * FROM ideas WHERE id = ?",
            (idea_id,),
        )
        row = await cursor.fetchone()

        if row is None:
            return None

        return Idea.from_dict(dict(row))

    async def get_all_ideas(self) -> list[Idea]:
        """Get all ideas.

        Returns:
            List of all ideas.
        """
        conn = await self._get_connection()
        cursor = await conn.execute("SELECT * FROM ideas ORDER BY created_at DESC")
        rows = await cursor.fetchall()

        return [Idea.from_dict(dict(row)) for row in rows]

    async def get_ideas_by_status(self, status: IdeaStatus) -> list[Idea]:
        """Get ideas by status.

        Args:
            status: Status to filter by.

        Returns:
            List of ideas with the specified status.
        """
        conn = await self._get_connection()
        cursor = await conn.execute(
            "SELECT * FROM ideas WHERE status = ? ORDER BY created_at DESC",
            (status.value,),
        )
        rows = await cursor.fetchall()

        return [Idea.from_dict(dict(row)) for row in rows]

    async def update_idea_status(self, idea_id: int, status: IdeaStatus) -> Idea | None:
        """Update idea status.

        Args:
            idea_id: Idea ID.
            status: New status.

        Returns:
            Updated idea if found, None otherwise.
        """
        now = datetime.now(timezone.utc).isoformat()
        approved_at = now if status == IdeaStatus.APPROVED else None
        completed_at = now if status == IdeaStatus.COMPLETED else None

        conn = await self._get_connection()
        await conn.execute(
            """UPDATE ideas
               SET status = ?, updated_at = ?, approved_at = COALESCE(?, approved_at), completed_at = COALESCE(?, completed_at)
               WHERE id = ?""",
            (status.value, now, approved_at, completed_at, idea_id),
        )
        await conn.commit()

        return await self.get_idea(idea_id)

    async def update_vote_count(self, idea_id: int, vote_count: int) -> None:
        """Update idea vote count.

        Args:
            idea_id: Idea ID.
            vote_count: New vote count.
        """
        conn = await self._get_connection()
        await conn.execute(
            "UPDATE ideas SET vote_count = ?, updated_at = ? WHERE id = ?",
            (vote_count, datetime.utcnow().isoformat(), idea_id),
        )
        await conn.commit()

    async def delete_idea(self, idea_id: int) -> bool:
        """Delete idea and its votes.

        Args:
            idea_id: Idea ID.

        Returns:
            True if deleted, False otherwise.
        """
        conn = await self._get_connection()
        cursor = await conn.execute("DELETE FROM ideas WHERE id = ?", (idea_id,))
        await conn.commit()

        return cursor.rowcount > 0


class VoteRepository:
    """Repository for managing votes in the database."""

    def __init__(self, db_path: Path | None = None) -> None:
        """Initialize repository with database path.

        Args:
            db_path: Path to SQLite database. If None, uses config.yaml.
        """
        if db_path is None:
            config = get_config()
            db_path = Path(config["database"]["path"])
        self._db_path = db_path
        self._connection: aiosqlite.Connection | None = None

    async def _get_connection(self) -> aiosqlite.Connection:
        """Get or create database connection.

        Returns:
            SQLite connection.
        """
        if self._connection is None:
            self._connection = await aiosqlite.connect(str(self._db_path))
            self._connection.row_factory = aiosqlite.Row
        return self._connection

    async def close(self) -> None:
        """Close database connection."""
        if self._connection is not None:
            await self._connection.close()
            self._connection = None

    async def create_tables(self) -> None:
        """Create database tables if they don't exist."""
        from vibe_coding.db.schema import (
            CREATE_IDEAS_INDEX,
            CREATE_IDEAS_TABLE,
            CREATE_VOTES_INDEX,
            CREATE_VOTES_TABLE,
        )

        conn = await self._get_connection()
        await conn.executescript(CREATE_IDEAS_TABLE)
        await conn.executescript(CREATE_VOTES_TABLE)
        await conn.execute(CREATE_IDEAS_INDEX)
        await conn.execute(CREATE_VOTES_INDEX)
        await conn.commit()

    async def add_vote(self, idea_id: int, username: str, value: int) -> Vote:
        """Add or update a vote.

        Args:
            idea_id: Idea ID.
            username: Username who voted.
            value: Vote value (1 or -1).

        Returns:
            Created or updated vote.
        """
        now = datetime.now(timezone.utc).isoformat()
        conn = await self._get_connection()

        existing = await conn.execute(
            "SELECT * FROM votes WHERE idea_id = ? AND username = ?",
            (idea_id, username),
        )
        existing_row = await existing.fetchone()

        if existing_row:
            await conn.execute(
                "UPDATE votes SET value = ?, created_at = ? WHERE idea_id = ? AND username = ?",
                (value, now, idea_id, username),
            )
            vote_id = existing_row["id"]
        else:
            cursor = await conn.execute(
                "INSERT INTO votes (idea_id, username, value, created_at) VALUES (?, ?, ?, ?)",
                (idea_id, username, value, now),
            )
            vote_id = cursor.lastrowid

        await conn.commit()

        return Vote(id=vote_id, idea_id=idea_id, username=username, value=value, created_at=now)

    async def remove_vote(self, idea_id: int, username: str) -> bool:
        """Remove a vote.

        Args:
            idea_id: Idea ID.
            username: Username who voted.

        Returns:
            True if removed, False otherwise.
        """
        conn = await self._get_connection()
        cursor = await conn.execute(
            "DELETE FROM votes WHERE idea_id = ? AND username = ?",
            (idea_id, username),
        )
        await conn.commit()

        return cursor.rowcount > 0

    async def get_votes_for_idea(self, idea_id: int) -> list[Vote]:
        """Get all votes for an idea.

        Args:
            idea_id: Idea ID.

        Returns:
            List of votes for the idea.
        """
        conn = await self._get_connection()
        cursor = await conn.execute(
            "SELECT * FROM votes WHERE idea_id = ?",
            (idea_id,),
        )
        rows = await cursor.fetchall()

        return [Vote.from_dict(dict(row)) for row in rows]

    async def get_vote_count(self, idea_id: int) -> int:
        """Get total vote count for an idea.

        Args:
            idea_id: Idea ID.

        Returns:
            Sum of all vote values for the idea.
        """
        conn = await self._get_connection()
        cursor = await conn.execute(
            "SELECT SUM(value) as total FROM votes WHERE idea_id = ?",
            (idea_id,),
        )
        row = await cursor.fetchone()

        return row["total"] if row and row["total"] is not None else 0

    async def get_user_vote(self, idea_id: int, username: str) -> Vote | None:
        """Get user's vote for an idea.

        Args:
            idea_id: Idea ID.
            username: Username.

        Returns:
            Vote if found, None otherwise.
        """
        conn = await self._get_connection()
        cursor = await conn.execute(
            "SELECT * FROM votes WHERE idea_id = ? AND username = ?",
            (idea_id, username),
        )
        row = await cursor.fetchone()

        if row is None:
            return None

        return Vote.from_dict(dict(row))