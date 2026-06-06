from app.parsers.base_parser import ParsedSession
from typing import List


def generate(session: ParsedSession) -> str:
    """
    Technical Context Strategy V2

    Focus:
    - Problems
    - Errors
    - Resolutions
    - Current State
    - Next Work Item

    Designed for:
    - Coding sessions
    - Debugging
    - Architecture discussions
    """

    messages = session.messages

    user_messages = [
        m.content.strip()
        for m in messages
        if m.role == "user"
    ]

    assistant_messages = [
        m.content.strip()
        for m in messages
        if m.role == "assistant"
    ]

    sections = []

    # -----------------------------------------
    # Header
    # -----------------------------------------

    sections.append(
        f"# Technical Continuation Context\n"
        f"Platform : {session.source_platform.title()}\n"
        f"Messages : {session.message_count}"
    )

    # -----------------------------------------
    # Problem
    # -----------------------------------------

    if user_messages:
        sections.append(
            "## Problem Statement\n"
            f"{_truncate(user_messages[0], 500)}"
        )

    # -----------------------------------------
    # Errors
    # -----------------------------------------

    errors = _extract_errors(messages)

    if errors:
        lines = ["## Errors Encountered"]

        for err in errors:
            lines.append(f"- {err}")

        sections.append("\n".join(lines))

    # -----------------------------------------
    # Technical Components
    # -----------------------------------------

    components = _extract_components(messages)

    if components:
        lines = ["## Relevant Components"]

        for component in components:
            lines.append(f"- {component}")

        sections.append("\n".join(lines))

    # -----------------------------------------
    # Resolutions
    # -----------------------------------------

    resolutions = _extract_resolutions(messages)

    if resolutions:
        lines = ["## Resolutions and Findings"]

        for item in resolutions:
            lines.append(f"- {item}")

        sections.append("\n".join(lines))

    # -----------------------------------------
    # Code Blocks
    # -----------------------------------------

    code_blocks = _extract_code_blocks(messages)

    if code_blocks:
        lines = ["## Referenced Code"]

        for i, block in enumerate(code_blocks):
            lines.append(
                f"\n### Snippet {i + 1}"
            )

            lines.append(
                f"```\n{block}\n```"
            )

        sections.append("\n".join(lines))

    # -----------------------------------------
    # Current State
    # -----------------------------------------

    current_state = _current_state(messages)

    if current_state:
        sections.append(
            "## Current State\n"
            f"{current_state}"
        )

    # -----------------------------------------
    # Next Task
    # -----------------------------------------

    next_task = _next_task(messages)

    if next_task:
        sections.append(
            "## Next Task\n"
            f"{next_task}"
        )

    # -----------------------------------------
    # Continuation Guidance
    # -----------------------------------------

    sections.append(
        "## Continuation Guidance\n"
        "Continue the technical discussion while preserving "
        "the problem history, technical decisions, "
        "resolutions already attempted, and remaining tasks."
    )

    return "\n\n".join(sections)


# ==================================================
# Helpers
# ==================================================

def _extract_errors(messages) -> List[str]:
    keywords = [
        "error",
        "exception",
        "traceback",
        "invalidrequesterror",
        "typeerror",
        "nameerror",
        "valueerror",
        "failed",
    ]

    results = []

    for msg in messages:
        content = msg.content.strip()

        lower = content.lower()

        if any(k in lower for k in keywords):
            results.append(content)

    return list(dict.fromkeys(results))[:8]


def _extract_components(messages) -> List[str]:
    keywords = [
        "model",
        "models",
        "service",
        "services",
        "api",
        "database",
        "session",
        "message",
        "context",
        "sqlalchemy",
        "fastapi",
        "migration",
        "alembic",
    ]

    components = []

    for msg in messages:
        content = msg.content.strip()

        lower = content.lower()

        if any(k in lower for k in keywords):
            components.append(content)

    return list(dict.fromkeys(components))[:10]


def _extract_resolutions(messages) -> List[str]:
    keywords = [
        "fixed",
        "resolved",
        "working",
        "that fixed",
        "implemented",
        "completed",
        "added",
    ]

    resolutions = []

    for msg in messages:
        content = msg.content.strip()

        lower = content.lower()

        if any(k in lower for k in keywords):
            resolutions.append(content)

    return list(dict.fromkeys(resolutions))[:8]


def _current_state(messages) -> str:
    user_messages = [
        m.content.strip()
        for m in messages
        if m.role == "user"
    ]

    if not user_messages:
        return ""

    return (
        "The discussion is currently focused on:\n\n"
        f"{user_messages[-1]}"
    )


def _next_task(messages) -> str:
    user_messages = [
        m.content.strip()
        for m in messages
        if m.role == "user"
    ]

    if len(user_messages) < 2:
        return user_messages[-1] if user_messages else ""

    return user_messages[-1]


def _extract_code_blocks(messages) -> List[str]:
    blocks = []

    for msg in messages:
        content = msg.content

        in_block = False
        current = []

        for line in content.splitlines():
            if line.strip().startswith("```"):
                if in_block:
                    if current:
                        blocks.append(
                            "\n".join(current)
                        )
                    current = []
                    in_block = False
                else:
                    in_block = True
            elif in_block:
                current.append(line)

    return blocks[:3]


def _truncate(
    text: str,
    max_length: int,
) -> str:
    if len(text) <= max_length:
        return text

    return text[:max_length] + "..."