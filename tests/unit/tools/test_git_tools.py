"""Tests for the Git tools (git_status, git_log, git_diff)."""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from mimo_tui.tools.git_tools import GitDiffTool, GitLogTool, GitStatusTool


@pytest.fixture
def git_repo(tmp_path: Path) -> Path:
    """Create a temporary git repo with one commit."""
    subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=tmp_path, capture_output=True, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, capture_output=True, check=True)
    (tmp_path / "README.md").write_text("hello\n")
    subprocess.run(["git", "add", "."], cwd=tmp_path, capture_output=True, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=tmp_path, capture_output=True, check=True)
    return tmp_path


@pytest.fixture
def status_tool(git_repo: Path) -> GitStatusTool:
    return GitStatusTool(project_root=str(git_repo))


@pytest.fixture
def log_tool(git_repo: Path) -> GitLogTool:
    return GitLogTool(project_root=str(git_repo))


@pytest.fixture
def diff_tool(git_repo: Path) -> GitDiffTool:
    return GitDiffTool(project_root=str(git_repo))


@pytest.mark.asyncio
async def test_git_status_clean(status_tool: GitStatusTool) -> None:
    result = await status_tool.run()
    assert result == "(no output)"


@pytest.mark.asyncio
async def test_git_status_dirty(status_tool: GitStatusTool, git_repo: Path) -> None:
    (git_repo / "new.txt").write_text("new file\n")
    result = await status_tool.run()
    assert "new.txt" in result


@pytest.mark.asyncio
async def test_git_log_default(log_tool: GitLogTool) -> None:
    result = await log_tool.run()
    assert "init" in result


@pytest.mark.asyncio
async def test_git_log_custom_n(log_tool: GitLogTool) -> None:
    result = await log_tool.run(n=1)
    assert "init" in result
    lines = [l for l in result.strip().splitlines() if l.strip()]
    assert len(lines) == 1


@pytest.mark.asyncio
async def test_git_log_with_path(log_tool: GitLogTool) -> None:
    result = await log_tool.run(path="README.md")
    assert "init" in result


@pytest.mark.asyncio
async def test_git_diff_no_changes(diff_tool: GitDiffTool) -> None:
    result = await diff_tool.run()
    assert result == "(no output)"


@pytest.mark.asyncio
async def test_git_diff_with_changes(diff_tool: GitDiffTool, git_repo: Path) -> None:
    (git_repo / "README.md").write_text("modified\n")
    result = await diff_tool.run()
    assert "hello" in result
    assert "modified" in result
    assert "@@" in result


@pytest.mark.asyncio
async def test_git_diff_staged(diff_tool: GitDiffTool, git_repo: Path) -> None:
    (git_repo / "staged.txt").write_text("staged content\n")
    subprocess.run(["git", "add", "staged.txt"], cwd=git_repo, capture_output=True, check=True)
    result = await diff_tool.run(staged=True)
    assert "staged content" in result


@pytest.mark.asyncio
async def test_git_diff_with_path(diff_tool: GitDiffTool, git_repo: Path) -> None:
    (git_repo / "README.md").write_text("changed\n")
    (git_repo / "other.txt").write_text("other\n")
    result = await diff_tool.run(path="README.md")
    assert "changed" in result
    assert "other" not in result


@pytest.mark.asyncio
async def test_git_diff_context_lines(diff_tool: GitDiffTool, git_repo: Path) -> None:
    (git_repo / "README.md").write_text("modified\n")
    result = await diff_tool.run(context_lines=1)
    assert "modified" in result
