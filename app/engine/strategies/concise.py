from app.parsers.base_parser import ParsedSession


def generate(session: ParsedSession) -> str:
    """
    Concise context strategy.
    Generates a short and direct context brief.
    Best for simple conversations or quick continuation.
    """

    messages = session.messages
    user_messages = [m for m in messages if m.role == "user"]
    assistant_messages = [m for m in messages if m.role == "assistant"]

    sections = []

    # Header
    sections.append(
        f"# Quick Context Brief\n"
        f"Platform : {session.source_platform.title()}\n"
    )

    # Topic from first user message
    if user_messages:
        sections.append(
            f"## Topic\n"
            f"{_truncate(user_messages[0].content, 200)}"
        )

    # Last user message
    if len(user_messages) > 1:
        sections.append(
            f"## Last Request\n"
            f"{_truncate(user_messages[-1].content, 300)}"
        )

    # Last assistant response
    if assistant_messages:
        sections.append(
            f"## Last Response\n"
            f"{_truncate(assistant_messages[-1].content, 400)}"
        )

    # Continuation
    sections.append(
        "---\n"
        "Please continue from where we left off."
    )

    return "\n\n".join(sections)


def _truncate(text: str, max_length: int) -> str:
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."