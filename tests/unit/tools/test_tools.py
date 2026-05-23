"""Tests for builtin tools."""
import pytest
from pathlib import Path


@pytest.mark.asyncio
async def test_read_file(tmp_path: Path) -> None:
    from mimo_tui.tools.read_file import ReadFileTool
    p = tmp_path / "hello.txt"
    p.write_text("line1\nline2\nline3")
    tool = ReadFileTool()
    result = await tool.run(path=str(p))
    assert "line1" in result
    assert "line2" in result


@pytest.mark.asyncio
async def test_read_file_not_found(tmp_path: Path) -> None:
    from mimo_tui.tools.read_file import ReadFileTool
    tool = ReadFileTool()
    result = await tool.run(path=str(tmp_path / "nope.txt"))
    assert "Error" in result


@pytest.mark.asyncio
async def test_write_file(tmp_path: Path) -> None:
    from mimo_tui.tools.write_file import WriteFileTool
    tool = WriteFileTool(write_paths=[str(tmp_path)], project_root=str(tmp_path))
    p = tmp_path / "out.txt"
    result = await tool.run(path=str(p), content="hello world")
    assert "Written" in result
    assert p.read_text() == "hello world"


@pytest.mark.asyncio
async def test_write_file_sandbox_violation(tmp_path: Path) -> None:
    from mimo_tui.tools.write_file import WriteFileTool
    tool = WriteFileTool(write_paths=[str(tmp_path / "allowed")], project_root=str(tmp_path))
    result = await tool.run(path="/etc/hosts", content="bad")
    assert "Error" in result


@pytest.mark.asyncio
async def test_edit_file(tmp_path: Path) -> None:
    from mimo_tui.tools.edit_file import EditFileTool
    p = tmp_path / "code.py"
    p.write_text("def foo():\n    return 1\n")
    tool = EditFileTool(write_paths=[str(tmp_path)], project_root=str(tmp_path))
    result = await tool.run(path=str(p), old_string="return 1", new_string="return 2")
    assert "return 2" in p.read_text()


@pytest.mark.asyncio
async def test_glob(tmp_path: Path) -> None:
    from mimo_tui.tools.glob import GlobTool
    (tmp_path / "a.py").write_text("")
    (tmp_path / "b.py").write_text("")
    tool = GlobTool()
    result = await tool.run(pattern="*.py", cwd=str(tmp_path))
    assert "a.py" in result
    assert "b.py" in result


@pytest.mark.asyncio
async def test_shell_exec_allowed(tmp_path: Path) -> None:
    from mimo_tui.tools.shell_exec import ShellExecTool
    tool = ShellExecTool(allowlist=["echo"], project_root=str(tmp_path))
    result = await tool.run(command="echo hello", cwd=str(tmp_path))
    assert "hello" in result


@pytest.mark.asyncio
async def test_shell_exec_denied(tmp_path: Path) -> None:
    from mimo_tui.tools.shell_exec import ShellExecTool
    tool = ShellExecTool(allowlist=["echo"], project_root=str(tmp_path))
    result = await tool.run(command="rm -rf /", cwd=str(tmp_path))
    assert "Error" in result or "not in the shell allowlist" in result


@pytest.mark.asyncio
async def test_todo_write(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import mimo_tui.tools.todo_write as tw
    monkeypatch.setattr(tw, "_TODO_FILE", tmp_path / "todos.json")
    from mimo_tui.tools.todo_write import TodoWriteTool
    tool = TodoWriteTool()
    await tool.run(action="add", text="write tests")
    result = await tool.run(action="list")
    assert "write tests" in result
    await tool.run(action="complete", index=1)
    result2 = await tool.run(action="list")
    assert "[x]" in result2
