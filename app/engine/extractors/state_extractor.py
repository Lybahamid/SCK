from typing import List

from app.parsers.base_parser import ParsedSession


def extract_state(session: ParsedSession) -> dict:
    """
    Extract reusable conversation state for all strategies.

    This version adds higher-level project signals so the AI can
    generate richer handoff documents:
    - milestones
    - blockers
    - project status
    - git / PR state
    - completed artifacts
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

    all_messages = [
        m.content.strip()
        for m in session.messages
    ]

    return {
        "topic": _extract_topic(user_messages),
        "goal": _extract_goal(user_messages),
        "key_points": _extract_key_points(user_messages),
        "open_questions": _extract_questions(user_messages),
        "resolutions": _extract_resolutions(session),
        "current_progress": _extract_progress(all_messages),
        "milestones": _extract_milestones(all_messages),
        "blockers": _extract_blockers(all_messages),
        "project_status": _extract_project_status(all_messages),
        "git_state": _extract_git_state(all_messages),
        "completed_artifacts": _extract_completed_artifacts(all_messages),
        "next_tasks": _extract_next_tasks(user_messages),
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
        "verified",
        "passed",
        "migrated",
        "functional",
        "operational",
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
    messages: List[str]
) -> List[str]:

    patterns = [
        "built",
        "implemented",
        "completed",
        "using",
        "created",
        "integrated",
        "finished",
        "working",
        "ready",
        "functional",
        "operational",
        "set up",
        "verified",
        "migrated",
    ]

    progress = []

    for msg in messages:
        lower = msg.lower()

        if any(k in lower for k in patterns):
            if msg not in progress:
                progress.append(msg)

    return progress[:10]


# ==================================================
# Milestones
# ==================================================

def _extract_milestones(
    messages: List[str]
) -> List[str]:

    patterns = [
        "completed",
        "implemented",
        "resolved",
        "verified",
        "passed",
        "migrated",
        "integrated",
        "functional",
        "operational",
        "finished",
        "done",
        "launched",
        "shipped",
    ]

    milestones = []

    for msg in messages:
        lower = msg.lower()

        if any(k in lower for k in patterns):
            if msg not in milestones:
                milestones.append(msg)

    return milestones[:10]


# ==================================================
# Blockers
# ==================================================

def _extract_blockers(
    messages: List[str]
) -> List[str]:

    patterns = [
        "blocker",
        "blocked",
        "issue",
        "problem",
        "bug",
        "error",
        "failed",
        "failure",
        "concern",
        "risk",
        "unresolved",
        "pending",
        "waiting",
        "not working",
        "missing",
        "limitation",
        "afraid",
        "worried",
    ]

    blockers = []

    for msg in messages:
        lower = msg.lower()

        if any(k in lower for k in patterns):
            if msg not in blockers:
                blockers.append(msg)

    return blockers[:10]


# ==================================================
# Project Status
# ==================================================

def _extract_project_status(
    messages: List[str]
) -> List[str]:

    patterns = [
        "stable",
        "ready",
        "awaiting",
        "focus",
        "current state",
        "current focus",
        "working on",
        "operational",
        "pending",
        "complete",
        "completed",
        "functional",
        "evolving",
        "next step",
        "next milestone",
    ]

    status = []

    for msg in messages:
        lower = msg.lower()

        if any(k in lower for k in patterns):
            if msg not in status:
                status.append(msg)

    return status[:10]


# ==================================================
# Git / PR State
# ==================================================

def _extract_git_state(
    messages: List[str]
) -> List[str]:

    patterns = [
        "git",
        "branch",
        "pr",
        "pull request",
        "merge",
        "conflict",
        "commit",
        "push",
        "origin",
        "checkout",
        "main",
        "head",
        "remote",
        "feature/",
    ]

    git_items = []

    for msg in messages:
        lower = msg.lower()

        if any(k in lower for k in patterns):
            if msg not in git_items:
                git_items.append(msg)

    return git_items[:10]


# ==================================================
# Completed Artifacts
# ==================================================

def _extract_completed_artifacts(
    messages: List[str]
) -> List[str]:

    artifact_keywords = [
        "backend",
        "parser",
        "engine",
        "api",
        "extension",
        "frontend",
        "migration",
        "model",
        "service",
        "test",
        "gemini",
        "streamlit",
        "react",
        "database",
        "persistence",
        "strategy",
    ]

    completion_keywords = [
        "completed",
        "implemented",
        "added",
        "integrated",
        "resolved",
        "migrated",
        "verified",
        "functional",
        "working",
        "passed",
        "set up",
    ]

    artifacts = []

    for msg in messages:
        lower = msg.lower()

        if any(a in lower for a in artifact_keywords) and any(
            c in lower for c in completion_keywords
        ):
            if msg not in artifacts:
                artifacts.append(msg)

    return artifacts[:10]


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
        "should",
        "have to",
        "must",
        "still need",
        "pending",
        "want to",
    ]

    tasks = []

    for msg in user_messages:
        lower = msg.lower()

        if any(p in lower for p in patterns):
            if msg not in tasks:
                tasks.append(msg)

    return tasks[:10]