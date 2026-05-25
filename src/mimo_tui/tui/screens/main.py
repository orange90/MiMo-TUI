"""Main application screen — Claude Code style layout with right sidebar panels."""
from __future__ import annotations

import asyncio
import json
import time
from pathlib import Path
from typing import Any

from textual.app import ComposeResult
from textual.binding import Binding
from textual.css.query import NoMatches
from textual.screen import Screen
from textual.containers import Horizontal, Vertical
from textual.widgets import Static

from mimo_tui.agent.approval import ApprovalCallback, ApprovalRequest
from mimo_tui.agent.loop import (
    AgentLoop,
    AudioEvent,
    DoneEvent,
    ErrorEvent,
    ReasoningEvent,
    TextEvent,
    ToolCallArgFragEvent,
    ToolCallExecutingEvent,
    ToolCallResultEvent,
    ToolCallStartEvent,
    UsageEvent,
)
from mimo_tui.agent.modes import AgentMode
from mimo_tui.agent.registry import build_registry
from mimo_tui.audio.formats import AudioData
from mimo_tui.audio.player import AudioPlayer
from mimo_tui.client.protocol_selector import get_client
from mimo_tui.config.loader import load_config, save_config
from mimo_tui.config.schema import AppConfig
from mimo_tui.constants import SESSIONS_DB
from mimo_tui.i18n.translator import set_language, t
from mimo_tui.mcp.manager import MCPManager
from mimo_tui.providers.capabilities import get_capabilities
from mimo_tui.sessions.store import SessionStore
from mimo_tui.tui.commands import parse_command
from mimo_tui.tui.screens.approval import ApprovalPanel
from mimo_tui.tui.theme import THEMES, get_theme_css
from mimo_tui.tui.widgets.activity_bar import ActivityBar
from mimo_tui.tui.widgets.chat_log import ChatLog
from mimo_tui.tui.widgets.composer import Composer
from mimo_tui.tui.widgets.header_bar import HeaderBar
from mimo_tui.tui.widgets.sessions_list import SessionsList
from mimo_tui.tui.widgets.sidebar_panel import RightSidebar
from mimo_tui.tui.widgets.status_bar import StatusBar


