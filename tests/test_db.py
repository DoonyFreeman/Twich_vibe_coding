"""Tests for database repository."""

import pytest
from pathlib import Path

from vibe_coding.db.models import Complexity, Idea, IdeaStatus, Priority, Vote
from vibe_coding.db.repository import IdeaRepository, VoteRepository


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    """Create temporary database path."""
    return tmp_path / "test.db"


@pytest.fixture
async def idea_repo(db_path: Path) -> IdeaRepository:
    """Create IdeaRepository with temporary database."""
    repo = IdeaRepository(db_path)
    await repo.create_tables()
    yield repo
    await repo.close()


@pytest.fixture
async def vote_repo(db_path: Path) -> VoteRepository:
    """Create VoteRepository with temporary database."""
    repo = VoteRepository(db_path)
    await repo.create_tables()
    yield repo
    await repo.close()


@pytest.fixture
async def combined_repo(db_path: Path) -> tuple[IdeaRepository, VoteRepository]:
    """Create both repositories with shared database."""
    idea_repo = IdeaRepository(db_path)
    vote_repo = VoteRepository(db_path)
    await idea_repo.create_tables()
    yield idea_repo, vote_repo
    await idea_repo.close()
    await vote_repo.close()


class TestIdeaRepository:
    """Tests for IdeaRepository."""

    async def test_create_tables(self, db_path: Path) -> None:
        """Test table creation."""
        repo = IdeaRepository(db_path)
        await repo.create_tables()
        await repo.close()

        assert db_path.exists()

    async def test_create_idea(self, idea_repo: IdeaRepository) -> None:
        """Test creating an idea."""
        idea = await idea_repo.create_idea(
            description="Test idea",
            complexity=Complexity.M,
            priority=Priority.MEDIUM,
            author="testuser",
        )

        assert idea.id is not None
        assert idea.description == "Test idea"
        assert idea.complexity == Complexity.M
        assert idea.priority == Priority.MEDIUM
        assert idea.status == IdeaStatus.PENDING
        assert idea.vote_count == 0

    async def test_get_idea(self, idea_repo: IdeaRepository) -> None:
        """Test getting an idea by ID."""
        created = await idea_repo.create_idea(
            description="Test idea",
            complexity=Complexity.M,
            priority=Priority.MEDIUM,
            author="testuser",
        )

        retrieved = await idea_repo.get_idea(created.id)

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.description == created.description

    async def test_get_idea_not_found(self, idea_repo: IdeaRepository) -> None:
        """Test getting non-existent idea returns None."""
        result = await idea_repo.get_idea(999)

        assert result is None

    async def test_get_all_ideas(self, idea_repo: IdeaRepository) -> None:
        """Test getting all ideas."""
        await idea_repo.create_idea("Idea 1", Complexity.S, Priority.LOW, "user1")
        await idea_repo.create_idea("Idea 2", Complexity.M, Priority.HIGH, "user2")

        ideas = await idea_repo.get_all_ideas()

        assert len(ideas) == 2

    async def test_get_ideas_by_status(self, idea_repo: IdeaRepository) -> None:
        """Test filtering ideas by status."""
        idea1 = await idea_repo.create_idea("Idea 1", Complexity.S, Priority.LOW, "user1")
        idea2 = await idea_repo.create_idea("Idea 2", Complexity.M, Priority.HIGH, "user2")
        await idea_repo.update_idea_status(idea1.id, IdeaStatus.APPROVED)

        pending = await idea_repo.get_ideas_by_status(IdeaStatus.PENDING)
        approved = await idea_repo.get_ideas_by_status(IdeaStatus.APPROVED)

        assert len(pending) == 1
        assert len(approved) == 1

    async def test_update_idea_status(self, idea_repo: IdeaRepository) -> None:
        """Test updating idea status."""
        idea = await idea_repo.create_idea("Test idea", Complexity.M, Priority.MEDIUM, "user")

        updated = await idea_repo.update_idea_status(idea.id, IdeaStatus.APPROVED)

        assert updated is not None
        assert updated.status == IdeaStatus.APPROVED
        assert updated.approved_at is not None

    async def test_delete_idea(self, idea_repo: IdeaRepository) -> None:
        """Test deleting an idea."""
        idea = await idea_repo.create_idea("Test idea", Complexity.M, Priority.MEDIUM, "user")

        deleted = await idea_repo.delete_idea(idea.id)

        assert deleted is True
        assert await idea_repo.get_idea(idea.id) is None


