"""Right sidebar panel — collapsible sections for Plan, Todos, Tasks, Agents."""
from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.reactive import reactive
from textual.widgets import Static


class SidebarSection(Vertical):
    """A single collapsible section in the right sidebar."""

    DEFAULT_CSS = """
    SidebarSection {
        height: auto;
        max-height: 50%;
        border: solid #29a4bd;
        margin: 0;
        padding: 0;
        background: #16213e;
    }
    SidebarSection .sb-section-title {
        height: 1;
        background: #1f2335;
        color: #e0af68;
        text-style: bold;
        padding: 0 1;
    }
    SidebarSection .sb-section-body {
        height: auto;
        max-height: 12;
        padding: 0 1;
        color: #565f89;
    }
    """

    def __init__(self, title: str, empty_text: str = "None") -> None:
        super().__init__()
        self._title = title
        self._empty_text = empty_text
        self._items: list[str] = []

    def compose(self) -> ComposeResult:
        yield Static(self._title, classes="sb-section-title")
        yield Static(self._empty_text, classes="sb-section-body")

    def set_items(self, items: list[str]) -> None:
        self._items = items
        body = self.query_one(".sb-section-body", Static)
        if items:
            body.update("\n".join(items))
        else:
            body.update(self._empty_text)

    def add_item(self, text: str) -> None:
        self._items.append(text)
        body = self.query_one(".sb-section-body", Static)
        body.update("\n".join(self._items))

    def clear_items(self) -> None:
        self._items = []
        body = self.query_one(".sb-section-body", Static)
        body.update(self._empty_text)


class RightSidebar(Vertical):
    """Right sidebar with Plan, Todos, Tasks, Agents sections."""

    DEFAULT_CSS = """
    RightSidebar {
        width: 30;
        border-left: solid #29a4bd;
        background: #1a1b2e;
        padding: 0;
        overflow-y: auto;
    }
    RightSidebar.collapsed {
        width: 0;
        display: none;
    }
    """

    collapsed: reactive[bool] = reactive(False)

    def compose(self) -> ComposeResult:
        yield SidebarSection("Plan", "No active plan")
        yield SidebarSection("Todos", "No todos")
        yield SidebarSection("Tasks", "No tasks")
        yield SidebarSection("Agents", "No agents")

    @property
    def plan_section(self) -> SidebarSection:
        return self.query(SidebarSection)[0]

    @property
    def todos_section(self) -> SidebarSection:
        return self.query(SidebarSection)[1]

    @property
    def tasks_section(self) -> SidebarSection:
        return self.query(SidebarSection)[2]

    @property
    def agents_section(self) -> SidebarSection:
        return self.query(SidebarSection)[3]

    def toggle_collapse(self) -> None:
        if self.collapsed:
            self.remove_class("collapsed")
            self.collapsed = False
        else:
            self.add_class("collapsed")
            self.collapsed = True
