from typing import List

from app.parsers.base_parser import ParsedSession


def extract_state(session: ParsedSession) -> dict:
    """
    Extracts reusable conversation state
    that all strategies can use.
    """

    user_messages = [
        m.content.strip()
        for m in session.messages
        if m.role == "user"
    ]

    assistant_messages = [
        m.content.strip()
        for m in session.messages
        if m.role == "assistant"
    ]

    return {
        "topic": _extract_topic(user_messages),
        "goal": _extract_goal(user_messages),
        "key_points": _extract_key_points(user_messages),
        "open_questions": _extract_questions(user_messages),
        "resolutions": _extract_resolutions(session),
        "next_tasks": _extract_next_tasks(user_messages),
        "current_progress": _extract_progress(user_messages),
        "latest_user_message": (
            user_messages[-1]
            if user_messages
            else ""
        ),
        "latest_assistant_message": (
            assistant_messages[-1]
            if assistant_messages
            else ""
        ),
    }


# ==================================================
# Topic
# ==================================================

def _extract_topic(
    user_messages: List[str]
) -> str:
    if not user_messages:
        return ""

    return user_messages[0]


# ==================================================
# Goal
# ==================================================

def _extract_goal(
    user_messages: List[str]
) -> str:
    """
    The initial user objective usually
    represents the session goal.
    """

    if not user_messages:
        return ""

    return user_messages[0]


# ==================================================
# Key Points
# ==================================================

def _extract_key_points(
    user_messages: List[str]
) -> List[str]:

    points = []

    for msg in user_messages:

        if len(msg) < 20:
            continue

        if msg not in points:
            points.append(msg)

    return points[:10]


# ==================================================
# Questions
# ==================================================

def _extract_questions(
    user_messages: List[str]
) -> List[str]:

    questions = []

    for msg in user_messages:

        if "?" in msg:
            questions.append(msg)

    return questions[:5]


# ==================================================
# Resolutions
# ==================================================

def _extract_resolutions(
    session: ParsedSession
) -> List[str]:

    patterns = [
        "fixed",
        "resolved",
        "working",
        "completed",
        "implemented",
        "added",
        "successful",
    ]

    findings = []

    for msg in session.messages:

        text = msg.content.strip()

        lower = text.lower()

        if any(p in lower for p in patterns):

            if text not in findings:
                findings.append(text)

    return findings[:10]


# ==================================================
# Progress
# ==================================================

def _extract_progress(
    user_messages: List[str]
) -> List[str]:

    keywords = [
        "built",
        "implemented",
        "completed",
        "using",
        "created",
        "integrated",
        "finished",
        "working",
    ]

    progress = []

    for msg in user_messages:

        lower = msg.lower()

        if any(k in lower for k in keywords):

            if msg not in progress:
                progress.append(msg)

    return progress[:8]


# ==================================================
# Next Tasks
# ==================================================

def _extract_next_tasks(
    user_messages: List[str]
) -> List[str]:

    patterns = [
        "need to",
        "now i need",
        "next",
        "remaining",
        "todo",
        "plan to",
        "going to",
    ]

    tasks = []

    for msg in user_messages:

        lower = msg.lower()

        if any(p in lower for p in patterns):

            if msg not in tasks:
                tasks.append(msg)

    return tasks[:10]