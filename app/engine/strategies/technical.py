from app.parsers.base_parser import ParsedSession
from typing import List


def generate(session: ParsedSession) -> str:
    """
    Technical context strategy.
    Prioritizes code blocks, errors, and technical decisions.
    Best for coding and debugging sessions.
    """

    messages = session.messages
    user_messages = [m for m in messages if m.role == "user"]
    assistant_messages = [m for m in messages if m.role == "assistant"]

    sections = []

    # Header
    sections.append(
        f"# Technical Context\n"
        f"Platform : {session.source_platform.title()}\n"
        f"Messages : {session.message_count}\n"
    )

    # Problem statement from first user message
    if user_messages:
        sections.append(
            f"## Problem Statement\n"
            f"{_truncate(user_messages[0].content, 400)}"
        )

    # All code blocks with source
    code_blocks = _extract_code_blocks_with_source(messages)
    if code_blocks:
        code_lines = ["## Code"]
        for block in code_blocks:
            code_lines.append(
                f"\n**Source:** {block['role'].title()}"
            )
            code_lines.append(f"```\n{block['code']}\n```")
        sections.append("\n".join(code_lines))

    # Errors mentioned
    errors = _extract_errors(messages)
    if errors:
        error_lines = ["## Errors Encountered"]
        for i, error in enumerate(errors):
            error_lines.append(f"{i + 1}. {error}")
        sections.append("\n".join(error_lines))

    # Current state
    if assistant_messages:
        sections.append(
            f"## Current State\n"
            f"{_truncate(assistant_messages[-1].content, 600)}"
        )

    # Next task
    if user_messages:
        sections.append(
            f"## Next Task\n"
            f"{_truncate(user_messages[-1].content, 300)}"
        )

    # Continuation
    sections.append(
        "---\n"
        "Please continue the technical work from where we left off.\n"
        "Reference the code and context above."
    )

    return "\n\n".join(sections)


def _extract_code_blocks_with_source(messages) -> List[dict]:
    blocks = []
    for msg in messages:
        in_block = False
        current_block = []
        for line in msg.content.splitlines():
            if line.strip().startswith("```"):
                if in_block:
                    if current_block:
                        blocks.append({
                            "role": msg.role,
                            "code": "\n".join(current_block),
                        })
                    current_block = []
                    in_block = False
                else:
                    in_block = True
            elif in_block:
                current_block.append(line)
    return blocks


def _extract_errors(messages) -> List[str]:
    error_keywords = [
        "error", "exception", "traceback",
        "failed", "undefined", "typeerror",
        "syntaxerror", "nameerror", "valueerror",
    ]
    errors = []
    for msg in messages:
        for line in msg.content.splitlines():
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in error_keywords):
                cleaned = line.strip()
                if cleaned and len(cleaned) > 10:
                    errors.append(cleaned)
    return list(dict.fromkeys(errors))[:5]


def _truncate(text: str, max_length: int) -> str:
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."