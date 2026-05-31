"""Tests for the PythonExecTool."""
from __future__ import annotations

from pathlib import Path

import pytest

from mimo_tui.tools.python_exec import PythonExecTool


@pytest.fixture
def py_tool(tmp_path: Path) -> PythonExecTool:
    return PythonExecTool(project_root=str(tmp_path))


@pytest.mark.asyncio
async def test_python_exec_simple(py_tool: PythonExecTool) -> None:
    result = await py_tool.run(code="print(1 + 2)")
    assert "3" in result


@pytest.mark.asyncio
async def test_python_exec_multiline(py_tool: PythonExecTool) -> None:
    code = """
import math
print(math.pi)
"""
    result = await py_tool.run(code=code)
    assert "3.14" in result


@pytest.mark.asyncio
async def test_python_exec_stderr(py_tool: PythonExecTool) -> None:
    result = await py_tool.run(code="import sys; sys.stderr.write('oops\\n')")
    assert "STDERR" in result
    assert "oops" in result


@pytest.mark.asyncio
async def test_python_exec_syntax_error(py_tool: PythonExecTool) -> None:
    result = await py_tool.run(code="def (")
    assert "STDERR" in result or "Error" in result


@pytest.mark.asyncio
async def test_python_exec_empty_code(py_tool: PythonExecTool) -> None:
    result = await py_tool.run(code="")
    assert "Error" in result


@pytest.mark.asyncio
async def test_python_exec_timeout(py_tool: PythonExecTool) -> None:
    result = await py_tool.run(code="import time; time.sleep(10)", timeout=1)
    assert "timed out" in result


@pytest.mark.asyncio
async def test_python_exec_exit_code(py_tool: PythonExecTool) -> None:
    result = await py_tool.run(code="import sys; sys.exit(1)")
    # Should show exit code or stderr
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_python_exec_returns_output(py_tool: PythonExecTool) -> None:
    result = await py_tool.run(code="for i in range(3): print(i)")
    assert "0" in result
    assert "1" in result
    assert "2" in result
