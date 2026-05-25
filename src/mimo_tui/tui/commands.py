"""Slash-command registry and parser."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass
class Command:
    name: str
    description: str
    handler: str  # method name on the screen


COMMANDS: list[Command] = [
    Command("model", "Switch model: /model <name>", "cmd_model"),
    Command("mode", "Switch mode: /mode <chat|plan|agent|yolo>", "cmd_mode"),
    Command("lang", "Switch language: /lang <en|zh_CN>", "cmd_lang"),
    Command("theme", "Switch theme: /theme <name>", "cmd_theme"),
    Command("clear", "Clear conversation", "cmd_clear"),
    Command("compact", "Compact conversation to a summary: /compact [focus]", "cmd_compact"),
    Command("attach", "Attach a file: /attach <path>", "cmd_attach"),
    Command("search", "Search sessions: /search <query>", "cmd_search"),
    Command("tools", "List available tools", "cmd_tools"),
    Command("mcp", "Open MCP server manager", "cmd_mcp"),
    Command("plan", "Set plan: /plan <description>", "cmd_plan"),
    Command("todo", "Add todo: /todo <item>", "cmd_todo"),
    Command("fork", "Fork this session", "cmd_fork"),
    Command("save", "Save session", "cmd_save"),
    Command("load", "Load session", "cmd_load"),
    Command("protocol", "Switch protocol: /protocol <openai|anthropic>", "cmd_protocol"),
    Command("help", "Show help", "cmd_help"),
]

COMMAND_MAP: dict[str, Command] = {c.name: c for c in COMMANDS}


def parse_command(text: str) -> tuple[str, list[str]] | None:
    """Parse '/cmd arg1 arg2' → ('cmd', ['arg1', 'arg2']) or None."""
    text = text.strip()
    if not text.startswith("/"):
        return None
    parts = text[1:].split()
    if not parts:
        return None
    return parts[0].lower(), parts[1:]


def completions_for(prefix: str) -> list[str]:
    """Return slash-command names starting with prefix."""
    p = prefix.lstrip("/").lower()
    return [f"/{c.name}" for c in COMMANDS if c.name.startswith(p)]
