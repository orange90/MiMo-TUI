"""Tests for the SQLite session store."""
import pytest
from pathlib import Path

from mimo_tui.sessions.store import SessionStore


@pytest.mark.asyncio
async def test_create_and_list_sessions(tmp_path: Path) -> None:
    store = SessionStore(tmp_path / "test.db")
    await store.open()
    session = await store.create_session(model="MiMo-V2.5-Pro", mode="chat", title="Test")
    await store._write_queue.join()
    sessions = await store.list_sessions()
    assert any(s.id == session.id for s in sessions)
    await store.close()


@pytest.mark.asyncio
async def test_add_and_list_messages(tmp_path: Path) -> None:
    store = SessionStore(tmp_path / "test.db")
    await store.open()
    session = await store.create_session(model="MiMo-V2.5-Pro", mode="chat")
    await store._write_queue.join()
    msg = await store.add_message(session.id, "user", "Hello!")
    await store._write_queue.join()
    messages = await store.list_messages(session.id)
    assert any(m.content == "Hello!" for m in messages)
    await store.close()


@pytest.mark.asyncio
async def test_search_messages(tmp_path: Path) -> None:
    store = SessionStore(tmp_path / "test.db")
    await store.open()
    session = await store.create_session(model="MiMo-V2.5-Pro", mode="chat")
    await store._write_queue.join()
    await store.add_message(session.id, "user", "unique_search_term_xyz")
    await store._write_queue.join()
    results = await store.search_messages("unique_search_term_xyz")
    assert any("unique_search_term_xyz" in r.content for r in results)
    await store.close()
