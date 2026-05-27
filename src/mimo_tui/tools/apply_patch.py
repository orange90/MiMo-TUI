"""Apply patch tool — Claude Code style file patching."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from mimo_tui.tools.base import BaseTool, ToolSpec

_BEGIN = "*** Begin of File"
_END = "*** End of File"


def _parse_patch(patch_text: str) -> list[dict[str, Any]]:
    """Parse Claude Code style patch into a list of file operations.

    Each operation is a dict with keys:
      - path: str
      - action: 'modify' | 'create' | 'delete'
      - lines: list of (op, text) where op is '+' | '-' | ' '
    """
    files: list[dict[str, Any]] = []
    current_path: str | None = None
    current_lines: list[tuple[str, str]] = []
    in_file = False

    for raw_line in patch_text.splitlines():
        line = raw_line.rstrip("\r")

        if line.startswith(_BEGIN):
            # Extract path: "*** Begin of File path/to/file"
            current_path = line[len(_BEGIN):].strip()
            current_lines = []
            in_file = True
            continue

        if line.startswith(_END):
            if current_path is not None:
                files.append({
                    "path": current_path,
                    "lines": current_lines,
                })
            current_path = None
            current_lines = []
            in_file = False
            continue

        if not in_file:
            continue

        if line and line[0] in ("+", "-", " "):
            op = line[0]
            # Convention: first char is the op indicator, rest is the literal
            # line content as it appears (or should appear) in the file.
            current_lines.append((op, line[1:]))
        elif line == "":
            # Blank line treated as context
            current_lines.append((" ", ""))

    return files


def _apply_file_op(op: dict[str, Any], project_root: Path) -> str:
    """Apply a single file operation. Returns a status string."""
    rel_path = op["path"]
    path = (project_root / rel_path).resolve()

    if not str(path).startswith(str(project_root)):
        return f"SKIP {rel_path}: outside project root"

    lines = op["lines"]
    has_plus = any(op_char == "+" for op_char, _ in lines)
    has_minus = any(op_char == "-" for op_char, _ in lines)
    has_space = any(op_char == " " for op_char, _ in lines)

    # Determine action
    if not path.exists() and has_plus:
        # New file
        content_lines = [text for op_char, text in lines if op_char == "+"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(content_lines) + "\n", encoding="utf-8")
        return f"CREATE {rel_path}"

    if path.exists() and has_minus and not has_plus and not has_space:
        # Delete file (all lines are removals)
        path.unlink()
        return f"DELETE {rel_path}"

    if path.exists() and (has_plus or has_minus):
        # Modify file: apply the patch
        original = path.read_text(encoding="utf-8").splitlines()
        result = _apply_hunks(original, lines)
        if result is None:
            return f"ERROR {rel_path}: patch did not match file content"
        path.write_text("\n".join(result) + "\n", encoding="utf-8")
        return f"MODIFY {rel_path}"

    return f"SKIP {rel_path}: no changes detected"


def _apply_hunks(original: list[str], hunks: list[tuple[str, str]]) -> list[str] | None:
    """Apply hunks to original file content.

    Strategy: walk through the original lines and the hunks simultaneously.
    Context lines (' ') must match. '-' lines are removed. '+' lines are inserted.
    """
    result: list[str] = []
    orig_idx = 0
    hunk_idx = 0

    while hunk_idx < len(hunks):
        op, text = hunks[hunk_idx]

        if op == " ":
            # Context line — must match original
            if orig_idx >= len(original) or original[orig_idx] != text:
                # Try to find the match by scanning ahead (small window)
                found = False
                for scan in range(orig_idx, min(orig_idx + 5, len(original))):
                    if original[scan] == text:
                        # Copy skipped lines as-is
                        for i in range(orig_idx, scan):
                            result.append(original[i])
                        orig_idx = scan
                        found = True
                        break
                if not found:
                    return None
            result.append(original[orig_idx])
            orig_idx += 1
            hunk_idx += 1

        elif op == "-":
            # Removal — skip original line if it matches
            if orig_idx < len(original) and original[orig_idx] == text:
                orig_idx += 1
                hunk_idx += 1
            elif orig_idx < len(original):
                # Mismatch — try scanning ahead
                found = False
                for scan in range(orig_idx, min(orig_idx + 5, len(original))):
                    if original[scan] == text:
                        for i in range(orig_idx, scan):
                            result.append(original[i])
                        orig_idx = scan + 1
                        hunk_idx += 1
                        found = True
                        break
                if not found:
                    return None
            else:
                return None

        elif op == "+":
            # Addition — insert new line
            result.append(text)
            hunk_idx += 1

        else:
            hunk_idx += 1

    # Append remaining original lines
    result.extend(original[orig_idx:])
    return result


class ApplyPatchTool(BaseTool):
    spec = ToolSpec(
        name="apply_patch",
        description=(
            "Apply a Claude Code style patch to create, modify, or delete files. "
            "Format: each file block starts with '*** Begin of File <path>' and ends "
            "with '*** End of File'. Lines prefixed with '+' are added, '-' are removed, "
            "' ' are context (must match). New files have only '+' lines. "
            "Deleted files have only '-' lines."
        ),
        parameters={
            "type": "object",
            "properties": {
                "patch": {
                    "type": "string",
                    "description": (
                        "The patch content in Claude Code format. "
                        "First character of each line is the op (+, -, space), "
                        "rest is the literal file content. Example:\n"
                        "*** Begin of File hello.py\n"
                        "+print('hello')\n"
                        "*** End of File"
                    ),
                },
            },
            "required": ["patch"],
        },
        danger_level=2,
    )

    def __init__(self, project_root: str = ".") -> None:
        self._project_root = Path(project_root).resolve()

    async def run(self, **kwargs: Any) -> str:
        patch_text = kwargs.get("patch", "")
        if not patch_text.strip():
            return "Error: patch content is required."

        ops = _parse_patch(patch_text)
        if not ops:
            return "Error: no file blocks found in patch. Use '*** Begin of File <path>' format."

        results: list[str] = []
        errors: list[str] = []

        for op in ops:
            status = _apply_file_op(op, self._project_root)
            results.append(status)
            if status.startswith("ERROR"):
                errors.append(status)

        summary = "\n".join(results)
        if errors:
            return f"Patch applied with errors:\n{summary}"
        return f"Patch applied successfully:\n{summary}"