class MainScreen(Screen):  # type: ignore[type-arg]
    BINDINGS = [
        Binding("ctrl+m", "open_model_picker", "Model"),
        Binding("ctrl+l", "toggle_lang", "Lang"),
        Binding("ctrl+t", "toggle_theme", "Theme"),
        Binding("ctrl+n", "new_session", "New"),
        Binding("ctrl+s", "toggle_sessions", "Sessions"),
        Binding("ctrl+b", "toggle_sidebar", "Sidebar"),
        Binding("ctrl+q", "quit_app", "Quit"),
    ]

    DEFAULT_CSS = """
    MainScreen {
        layout: vertical;
        background: #1a1b2e;
    }
    #main-body {
        layout: horizontal;
        height: 1fr;
    }
    #center-pane {
        layout: vertical;
        width: 1fr;
        background: #1a1b2e;
    }
    """

    def __init__(self, cfg: AppConfig) -> None:
        super().__init__()
        self._cfg = cfg
        self._store: SessionStore | None = None
        self._session_id: str | None = None
        self._loop: AgentLoop | None = None
        self._client: Any = None
        self._audio_player = AudioPlayer(on_state_change=self._on_audio_state_change)
        self._audio_buf = b""
        self._audio_mime = "audio/wav"
        self._streaming = False
        self._pending_tool_name: str | None = None
        self._mcp = MCPManager()
        self._stream_worker: Any = None
        self._reasoning_start: float = 0.0
        self._task_counter = 0
        self._tool_anchors: dict[int, int] = {}
        self._tool_arg_buffers: dict[int, str] = {}
        self._tool_names: dict[int, str] = {}
        self._tool_started_at: dict[int, float] = {}

    def compose(self) -> ComposeResult:
        yield HeaderBar(model=self._cfg.model.name, mode=self._cfg.mode, title="Untitled")
        with Horizontal(id="main-body"):
            yield SessionsList()
            with Vertical(id="center-pane"):
                yield ChatLog()
                yield ApprovalPanel()
                yield ActivityBar()
                yield Composer(placeholder=t("chat.placeholder"))
            yield RightSidebar()
        yield StatusBar()

    async def on_mount(self) -> None:
        self._store = SessionStore(SESSIONS_DB)
        await self._store.open()

        self._client = get_client(self._cfg)
        registry = build_registry(self._cfg)

        for srv in self._cfg.mcp.servers:
            if srv.enabled:
                await self._mcp.start_server(srv)
        for mcp_tool in self._mcp.get_tools():
            registry.register(mcp_tool)

        self._loop = AgentLoop(
            cfg=self._cfg,
            client=self._client,
            registry=registry,
            mode=AgentMode(self._cfg.mode),
            approval_cb=self._approval_callback,
        )

        await self._new_session()
        await self._refresh_sessions_list()

        caps = get_capabilities(self._cfg.model.name)
        sb = self.query_one(StatusBar)
        sb.update_all(
            model=self._cfg.model.name,
            mode=self._cfg.mode,
            endpoint=self._cfg.endpoint.url,
            lang=self._cfg.language,
            context_window=caps.context_window,
        )

        header = self.query_one(HeaderBar)
        header.update_model(self._cfg.model.name)
        header.update_context(used=0, window=caps.context_window)
        self.query_one(Composer).focus_input()

        chat = self.query_one(ChatLog)
        chat.write_system_message(t("chat.empty_hint"))

    async def _new_session(self) -> None:
        assert self._store is not None
        session = await self._store.create_session(
            model=self._cfg.model.name,
            mode=self._cfg.mode,
        )
        self._session_id = session.id
        if self._loop:
            self._loop.reset()

    async def _refresh_sessions_list(self) -> None:
        if not self._store:
            return
        sessions = await self._store.list_sessions()
        sl = self.query_one(SessionsList)
        await sl.load_sessions([(s.id, s.title) for s in sessions])

    # -- Approval callback --

    async def _approval_callback(self, req: ApprovalRequest) -> bool:
        try:
            panel = self.query_one(ApprovalPanel)
        except NoMatches:
            return False
        return await panel.request(req)

    # -- Message handlers --

    async def on_composer_message_submitted(self, event: Composer.MessageSubmitted) -> None:
        text = event.text.strip()
        if not text:
            return

        parsed = parse_command(text)
        if parsed:
            await self._handle_command(*parsed)
            return

        await self._send_message(text)

    async def on_composer_stop_requested(self, _: Composer.StopRequested) -> None:
        if self._stream_worker is not None:
            try:
                self._stream_worker.cancel()
            except Exception:
                pass
        self._set_streaming(False)
        self.query_one(ChatLog).write_system_message("Stopped.", style="dim #f7768e")

    async def on_sessions_list_new_session_requested(self, _: SessionsList.NewSessionRequested) -> None:
        await self._new_session()
        self.query_one(ChatLog).clear()
        self.query_one(ChatLog).write_system_message(t("chat.empty_hint"))
        header = self.query_one(HeaderBar)
        header.update_title("Untitled")
        header.update_context(used=0)
        self.query_one(StatusBar).update_all(reset_tokens=True)
        await self._refresh_sessions_list()

    async def on_sessions_list_session_selected(self, event: SessionsList.SessionSelected) -> None:
        await self._load_session(event.session_id)

    async def _load_session(self, session_id: str) -> None:
        if not self._store:
            return
        self._session_id = session_id

        sessions = await self._store.list_sessions()
        for s in sessions:
            if s.id == session_id:
                self.query_one(HeaderBar).update_title(s.title)
                break

        messages = await self._store.list_messages(session_id)
        chat = self.query_one(ChatLog)
        chat.clear()
        from mimo_tui.client.schemas import Message
        history: list[Message] = []
        for msg in messages:
            if msg.role == "user":
                chat.begin_user_message(msg.content)
            elif msg.role == "assistant":
                chat.begin_assistant_message()
                chat.append_assistant_chunk(msg.content)
                chat.flush_assistant_stream()
            history.append(Message(role=msg.role, content=msg.content))  # type: ignore[arg-type]
        if self._loop:
            self._loop.load_history(history)

    # -- Send message & stream --

    async def _send_message(self, text: str) -> None:
        if self._streaming:
            return
        chat = self.query_one(ChatLog)
        chat.begin_user_message(text)

        if self._store and self._session_id:
            await self._store.add_message(self._session_id, "user", text)
            sessions = await self._store.list_sessions()
            for s in sessions:
                if s.id == self._session_id and s.title == "Untitled":
                    new_title = text[:40]
                    await self._store.update_session_title(self._session_id, new_title)
                    self.query_one(HeaderBar).update_title(new_title)
                    break
            await self._refresh_sessions_list()

        self._set_streaming(True)
        chat.begin_assistant_message()
        self._reasoning_start = time.monotonic()

        # Update tasks in sidebar
        self._task_counter += 1
        sidebar = self.query_one(RightSidebar)
        task_label = f"turn {self._session_id[:8] if self._session_id else ''}... (in progress)"
        sidebar.tasks_section.set_items([task_label])

        self._audio_buf = b""
        self._audio_mime = "audio/wav"

        assert self._loop is not None
        self._stream_worker = self.run_worker(
            self._run_stream(text),
            name="agent-stream",
            exclusive=True,
            group="stream",
        )

    def _extract_arg_hint(self, partial_args: str) -> tuple[str, str] | None:
        """Best-effort extraction of a key→value pair from partial JSON args for live UI hints.

        Tries to parse `partial_args` as JSON, then picks a friendly key in
        priority order (path > file_path > command > pattern > url > query > content).
        For very long values (e.g. full file content) returns just a length summary.
        Returns (label, value) or None if no useful key is yet present.
        """
        priority = [
            ("path", "path"),
            ("file_path", "path"),
            ("command", "$"),
            ("pattern", "pattern"),
            ("url", "url"),
            ("query", "query"),
        ]
        try:
            parsed = json.loads(partial_args or "{}")
        except json.JSONDecodeError:
            for key, label in priority:
                marker = f'"{key}"'
                pos = partial_args.find(marker)
                if pos < 0:
                    continue
                rest = partial_args[pos + len(marker):]
                colon = rest.find(":")
                if colon < 0:
                    continue
                rest = rest[colon + 1:].lstrip()
                if rest.startswith('"'):
                    end = rest.find('"', 1)
                    value = rest[1:end] if end > 0 else rest[1:]
                    if value:
                        return label, value[:80]
            return None

        if not isinstance(parsed, dict):
            return None
        for key, label in priority:
            if key in parsed and isinstance(parsed[key], str) and parsed[key]:
                return label, parsed[key][:80]
        if "content" in parsed and isinstance(parsed["content"], str):
            return "content", f"{len(parsed['content'])} chars"
        return None

    async def _run_stream(self, text: str) -> None:
        chat = self.query_one(ChatLog)
        sb = self.query_one(StatusBar)
        sidebar = self.query_one(RightSidebar)
        content_buf = ""
        reasoning_buf = ""
        reasoning_started = False
        self._set_activity("calling model")

        try:
            assert self._loop is not None
            async for event in self._loop.run(text):
                if isinstance(event, TextEvent):
                    if reasoning_started:
                        elapsed = time.monotonic() - self._reasoning_start
                        chat.end_thinking(elapsed)
                        reasoning_started = False
                    content_buf += event.text
                    chat.append_assistant_chunk(event.text)
                    self._set_activity("writing reply")

                elif isinstance(event, ReasoningEvent):
                    if not reasoning_started:
                        chat.begin_thinking()
                        reasoning_started = True
                    reasoning_buf += event.text
                    chat.append_thinking(event.text)
                    self._set_activity("thinking")

                elif isinstance(event, AudioEvent):
                    self._audio_buf += event.data
                    self._audio_mime = event.mime_type
                    if event.finished:
                        await self._play_audio()

                elif isinstance(event, ToolCallStartEvent):
                    if reasoning_started:
                        elapsed = time.monotonic() - self._reasoning_start
                        chat.end_thinking(elapsed)
                        reasoning_started = False
                    self._pending_tool_name = event.tool_name
                    chat.flush_assistant_stream()
                    content_buf = ""
                    self._tool_names[event.index] = event.tool_name
                    self._tool_arg_buffers[event.index] = ""
                    self._tool_started_at[event.index] = time.monotonic()
                    chat.write_tool_start(event.tool_name)
                    self._set_activity(f"preparing {event.tool_name}")

                elif isinstance(event, ToolCallArgFragEvent):
                    buf = self._tool_arg_buffers.get(event.index, "") + event.fragment
                    self._tool_arg_buffers[event.index] = buf
                    hint = self._extract_arg_hint(buf)
                    if hint is not None:
                        label, value = hint
                        prev = getattr(self, "_tool_arg_last_hint", {}).get(event.index)
                        if prev != (label, value):
                            chat.write_tool_progress(label, value)
                            if not hasattr(self, "_tool_arg_last_hint"):
                                self._tool_arg_last_hint: dict[int, tuple[str, str]] = {}
                            self._tool_arg_last_hint[event.index] = (label, value)
                    name = self._tool_names.get(event.index, "tool")
                    self._set_activity(f"streaming args for {name}")

                elif isinstance(event, ToolCallExecutingEvent):
                    summary = ""
                    for key in ("path", "file_path", "command", "pattern", "url", "query"):
                        val = event.arguments.get(key)
                        if isinstance(val, str) and val:
                            summary = f"{key}={val[:80]}"
                            break
                    if not summary and "content" in event.arguments and isinstance(event.arguments["content"], str):
                        summary = f"content={len(event.arguments['content'])} chars"
                    chat.write_tool_executing(event.tool_name, summary)
                    self._set_activity(f"running {event.tool_name}")

                elif isinstance(event, ToolCallResultEvent):
                    idx = next(
                        (i for i, n in self._tool_names.items() if n == event.tool_name),
                        None,
                    )
                    elapsed_ms = 0.0
                    if idx is not None and idx in self._tool_started_at:
                        elapsed_ms = (time.monotonic() - self._tool_started_at.pop(idx)) * 1000
                        self._tool_names.pop(idx, None)
                        self._tool_arg_buffers.pop(idx, None)
                        if hasattr(self, "_tool_arg_last_hint"):
                            self._tool_arg_last_hint.pop(idx, None)
                    chat.write_tool_done(
                        event.tool_name,
                        event.result,
                        event.approved,
                        elapsed_ms=elapsed_ms,
                    )
                    if self._store and self._session_id:
                        pass
                    self._set_activity("calling model")

                elif isinstance(event, UsageEvent):
                    sb.update_all(
                        prompt_tokens=event.prompt_tokens,
                        completion_tokens=event.completion_tokens,
                        latency_ms=event.latency_ms,
                    )
                    self.query_one(HeaderBar).update_context(
                        used=event.prompt_tokens + event.completion_tokens
                    )

                elif isinstance(event, ErrorEvent):
                    if reasoning_started:
                        chat.end_thinking()
                        reasoning_started = False
                    chat.flush_assistant_stream()
                    chat.write_error(event.message)
                    self._set_activity(None)

                elif isinstance(event, DoneEvent):
                    if reasoning_started:
                        elapsed = time.monotonic() - self._reasoning_start
                        chat.end_thinking(elapsed)
                        reasoning_started = False
                    chat.flush_assistant_stream()
                    if self._audio_buf:
                        await self._play_audio()
                    if self._store and self._session_id and content_buf:
                        await self._store.add_message(
                            self._session_id, "assistant", content_buf, reasoning_buf
                        )
                    task_label = f"turn {self._session_id[:8] if self._session_id else ''}... (completed)"
                    sidebar.tasks_section.set_items([task_label])
                    self._set_activity(None)

        except asyncio.CancelledError:
            if reasoning_started:
                chat.end_thinking()
            chat.flush_assistant_stream()
        except Exception as e:
            if reasoning_started:
                chat.end_thinking()
            chat.flush_assistant_stream()
            chat.write_error(str(e))
        finally:
            try:
                self._set_activity(None)
            except Exception:
                pass
            self._set_streaming(False)
            self.query_one(Composer).focus_input()

    async def _play_audio(self) -> None:
        if not self._audio_buf:
            return
        chat = self.query_one(ChatLog)
        import uuid as _uuid
        audio_id = str(_uuid.uuid4())[:8]
        chat.write_audio_card(audio_id)
        audio = AudioData(raw=self._audio_buf, mime_type=self._audio_mime)
        self._audio_buf = b""
        asyncio.create_task(self._audio_player.play(audio))

    def _on_audio_state_change(self, playing: bool) -> None:
        try:
            self.query_one(StatusBar).set_audio_playing(playing)
        except Exception:
            pass

    def _set_streaming(self, streaming: bool) -> None:
        self._streaming = streaming
        try:
            self.query_one(Composer).set_streaming(streaming)
        except Exception:
            pass

    def _set_activity(self, label: str | None) -> None:
        """Drive both the bottom status-bar spinner and the inline activity bar."""
        try:
            self.query_one(StatusBar).set_activity(label)
        except Exception:
            pass
        try:
            self.query_one(ActivityBar).set_activity(label)
        except Exception:
            pass

    # -- Actions --

    async def action_open_model_picker(self) -> None:
        from mimo_tui.tui.screens.model_picker import ModelPicker
        model = await self.app.push_screen_wait(ModelPicker())
        if model:
            await self._apply_model(model)

    async def _apply_model(self, model: str) -> None:
        self._cfg.model.name = model
        caps = get_capabilities(model)
        self._cfg.model.reasoning = caps.reasoning
        self._cfg.model.vision = caps.vision
        self._cfg.model.audio_out = caps.audio_out
        self._cfg.model.tools = caps.tools
        save_config(self._cfg)
        self._client = get_client(self._cfg)
        registry = build_registry(self._cfg)
        assert self._loop is not None
        self._loop = AgentLoop(
            cfg=self._cfg,
            client=self._client,
            registry=registry,
            mode=AgentMode(self._cfg.mode),
            approval_cb=self._approval_callback,
        )
        self.query_one(StatusBar).update_all(model=model, context_window=caps.context_window)
        header = self.query_one(HeaderBar)
        header.update_model(model)
        header.update_context(window=caps.context_window)
        self.query_one(ChatLog).write_system_message(t("commands.model_set", model=model))

    def action_toggle_sessions(self) -> None:
        self.query_one(SessionsList).toggle_collapse()

    def action_toggle_sidebar(self) -> None:
        self.query_one(RightSidebar).toggle_collapse()

    def action_toggle_lang(self) -> None:
        new_lang = "zh_CN" if self._cfg.language == "en" else "en"
        self._cfg.language = new_lang
        set_language(new_lang)
        save_config(self._cfg)
        self.query_one(StatusBar).update_all(lang=new_lang)
        self.query_one(ChatLog).write_system_message(t("commands.lang_set", lang=new_lang))

    def action_toggle_theme(self) -> None:
        theme_names = list(THEMES.keys())
        current = self._cfg.theme
        idx = theme_names.index(current) if current in theme_names else 0
        new_theme = theme_names[(idx + 1) % len(theme_names)]
        self._cfg.theme = new_theme
        save_config(self._cfg)
        self.query_one(ChatLog).write_system_message(t("commands.theme_set", theme=new_theme))

    async def action_new_session(self) -> None:
        await self._new_session()
        self.query_one(ChatLog).clear()
        self.query_one(ChatLog).write_system_message(t("chat.empty_hint"))
        header = self.query_one(HeaderBar)
        header.update_title("Untitled")
        header.update_context(used=0)
        self.query_one(StatusBar).update_all(reset_tokens=True)
        await self._refresh_sessions_list()
        sidebar = self.query_one(RightSidebar)
        sidebar.tasks_section.clear_items()
        sidebar.plan_section.clear_items()

    def action_quit_app(self) -> None:
        self.app.exit()

    # -- Slash command handlers --

    async def _handle_command(self, cmd: str, args: list[str]) -> None:
        chat = self.query_one(ChatLog)

        if cmd == "model":
            if args:
                await self._apply_model(args[0])
            else:
                await self.action_open_model_picker()

        elif cmd == "mode":
            if args and args[0] in ("chat", "plan", "agent", "yolo"):
                self._cfg.mode = args[0]  # type: ignore[assignment]
                save_config(self._cfg)
                assert self._loop is not None
                self._loop._mode = AgentMode(args[0])
                self.query_one(StatusBar).update_all(mode=args[0])
                chat.write_system_message(t("commands.mode_set", mode=args[0]))
            else:
                chat.write_system_message("Usage: /mode <chat|plan|agent|yolo>")

        elif cmd == "lang":
            if args and args[0] in ("en", "zh_CN"):
                self._cfg.language = args[0]  # type: ignore[assignment]
                set_language(args[0])
                save_config(self._cfg)
                self.query_one(StatusBar).update_all(lang=args[0])
                chat.write_system_message(t("commands.lang_set", lang=args[0]))
            else:
                chat.write_system_message("Usage: /lang <en|zh_CN>")

        elif cmd == "theme":
            if args and args[0] in THEMES:
                self._cfg.theme = args[0]
                save_config(self._cfg)
                chat.write_system_message(t("commands.theme_set", theme=args[0]))
            else:
                chat.write_system_message(f"Available themes: {', '.join(THEMES)}")

        elif cmd == "clear":
            chat.clear()
            if self._loop:
                self._loop.reset()
            self.query_one(StatusBar).update_all(reset_tokens=True)
            self.query_one(HeaderBar).update_context(used=0)
            chat.write_system_message(t("commands.cleared"))

        elif cmd == "compact":
            await self._compact_conversation(" ".join(args))

        elif cmd == "protocol":
            if args and args[0] in ("openai", "anthropic"):
                self._cfg.protocol = args[0]  # type: ignore[assignment]
                save_config(self._cfg)
                self._client = get_client(self._cfg)
                chat.write_system_message(f"Protocol set to {args[0]}")
            else:
                chat.write_system_message("Usage: /protocol <openai|anthropic>")

        elif cmd == "attach":
            if args:
                await self._attach_file(args[0])
            else:
                chat.write_system_message("Usage: /attach <path>")

        elif cmd == "search":
            query = " ".join(args)
            if query and self._store:
                results = await self._store.search_messages(query)
                if results:
                    lines = [f"{r.role}: {r.content[:80]}" for r in results[:10]]
                    chat.write_system_message("Search results:\n" + "\n".join(lines))
                else:
                    chat.write_system_message("No results found.")
            else:
                chat.write_system_message("Usage: /search <query>")

        elif cmd == "tools":
            registry = build_registry(self._cfg)
            names = registry.names()
            chat.write_system_message("Available tools: " + ", ".join(names))

        elif cmd == "plan":
            sidebar = self.query_one(RightSidebar)
            if args:
                sidebar.plan_section.set_items([" ".join(args)])
                chat.write_system_message("Plan updated.")
            else:
                chat.write_system_message("Usage: /plan <description>")

        elif cmd == "todo":
            sidebar = self.query_one(RightSidebar)
            if args:
                sidebar.todos_section.add_item(" ".join(args))
                chat.write_system_message("Todo added.")
            else:
                chat.write_system_message("Usage: /todo <item>")

        elif cmd == "help":
            chat.write_system_message(t("commands.help_text"))

        elif cmd == "fork":
            await self._new_session()
            chat.write_system_message("Session forked.")

        elif cmd == "save":
            chat.write_system_message(f"Session saved (id={self._session_id})")

        elif cmd == "load":
            sessions = await (self._store.list_sessions() if self._store else [])  # type: ignore[assignment]
            if sessions and args:
                for s in sessions:
                    if s.id.startswith(args[0]) or s.title == args[0]:
                        await self._load_session(s.id)
                        chat.write_system_message(f"Loaded session: {s.title}")
                        return
                chat.write_system_message("Session not found")
            else:
                lines = [f"{s.id[:8]}  {s.title}" for s in sessions[:10]]
                chat.write_system_message("Sessions:\n" + "\n".join(lines))

        elif cmd == "mcp":
            tools = self._mcp.get_tools()
            if tools:
                chat.write_system_message("MCP tools: " + ", ".join(t.spec.name for t in tools))
            else:
                chat.write_system_message("No MCP tools registered.")

        else:
            chat.write_system_message(t("commands.unknown", cmd=cmd))

    async def _compact_conversation(self, focus: str) -> None:
        chat = self.query_one(ChatLog)
        if self._streaming:
            chat.write_system_message(t("commands.compact_busy"))
            return
        if self._loop is None or self._loop.history_size() == 0:
            chat.write_system_message(t("commands.compact_empty"))
            return

        chat.write_system_message(t("commands.compact_running"))
        self._set_streaming(True)
        try:
            summary, est_tokens = await self._loop.compact(focus.strip())
        except Exception as e:
            chat.write_system_message(t("commands.compact_failed", error=str(e)))
            return
        finally:
            self._set_streaming(False)

        chat.clear()
        chat.write_system_message(
            t("commands.compact_done", tokens=est_tokens)
        )
        chat.write_system_message(summary, style="dim #c0caf5")

        if self._store and self._session_id:
            await self._store.delete_messages(self._session_id)
            await self._store.add_message(
                self._session_id, "user", f"[Compacted summary]\n{summary}"
            )
            await self._store.add_message(
                self._session_id,
                "assistant",
                "Got it — I have the recap and will continue from here.",
            )

        # Reflect the post-compact baseline: history is non-empty (the
        # summary), so show its estimated size rather than zero.
        self.query_one(StatusBar).update_all(
            reset_tokens=True, prompt_tokens=est_tokens
        )
        self.query_one(HeaderBar).update_context(used=est_tokens)
        self.query_one(Composer).focus_input()

    async def _attach_file(self, path: str) -> None:
        chat = self.query_one(ChatLog)
        p = Path(path)
        if not p.exists():
            chat.write_system_message(f"File not found: {path}")
            return
        if not self._cfg.model.vision:
            chat.write_system_message(f"Current model does not support vision. Switch to MiMo-V2-Omni.")
            return
        from mimo_tui.images.pipeline import build_image_content
        try:
            block = build_image_content(p)
            chat.write_system_message(f"Attached: {path} ({p.stat().st_size} bytes)")
            if self._loop:
                self._loop._pending_attachment = block  # type: ignore[attr-defined]
        except Exception as e:
            chat.write_system_message(f"Failed to attach: {e}")
