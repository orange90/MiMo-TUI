"""Async SQLite session store."""
from __future__ import annotations

import asyncio
import time
import uuid
from pathlib import Path

import aiosqlite

from mimo_tui.sessions.migrations import run_migrations
from mimo_tui.sessions.models import MessageRow, SessionRow, ToolCallRow
from mimo_tui.utils.logging import get_logger

log = get_logger(__name__)


class SessionStore:
    def __init__(self, db_path: Path) -> None:
        self._path = db_path
        self._db: aiosqlite.Connection | None = None
        self._write_queue: asyncio.Queue[tuple[str, tuple[object, ...]]] = asyncio.Queue()
        self._writer_task: asyncio.Task[None] | None = None

    async def open(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._db = await aiosqlite.connect(self._path)
        self._db.row_factory = aiosqlite.Row
        await self._db.execute("PRAGMA journal_mode=WAL")
        await self._db.execute("PRAGMA foreign_keys=ON")
        await run_migrations(self._db)
        self._writer_task = asyncio.create_task(self._writer_loop())

    async def close(self) -> None:
        if self._writer_task:
            self._writer_task.cancel()
        if self._db:
            await self._db.close()

    async def _writer_loop(self) -> None:
        while True:
            sql, params = await self._write_queue.get()
            try:
                assert self._db is not None
                await self._db.execute(sql, params)
                await self._db.commit()
            except Exception as e:
                log.error("db write error", error=str(e))
            finally:
                self._write_queue.task_done()

    def _enqueue(self, sql: str, params: tuple[object, ...] = ()) -> None:
        self._write_queue.put_nowait((sql, params))

    # ── Sessions ──

    async def create_session(self, model: str, mode: str, title: str = "Untitled") -> SessionRow:
        now = int(time.time() * 1000)
        sid = str(uuid.uuid4())
        self._enqueue(
            "INSERT INTO sessions (id, title, model, mode, created_at, updated_at) VALUES (?,?,?,?,?,?)",
            (sid, title, model, mode, now, now),
        )
        return SessionRow(id=sid, title=title, model=model, mode=mode, created_at=now, updated_at=now)

    async def list_sessions(self) -> list[SessionRow]:
        assert self._db is not None
        cursor = await self._db.execute(
            "SELECT id,title,model,mode,created_at,updated_at FROM sessions ORDER BY updated_at DESC"
        )
        rows = await cursor.fetchall()
        return [SessionRow(*r) for r in rows]

    async def update_session_title(self, session_id: str, title: str) -> None:
        now = int(time.time() * 1000)
        self._enqueue(
            "UPDATE sessions SET title=?, updated_at=? WHERE id=?",
            (title, now, session_id),
        )

    async def touch_session(self, session_id: str) -> None:
        now = int(time.time() * 1000)
        self._enqueue("UPDATE sessions SET updated_at=? WHERE id=?", (now, session_id))

    # ── Messages ──

    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        reasoning: str = "",
    ) -> MessageRow:
        now = int(time.time() * 1000)
        mid = str(uuid.uuid4())
        self._enqueue(
            "INSERT INTO messages (id, session_id, role, content, reasoning, created_at) VALUES (?,?,?,?,?,?)",
            (mid, session_id, role, content, reasoning, now),
        )
        # update FTS
        self._enqueue(
            "INSERT INTO messages_fts (rowid, content) SELECT rowid, content FROM messages WHERE id=?",
            (mid,),
        )
        await self.touch_session(session_id)
        return MessageRow(id=mid, session_id=session_id, role=role, content=content, reasoning=reasoning, created_at=now)

    async def list_messages(self, session_id: str) -> list[MessageRow]:
        assert self._db is not None
        cursor = await self._db.execute(
            "SELECT id, session_id, role, content, reasoning, created_at FROM messages WHERE session_id=? ORDER BY created_at",
            (session_id,),
        )
        rows = await cursor.fetchall()
        return [MessageRow(*r) for r in rows]

    async def search_messages(self, query: str, limit: int = 20) -> list[MessageRow]:
        assert self._db is not None
        cursor = await self._db.execute(
            """
            SELECT m.id, m.session_id, m.role, m.content, m.reasoning, m.created_at
            FROM messages m
            JOIN messages_fts fts ON m.rowid = fts.rowid
            WHERE messages_fts MATCH ?
            ORDER BY rank
            LIMIT ?
            """,
            (query, limit),
        )
        rows = await cursor.fetchall()
        return [MessageRow(*r) for r in rows]

    # ── Tool calls ──

    async def add_tool_call(
        self,
        message_id: str,
        tool_name: str,
        arguments: str,
        result: str,
    ) -> ToolCallRow:
        now = int(time.time() * 1000)
        tid = str(uuid.uuid4())
        self._enqueue(
            "INSERT INTO tool_calls (id, message_id, tool_name, arguments, result, created_at) VALUES (?,?,?,?,?,?)",
            (tid, message_id, tool_name, arguments, result, now),
        )
        return ToolCallRow(id=tid, message_id=message_id, tool_name=tool_name, arguments=arguments, result=result, created_at=now)
