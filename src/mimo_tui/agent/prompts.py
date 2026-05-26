from __future__ import annotations

import re
from typing import Literal

SYSTEM_PROMPTS: dict[str, str] = {
    "chat": (
        "You are MiMo, a helpful AI assistant. "
        "Answer questions clearly and concisely."
    ),
    "plan": (
        "You are MiMo, an expert software architect. "
        "When given a task, first create a detailed step-by-step plan before taking any action. "
        "Explain your reasoning, identify risks, and outline the approach. "
        "Do not execute code or modify files without explicit user approval."
    ),
    "agent": (
        "You are MiMo, an autonomous coding agent. "
        "You have access to tools for reading/writing files, running shell commands, and searching code. "
        "Complete tasks by breaking them into steps, using tools as needed. "
        "Always explain what you are doing before taking action. "
        "Use the minimum number of tool calls necessary. "
        "After completing a task, summarize what was done."
    ),
    "yolo": (
        "You are MiMo, an autonomous coding agent in YOLO mode. "
        "Execute tasks directly using available tools without asking for approval. "
        "Be efficient and complete tasks as quickly as possible. "
        "All tool calls are pre-approved."
    ),
}


def get_system_prompt(mode: str) -> str:
    return SYSTEM_PROMPTS.get(mode, SYSTEM_PROMPTS["chat"])


COMPACT_SYSTEM_PROMPT = (
    "You produce structured conversation summaries for context handoff. "
    "Follow the requested output format strictly."
)


# ── Compaction prompts (verbatim from Claude Code source, v2.1.139 / v2.1.38) ──
#
# `COMPACT_PROMPT_FULL` mirrors src/services/compact/prompt.ts in the Claude
# Code source leak (the "partial compaction instructions" template). It is used
# for the user-invoked `/compact` command, where a thorough handoff matters
# more than tokens.
COMPACT_PROMPT_FULL = """Your task is to create a detailed summary of this conversation. This summary will be placed at the start of a continuing session; newer messages that build on this context will follow after your summary (you do not see them here). Summarize thoroughly so that someone reading only your summary and then the newer messages can fully understand what happened and continue the work.

Before providing your final summary, wrap your analysis in <analysis> tags to organize your thoughts and ensure you've covered all necessary points. In your analysis process:

1. Chronologically analyze each message and section of the conversation. For each section thoroughly identify:
   - The user's explicit requests and intents
   - Your approach to addressing the user's requests
   - Key decisions, technical concepts and code patterns
   - Specific details like:
     - file names
     - full code snippets
     - function signatures
     - file edits
   - Errors that you ran into and how you fixed them
   - Pay special attention to specific user feedback that you received, especially if the user told you to do something differently.
   - Note any security-relevant instructions or constraints the user stated (e.g., sensitive files or data to avoid, operations that must not be performed, credential or secret handling rules). These MUST be preserved verbatim in the summary so they continue to apply after compaction.
2. Double-check for technical accuracy and completeness, addressing each required element thoroughly.

Your summary should include the following sections:

1. Primary Request and Intent: Capture the user's explicit requests and intents in detail
2. Key Technical Concepts: List important technical concepts, technologies, and frameworks discussed.
3. Files and Code Sections: Enumerate specific files and code sections examined, modified, or created. Include full code snippets where applicable and include a summary of why this file read or edit is important.
4. Errors and fixes: List errors encountered and how they were fixed.
5. Problem Solving: Document problems solved and any ongoing troubleshooting efforts.
6. All user messages: List ALL user messages that are not tool results. Preserve any security-relevant instructions or constraints verbatim so they remain in effect after compaction.
7. Pending Tasks: Outline any pending tasks.
8. Work Completed: Describe what was accomplished by the end of this portion.
9. Context for Continuing Work: Summarize any context, decisions, or state that would be needed to understand and continue the work in subsequent messages.

Here's an example of how your output should be structured:

<example>
<analysis>
[Your thought process, ensuring all points are covered thoroughly and accurately]
</analysis>

<summary>
1. Primary Request and Intent:
   [Detailed description]

2. Key Technical Concepts:
   - [Concept 1]
   - [Concept 2]

3. Files and Code Sections:
   - [File Name 1]
      - [Summary of why this file is important]
      - [Important Code Snippet]

4. Errors and fixes:
    - [Error description]:
      - [How you fixed it]

5. Problem Solving:
   [Description]

6. All user messages:
    - [Detailed non tool use user message]

7. Pending Tasks:
   - [Task 1]

8. Work Completed:
   [Description of what was accomplished]

9. Context for Continuing Work:
   [Key context, decisions, or state needed to continue the work]

</summary>
</example>

Please provide your summary following this structure, ensuring precision and thoroughness in your response."""


# `COMPACT_PROMPT_LIGHT` mirrors the lighter SDK-side handoff prompt
# (system-prompt-context-compaction-summary.md). Five sections, single
# <summary>…</summary> wrapper. Used for automatic triggers where we want a
# faster, cheaper summary.
COMPACT_PROMPT_LIGHT = """You have been working on the task described above but have not yet completed it. Write a continuation summary that will allow you (or another instance of yourself) to resume work efficiently in a future context window where the conversation history will be replaced with this summary. Your summary should be structured, concise, and actionable. Include:
1. Task Overview
The user's core request and success criteria
Any clarifications or constraints they specified
2. Current State
What has been completed so far
Files created, modified, or analyzed (with paths if relevant)
Key outputs or artifacts produced
3. Important Discoveries
Technical constraints or requirements uncovered
Decisions made and their rationale
Errors encountered and how they were resolved
What approaches were tried that didn't work (and why)
4. Next Steps
Specific actions needed to complete the task
Any blockers or open questions to resolve
Priority order if multiple steps remain
5. Context to Preserve
User preferences or style requirements
Domain-specific details that aren't obvious
Any promises made to the user
Be concise but complete—err on the side of including information that would prevent duplicate work or repeated mistakes. Write in a way that enables immediate resumption of the task.
Wrap your summary in <summary></summary> tags."""


CompactKind = Literal["full", "light"]


def build_compact_user_message(kind: CompactKind, focus: str = "") -> str:
    """Return the user-role instruction to append at the end of history."""
    base = COMPACT_PROMPT_FULL if kind == "full" else COMPACT_PROMPT_LIGHT
    focus = (focus or "").strip()
    if focus:
        return f"Focus areas requested by the user: {focus}\n\n{base}"
    return base


_SUMMARY_TAG_RE = re.compile(r"<summary>(.*?)</summary>", re.DOTALL | re.IGNORECASE)
_ANALYSIS_TAG_RE = re.compile(r"<analysis>.*?</analysis>", re.DOTALL | re.IGNORECASE)


def extract_summary(text: str) -> str:
    """Pull the summary body out of a compaction response.

    Prefers content inside <summary>…</summary>. Falls back to the text with
    any <analysis>…</analysis> block stripped, then to the whole string.
    """
    if not text:
        return ""
    m = _SUMMARY_TAG_RE.search(text)
    if m:
        return m.group(1).strip()
    stripped = _ANALYSIS_TAG_RE.sub("", text).strip()
    return stripped or text.strip()
