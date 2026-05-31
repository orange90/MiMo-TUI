"""Tests for the ApplyPatchTool."""
from __future__ import annotations

from pathlib import Path

import pytest

from mimo_tui.tools.apply_patch import ApplyPatchTool, _parse_patch


@pytest.fixture
def patch_tool(tmp_path: Path) -> ApplyPatchTool:
    return ApplyPatchTool(project_root=str(tmp_path))


# ── Parser tests ──


def test_parse_create_file() -> None:
    # Convention: op char at col 0, rest is literal content (no extra space).
    patch = (
        "*** Begin of File hello.py\n"
        "+print('hello')\n"
        "+print('world')\n"
        "*** End of File"
    )
    ops = _parse_patch(patch)
    assert len(ops) == 1
    assert ops[0]["path"] == "hello.py"
    assert len(ops[0]["lines"]) == 2
    assert ops[0]["lines"][0] == ("+", "print('hello')")


def test_parse_multiple_files() -> None:
    patch = (
        "*** Begin of File a.py\n"
        "+ a = 1\n"
        "*** End of File\n"
        "*** Begin of File b.py\n"
        "+ b = 2\n"
        "*** End of File"
    )
    ops = _parse_patch(patch)
    assert len(ops) == 2
    assert ops[0]["path"] == "a.py"
    assert ops[1]["path"] == "b.py"


def test_parse_modify_file() -> None:
    # Convention: op char at col 0, rest is literal file content (no extra space).
    patch = (
        "*** Begin of File main.py\n"
        " def main():\n"
        "-    print('old')\n"
        "+    print('new')\n"
        " main()\n"
        "*** End of File"
    )
    ops = _parse_patch(patch)
    assert len(ops) == 1
    lines = ops[0]["lines"]
    assert lines[0] == (" ", "def main():")
    assert lines[1] == ("-", "    print('old')")
    assert lines[2] == ("+", "    print('new')")
    assert lines[3] == (" ", "main()")


def test_parse_empty() -> None:
    ops = _parse_patch("")
    assert ops == []


# ── Create file tests ──


@pytest.mark.asyncio
async def test_create_new_file(patch_tool: ApplyPatchTool, tmp_path: Path) -> None:
    patch = (
        "*** Begin of File new.txt\n"
        "+hello\n"
        "+world\n"
        "*** End of File"
    )
    result = await patch_tool.run(patch=patch)
    assert "CREATE" in result
    assert "new.txt" in result
    content = (tmp_path / "new.txt").read_text()
    assert "hello" in content
    assert "world" in content


@pytest.mark.asyncio
async def test_create_nested_path(patch_tool: ApplyPatchTool, tmp_path: Path) -> None:
    patch = (
        "*** Begin of File src/utils/helper.py\n"
        "+def help():\n"
        "+    pass\n"
        "*** End of File"
    )
    result = await patch_tool.run(patch=patch)
    assert "CREATE" in result
    assert (tmp_path / "src" / "utils" / "helper.py").exists()


# ── Modify file tests ──


@pytest.mark.asyncio
async def test_modify_existing_file(patch_tool: ApplyPatchTool, tmp_path: Path) -> None:
    (tmp_path / "main.py").write_text("def main():\n    print('old')\nmain()\n")
    # Convention: op char at col 0, rest is literal file content.
    patch = (
        "*** Begin of File main.py\n"
        " def main():\n"
        "-    print('old')\n"
        "+    print('new')\n"
        " main()\n"
        "*** End of File"
    )
    result = await patch_tool.run(patch=patch)
    assert "MODIFY" in result
    content = (tmp_path / "main.py").read_text()
    assert "new" in content
    assert "old" not in content


# ── Delete file tests ──


@pytest.mark.asyncio
async def test_delete_file(patch_tool: ApplyPatchTool, tmp_path: Path) -> None:
    (tmp_path / "delete_me.txt").write_text("content\n")
    patch = (
        "*** Begin of File delete_me.txt\n"
        "-content\n"
        "*** End of File"
    )
    result = await patch_tool.run(patch=patch)
    assert "DELETE" in result
    assert not (tmp_path / "delete_me.txt").exists()


# ── Multi-file patch ──


@pytest.mark.asyncio
async def test_multi_file_patch(patch_tool: ApplyPatchTool, tmp_path: Path) -> None:
    (tmp_path / "existing.txt").write_text("old content\n")
    # Convention: op char at col 0, rest is literal content (no extra space).
    patch = (
        "*** Begin of File new_file.txt\n"
        "+brand new\n"
        "*** End of File\n"
        "*** Begin of File existing.txt\n"
        "-old content\n"
        "+updated content\n"
        "*** End of File"
    )
    result = await patch_tool.run(patch=patch)
    assert "CREATE" in result
    assert "MODIFY" in result
    assert (tmp_path / "new_file.txt").read_text().strip() == "brand new"
    assert "updated" in (tmp_path / "existing.txt").read_text()


# ── Error cases ──


@pytest.mark.asyncio
async def test_empty_patch(patch_tool: ApplyPatchTool) -> None:
    result = await patch_tool.run(patch="")
    assert "Error" in result


@pytest.mark.asyncio
async def test_no_blocks(patch_tool: ApplyPatchTool) -> None:
    result = await patch_tool.run(patch="just some random text")
    assert "Error" in result


@pytest.mark.asyncio
async def test_patch_mismatch(patch_tool: ApplyPatchTool, tmp_path: Path) -> None:
    (tmp_path / "f.txt").write_text("actual content\n")
    patch = (
        "*** Begin of File f.txt\n"
        " wrong context line\n"
        "-does not match\n"
        "+replacement\n"
        "*** End of File"
    )
    result = await patch_tool.run(patch=patch)
    assert "ERROR" in result
