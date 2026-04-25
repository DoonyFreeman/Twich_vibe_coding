"""Database schema definitions for SQLite."""

CREATE_IDEAS_TABLE = """
CREATE TABLE IF NOT EXISTS ideas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    description TEXT NOT NULL,
    complexity TEXT NOT NULL CHECK (complexity IN ('S', 'M', 'L', 'XL')),
    priority TEXT NOT NULL DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high')),
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected', 'in_progress', 'completed')),
    vote_count INTEGER NOT NULL DEFAULT 0,
    author TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    approved_at TEXT,
    completed_at TEXT
)
"""

CREATE_VOTES_TABLE = """
CREATE TABLE IF NOT EXISTS votes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    idea_id INTEGER NOT NULL,
    username TEXT NOT NULL,
    value INTEGER NOT NULL CHECK (value IN (-1, 1)),
    created_at TEXT NOT NULL,
    FOREIGN KEY (idea_id) REFERENCES ideas (id) ON DELETE CASCADE,
    UNIQUE (idea_id, username)
)
"""

CREATE_IDEAS_INDEX = "CREATE INDEX IF NOT EXISTS idx_ideas_status ON ideas (status)"
CREATE_VOTES_INDEX = "CREATE INDEX IF NOT EXISTS idx_votes_idea_id ON votes (idea_id)"