class TestVoteRepository:
    """Tests for VoteRepository."""

    async def test_create_tables(self, db_path: Path) -> None:
        """Test table creation."""
        repo = VoteRepository(db_path)
        await repo.create_tables()
        await repo.close()

        assert db_path.exists()

    async def test_add_vote(self, combined_repo: tuple[IdeaRepository, VoteRepository]) -> None:
        """Test adding a vote."""
        idea_repo, vote_repo = combined_repo
        idea = await idea_repo.create_idea("Test idea", Complexity.M, Priority.MEDIUM, "author")

        vote = await vote_repo.add_vote(idea.id, "voter1", 1)

        assert vote.id is not None
        assert vote.idea_id == idea.id
        assert vote.username == "voter1"
        assert vote.value == 1

    async def test_add_negative_vote(self, combined_repo: tuple[IdeaRepository, VoteRepository]) -> None:
        """Test adding a negative vote."""
        idea_repo, vote_repo = combined_repo
        idea = await idea_repo.create_idea("Test idea", Complexity.M, Priority.MEDIUM, "author")

        vote = await vote_repo.add_vote(idea.id, "hater", -1)

        assert vote.value == -1

    async def test_update_vote(self, combined_repo: tuple[IdeaRepository, VoteRepository]) -> None:
        """Test updating a vote."""
        idea_repo, vote_repo = combined_repo
        idea = await idea_repo.create_idea("Test idea", Complexity.M, Priority.MEDIUM, "author")
        await vote_repo.add_vote(idea.id, "voter", 1)

        updated = await vote_repo.add_vote(idea.id, "voter", -1)

        assert updated.value == -1

    async def test_remove_vote(self, combined_repo: tuple[IdeaRepository, VoteRepository]) -> None:
        """Test removing a vote."""
        idea_repo, vote_repo = combined_repo
        idea = await idea_repo.create_idea("Test idea", Complexity.M, Priority.MEDIUM, "author")
        await vote_repo.add_vote(idea.id, "voter", 1)

        removed = await vote_repo.remove_vote(idea.id, "voter")

        assert removed is True

    async def test_get_vote_count(self, combined_repo: tuple[IdeaRepository, VoteRepository]) -> None:
        """Test getting vote count."""
        idea_repo, vote_repo = combined_repo
        idea = await idea_repo.create_idea("Test idea", Complexity.M, Priority.MEDIUM, "author")
        await vote_repo.add_vote(idea.id, "voter1", 1)
        await vote_repo.add_vote(idea.id, "voter2", 1)
        await vote_repo.add_vote(idea.id, "voter3", -1)

        count = await vote_repo.get_vote_count(idea.id)

        assert count == 1

    async def test_get_user_vote(self, combined_repo: tuple[IdeaRepository, VoteRepository]) -> None:
        """Test getting user's vote."""
        idea_repo, vote_repo = combined_repo
        idea = await idea_repo.create_idea("Test idea", Complexity.M, Priority.MEDIUM, "author")
        await vote_repo.add_vote(idea.id, "voter", 1)

        vote = await vote_repo.get_user_vote(idea.id, "voter")

        assert vote is not None
        assert vote.value == 1

    async def test_get_user_vote_not_found(self, combined_repo: tuple[IdeaRepository, VoteRepository]) -> None:
        """Test getting non-existent user vote returns None."""
        idea_repo, vote_repo = combined_repo
        idea = await idea_repo.create_idea("Test idea", Complexity.M, Priority.MEDIUM, "author")

        vote = await vote_repo.get_user_vote(idea.id, "nonexistent")

        assert vote is None