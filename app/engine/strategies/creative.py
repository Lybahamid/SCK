from app.parsers.base_parser import ParsedSession
from typing import List


def generate(session: ParsedSession) -> str:
    """
    Creative context strategy.
    Optimized for writing, brainstorming, and creative work.
    Focuses on tone, style, characters, and narrative decisions.
    """

    messages = session.messages
    user_messages = [m for m in messages if m.role == "user"]
    assistant_messages = [m for m in messages if m.role == "assistant"]

    sections = []

    # Header
    sections.append(
        f"# Creative Context\n"
        f"Platform : {session.source_platform.title()}\n"
    )

    # Project description
    if user_messages:
        sections.append(
            f"## Project Description\n"
            f"{_truncate(user_messages[0].content, 400)}"
        )

    # Creative decisions and directions
    decisions = _extract_decisions(messages)
    if decisions:
        decision_lines = ["## Creative Decisions Made"]
        for i, decision in enumerate(decisions):
            decision_lines.append(f"{i + 1}. {decision}")
        sections.append("\n".join(decision_lines))

    # Latest creative output
    if assistant_messages:
        latest_output = assistant_messages[-1].content
        sections.append(
            f"## Latest Output\n"
            f"{_truncate(latest_output, 800)}"
        )

    # Current direction from last user message
    if len(user_messages) > 1:
        sections.append(
            f"## Current Direction\n"
            f"{_truncate(user_messages[-1].content, 300)}"
        )

    # Style notes
    style_notes = _extract_style_notes(messages)
    if style_notes:
        style_lines = ["## Style and Tone Notes"]
        for note in style_notes:
            style_lines.append(f"- {note}")
        sections.append("\n".join(style_lines))

    # Continuation
    sections.append(
        "---\n"
        "Please continue the creative work maintaining the same "
        "tone, style, and direction established above."
    )

    return "\n\n".join(sections)


def _extract_decisions(messages) -> List[str]:
    decision_keywords = [
        "let's", "we'll", "decided", "going with",
        "the character", "the story", "the tone",
        "the style", "make it", "keep it",
    ]
    decisions = []
    for msg in messages:
        for sentence in msg.content.split("."):
            sentence = sentence.strip()
            sentence_lower = sentence.lower()
            if any(kw in sentence_lower for kw in decision_keywords):
                if len(sentence) > 15:
                    decisions.append(sentence)
    return list(dict.fromkeys(decisions))[:6]


def _extract_style_notes(messages) -> List[str]:
    style_keywords = [
        "tone", "style", "voice", "formal",
        "casual", "humorous", "serious", "poetic",
        "concise", "detailed", "dark", "light",
    ]
    notes = []
    for msg in messages:
        for sentence in msg.content.split("."):
            sentence = sentence.strip()
            sentence_lower = sentence.lower()
            if any(kw in sentence_lower for kw in style_keywords):
                if len(sentence) > 10:
                    notes.append(sentence)
    return list(dict.fromkeys(notes))[:5]


def _truncate(text: str, max_length: int) -> str:
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."