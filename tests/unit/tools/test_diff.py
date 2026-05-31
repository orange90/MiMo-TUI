"""Tests for the DiffTool."""
from __future__ import annotations

import pytest
from pathlib import Path

from mimo_tui.tools.diff import DiffTool


@pytest.fixture
def diff_tool(tmp_path: Path) -> DiffTool:
    return DiffTool(project_root=str(tmp_path))


@pytest.fixture
def sample_files(tmp_path: Path) -> tuple[Path, Path]:
    a = tmp_path / "a.txt"
    b = tmp_path / "b.txt"
    a.write_text("line1\nline2\nline3\n")
    b.write_text("line1\nmodified\nline3\n")
    return a, b


@pytest.mark.asyncio
async def test_diff_files_shows_changes(diff_tool: DiffTool, sample_files: tuple[Path, Path], tmp_path: Path) -> None:
    a, b = sample_files
    result = await diff_tool.run(mode="files", file_a="a.txt", file_b="b.txt")
    assert "line2" in result
    assert "modified" in result
    assert "---" in result
    assert "+++" in result


@pytest.mark.asyncio
async def test_diff_files_identical(diff_tool: DiffTool, tmp_path: Path) -> None:
    f = tmp_path / "same.txt"
    f.write_text("hello\n")
    (tmp_path / "same2.txt").write_text("hello\n")
    result = await diff_tool.run(mode="files", file_a="same.txt", file_b="same2.txt")
    assert "identical" in result


@pytest.mark.asyncio
async def test_diff_files_missing_file(diff_tool: DiffTool, tmp_path: Path) -> None:
    (tmp_path / "exists.txt").write_text("x\n")
    result = await diff_tool.run(mode="files", file_a="exists.txt", file_b="nope.txt")
    assert "Error" in result


@pytest.mark.asyncio
async def test_diff_files_missing_args(diff_tool: DiffTool) -> None:
    result = await diff_tool.run(mode="files")
    assert "Error" in result


@pytest.mark.asyncio
async def test_diff_files_outside_root(diff_tool: DiffTool) -> None:
    result = await diff_tool.run(mode="files", file_a="../escape.txt", file_b="x.txt")
    assert "Error" in result
    assert "outside" in result


@pytest.mark.asyncio
async def test_diff_git_no_changes(diff_tool: DiffTool, tmp_path: Path) -> None:
    result = await diff_tool.run(mode="git")
    # No git repo or no changes
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_diff_unknown_mode(diff_tool: DiffTool) -> None:
    result = await diff_tool.run(mode="invalid")
    assert "Error" in result
    assert "unknown mode" in result


@pytest.mark.asyncio
async def test_diff_files_context_lines(diff_tool: DiffTool, sample_files: tuple[Path, Path]) -> None:
    result = await diff_tool.run(mode="files", file_a="a.txt", file_b="b.txt", context_lines=1)
    assert "modified" in result
