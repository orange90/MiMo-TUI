"""SQLite schema migrations (version-tracked)."""
from __future__ import annotations

import aiosqlite

_MIGRATIONS: list[str] = [
    # v1 — initial schema
    """
    CREATE TABLE IF NOT EXISTS schema_version (version INTEGER PRIMARY KEY);
    INSERT OR IGNORE INTO schema_version VALUES (0);

    CREATE TABLE IF NOT EXISTS sessions (
        id          TEXT PRIMARY KEY,
        title       TEXT NOT NULL DEFAULT 'Untitled',
        model       TEXT NOT NULL DEFAULT '',
        mode        TEXT NOT NULL DEFAULT 'chat',
        created_at  INTEGER NOT NULL,
        updated_at  INTEGER NOT NULL
    );

    CREATE TABLE IF NOT EXISTS messages (
        id          TEXT PRIMARY KEY,
        session_id  TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
        role        TEXT NOT NULL,
        content     TEXT NOT NULL DEFAULT '',
        reasoning   TEXT NOT NULL DEFAULT '',
        created_at  INTEGER NOT NULL
    );

    CREATE TABLE IF NOT EXISTS tool_calls (
        id          TEXT PRIMARY KEY,
        message_id  TEXT NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
        tool_name   TEXT NOT NULL,
        arguments   TEXT NOT NULL DEFAULT '{}',
        result      TEXT NOT NULL DEFAULT '',
        created_at  INTEGER NOT NULL
    );

    CREATE TABLE IF NOT EXISTS attachments (
        id          TEXT PRIMARY KEY,
        message_id  TEXT REFERENCES messages(id) ON DELETE CASCADE,
        mime_type   TEXT NOT NULL,
        data        BLOB NOT NULL,
        filename    TEXT NOT NULL DEFAULT '',
        created_at  INTEGER NOT NULL
    );

    CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts USING fts5(
        content,
        content='messages',
        content_rowid='rowid'
    );
    """,
]


async def run_migrations(db: aiosqlite.Connection) -> None:
    await db.execute("CREATE TABLE IF NOT EXISTS schema_version (version INTEGER PRIMARY KEY)")
    await db.execute("INSERT OR IGNORE INTO schema_version VALUES (0)")
    row = await (await db.execute("SELECT version FROM schema_version")).fetchone()
    current = row[0] if row else 0

    for i, sql in enumerate(_MIGRATIONS):
        if i >= current:
            await db.executescript(sql)
            await db.execute("UPDATE schema_version SET version = ?", (i + 1,))
    await db.commit()
