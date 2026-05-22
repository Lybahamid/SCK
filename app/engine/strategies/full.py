from app.parsers.base_parser import ParsedSession
from typing import List


def generate(session: ParsedSession) -> str:
    """
    Full context strategy.
    Generates a comprehensive structured context document.
    Best for complex multi-topic conversations.
    """

    messages = session.messages
    user_messages = [m for m in messages if m.role == "user"]
    assistant_messages = [m for m in messages if m.role == "assistant"]

    # Build conversation timeline
    pairs = _pair_messages(messages)

    sections = []

    # Header
    sections.append(
        f"# Session Context\n"
        f"Platform : {session.source_platform.title()}\n"
        f"Messages : {session.message_count}\n"
        f"Title    : {session.title or 'Untitled'}\n"
    )

    # Topic
    if user_messages:
        first_message = user_messages[0].content
        sections.append(
            f"## Topic\n"
            f"{_truncate(first_message, 300)}\n"
        )

    # Full conversation timeline
    if pairs:
        timeline_lines = ["## Conversation Summary"]
        for i, pair in enumerate(pairs):
            timeline_lines.append(
                f"\n### Exchange {i + 1}"
            )
            timeline_lines.append(
                f"**User:**\n{_truncate(pair['user'], 400)}"
            )
            timeline_lines.append(
                f"**Assistant:**\n{_truncate(pair['assistant'], 600)}"
            )
        sections.append("\n".join(timeline_lines))

    # Current state
    if pairs:
        last_pair = pairs[-1]
        sections.append(
            f"## Current State\n"
            f"The last exchange was:\n\n"
            f"User asked:\n{_truncate(last_pair['user'], 400)}\n\n"
            f"Assistant responded:\n{_truncate(last_pair['assistant'], 600)}\n"
        )

    # Open questions from user
    questions = _extract_questions(user_messages)
    if questions:
        question_lines = ["## Open Questions"]
        for i, q in enumerate(questions):
            question_lines.append(f"{i + 1}. {q}")
        sections.append("\n".join(question_lines))

    # Code blocks
    code_blocks = _extract_code_blocks(messages)
    if code_blocks:
        code_lines = ["## Code References"]
        for i, block in enumerate(code_blocks):
            code_lines.append(f"\n### Snippet {i + 1}")
            code_lines.append(f"```\n{block}\n```")
        sections.append("\n".join(code_lines))

    # Continuation instruction
    sections.append(
        "---\n"
        "Please review the above context and continue "
        "the conversation from where it left off."
    )

    return "\n\n".join(sections)


def _pair_messages(messages) -> List[dict]:
    pairs = []
    for i in range(len(messages) - 1):
        if (
            messages[i].role == "user"
            and messages[i + 1].role == "assistant"
        ):
            pairs.append({
                "user": messages[i].content,
                "assistant": messages[i + 1].content,
            })
    return pairs


def _extract_questions(user_messages) -> List[str]:
    questions = []
    for msg in user_messages:
        sentences = msg.content.split(".")
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence.endswith("?") and len(sentence) > 10:
                questions.append(sentence)
    return questions[:5]


def _extract_code_blocks(messages) -> List[str]:
    code_blocks = []
    for msg in messages:
        content = msg.content
        in_block = False
        current_block = []
        for line in content.splitlines():
            if line.strip().startswith("```"):
                if in_block:
                    if current_block:
                        code_blocks.append("\n".join(current_block))
                    current_block = []
                    in_block = False
                else:
                    in_block = True
            elif in_block:
                current_block.append(line)
    return code_blocks[:3]


def _truncate(text: str, max_length: int) -> str:
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."