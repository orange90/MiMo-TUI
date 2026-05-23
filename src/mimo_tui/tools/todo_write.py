from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from mimo_tui.tools.base import BaseTool, ToolSpec

_TODO_FILE = Path(".mimo") / "todos.json"


class TodoWriteTool(BaseTool):
    spec = ToolSpec(
        name="todo_write",
        description="Manage a TODO list for the current session. Actions: add, complete, list, clear.",
        parameters={
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["add", "complete", "list", "clear"],
                    "description": "Action to perform",
                },
                "text": {"type": "string", "description": "TODO text (for add)"},
                "index": {"type": "integer", "description": "TODO index (for complete, 1-based)"},
            },
            "required": ["action"],
        },
        danger_level=0,
    )

    def _load(self) -> list[dict[str, Any]]:
        if _TODO_FILE.exists():
            return json.loads(_TODO_FILE.read_text())  # type: ignore[no-any-return]
        return []

    def _save(self, todos: list[dict[str, Any]]) -> None:
        _TODO_FILE.parent.mkdir(parents=True, exist_ok=True)
        _TODO_FILE.write_text(json.dumps(todos, indent=2))

    async def run(self, action: str, text: str = "", index: int = 0, **_: Any) -> str:
        todos = self._load()
        if action == "add":
            todos.append({"text": text, "done": False})
            self._save(todos)
            return f"Added TODO: {text}"
        elif action == "complete":
            if 1 <= index <= len(todos):
                todos[index - 1]["done"] = True
                self._save(todos)
                return f"Completed: {todos[index-1]['text']}"
            return f"No TODO at index {index}"
        elif action == "list":
            if not todos:
                return "No TODOs"
            lines = [
                f"{'[x]' if t['done'] else '[ ]'} {i+1}. {t['text']}"
                for i, t in enumerate(todos)
            ]
            return "\n".join(lines)
        elif action == "clear":
            self._save([])
            return "TODOs cleared"
        return f"Unknown action: {action}"
