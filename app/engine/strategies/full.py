from app.parsers.base_parser import ParsedSession
from app.engine.extractors import extract_state


def generate(session: ParsedSession) -> str:
    """
    Full Context Strategy

    Goal:
    Produce a complete project/session handoff.
    """

    state = extract_state(session)

    sections = []

    # --------------------------------------------------
    # Header
    # --------------------------------------------------

    sections.append(
        f"# Session Continuation Context\n"
        f"Platform : {session.source_platform.title()}\n"
        f"Messages : {session.message_count}\n"
        f"Title    : {session.title or 'Untitled'}"
    )

    # --------------------------------------------------
    # Topic
    # --------------------------------------------------

    if state["topic"]:
        sections.append(
            "## Primary Topic\n"
            f"{state['topic']}"
        )

    # --------------------------------------------------
    # Goal
    # --------------------------------------------------

    if state["goal"]:
        sections.append(
            "## Goal\n"
            f"{state['goal']}"
        )

    # --------------------------------------------------
    # Key Information
    # --------------------------------------------------

    if state["key_points"]:
        lines = ["## Key Information"]

        for point in state["key_points"]:
            lines.append(f"- {point}")

        sections.append("\n".join(lines))

    # --------------------------------------------------
    # Current Progress
    # --------------------------------------------------

    if state["current_progress"]:
        lines = ["## Current Progress"]

        for item in state["current_progress"]:
            lines.append(f"- {item}")

        sections.append("\n".join(lines))

    # --------------------------------------------------
    # Resolutions
    # --------------------------------------------------

    if state["resolutions"]:
        lines = ["## Resolutions and Findings"]

        for item in state["resolutions"]:
            lines.append(f"- {item}")

        sections.append("\n".join(lines))

    # --------------------------------------------------
    # Current State
    # --------------------------------------------------

    if state["latest_user_message"]:
        sections.append(
            "## Current State\n"
            "The latest user focus is:\n\n"
            f"{state['latest_user_message']}"
        )

    # --------------------------------------------------
    # Open Questions
    # --------------------------------------------------

    if state["open_questions"]:
        lines = ["## Open Questions"]

        for question in state["open_questions"]:
            lines.append(f"- {question}")

        sections.append("\n".join(lines))

    # --------------------------------------------------
    # Next Tasks
    # --------------------------------------------------

    if state["next_tasks"]:
        lines = ["## Next Tasks"]

        for task in state["next_tasks"]:
            lines.append(f"- {task}")

        sections.append("\n".join(lines))

    # --------------------------------------------------
    # Most Recent Exchange
    # --------------------------------------------------

    if (
        state["latest_user_message"]
        and state["latest_assistant_message"]
    ):
        sections.append(
            "## Most Recent Exchange\n\n"
            f"User:\n{state['latest_user_message']}\n\n"
            f"Assistant:\n{state['latest_assistant_message']}"
        )

    # --------------------------------------------------
    # Continuation Guidance
    # --------------------------------------------------

    sections.append(
        "## Continuation Guidance\n"
        "Continue from the current state while preserving "
        "the objectives, decisions, findings, progress, "
        "and next tasks captured above."
    )

    return "\n\n".join(sections)