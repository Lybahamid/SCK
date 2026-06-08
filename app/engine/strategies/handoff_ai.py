from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional
import subprocess

from app.parsers.base_parser import ParsedSession
from app.engine.extractors import extract_state
from app.engine.llm import generate_with_gemini


def generate(
    session: ParsedSession,
    metadata: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Project Handoff AI Strategy

    Produces a rich project continuation document.
    This version also auto-collects local repo/git metadata
    so the handoff can include real development status.

    Optional metadata can be passed in later from the backend
    or frontend to override or enrich the automatically collected
    repository information.
    """

    state = extract_state(session)
    auto_repo_metadata = _collect_repo_metadata()
    combined_metadata = _merge_metadata(auto_repo_metadata, metadata)

    transcript = _build_transcript(session)

    prompt = _build_prompt(
        session=session,
        state=state,
        repo_metadata=combined_metadata,
        transcript=transcript,
    )

    ai_output = generate_with_gemini(prompt)

    if not ai_output:
        return _fallback_output(session, state, combined_metadata)

    return ai_output


# ==================================================
# Prompt Construction
# ==================================================

def _build_prompt(
    session: ParsedSession,
    state: dict,
    repo_metadata: Dict[str, Any],
    transcript: str,
) -> str:
    return f"""
You are SCK (Session Context Keeper).

Your task is to transform the conversation into a rich project handoff document
that can be pasted into a new AI session so work can continue seamlessly.

This is NOT a transcript summary.
This is NOT a dialogue recap.
This is a project continuation handoff.

Write in Markdown only.

Rules:
- Use clear section headings.
- Preserve concrete facts, decisions, milestones, blockers, and next actions.
- Do not invent details that are not supported by the conversation.
- If a section is not explicitly available, write "Not explicitly stated."
- Prefer project-level continuity over message-by-message narration.
- Keep the document detailed and useful for another AI model.
- Mention technologies, architecture, milestones, blockers, PR status, and next steps when relevant.
- If useful, include a compact status snapshot that makes the project state easy to understand quickly.
- Use the repository metadata below when relevant, especially for Git / PR State.

Use this exact structure:

# SCK Project Continuation Context

## Project Overview
A concise but detailed description of what the project is and why it exists.

## Team Structure
Who is responsible for what, if mentioned in the conversation.
If not available, write "Not explicitly stated."

## Original Product Vision
What the project was originally meant to be or how the user originally imagined it.

## Current Architecture
Describe the current stack, key components, and system design.

## Major Milestones Completed
List the important completed items, resolved issues, and finished integrations.

## Project Status Snapshot
A compact summary of where the project stands right now.

## Current State
Summarize the present focus and where the project currently stands.

## Risks / Blockers
List unresolved issues, constraints, or concerns.

## Git / PR State
Summarize relevant branch, PR, merge, commit, and working tree status.

## Open Questions
List any unresolved questions or decisions.

## Next Steps
Provide a practical list of what should happen next.

## Continuation Prompt
Write a short instruction for the next AI session explaining how to continue.

Conversation Metadata:
- Platform: {session.source_platform}
- Title: {session.title or "Untitled"}
- Messages: {session.message_count}

Repository Metadata:
- Git Branch: {repo_metadata.get("git_branch", "Not explicitly stated.")}
- Git Commit: {repo_metadata.get("git_commit", "Not explicitly stated.")}
- Git Status: {repo_metadata.get("git_status", "Not explicitly stated.")}
- Last Commit Message: {repo_metadata.get("last_commit_message", "Not explicitly stated.")}
- Remote Tracking: {repo_metadata.get("remote_tracking", "Not explicitly stated.")}
- PR Title: {repo_metadata.get("pr_title", "Not explicitly stated.")}
- PR Status: {repo_metadata.get("pr_status", "Not explicitly stated.")}
- Test Summary: {repo_metadata.get("test_summary", "Not explicitly stated.")}

Extracted Hints:
- Topic: {state.get("topic", "")}
- Goal: {state.get("goal", "")}
- Key Points: {state.get("key_points", [])}
- Resolutions: {state.get("resolutions", [])}
- Current Progress: {state.get("current_progress", [])}
- Milestones: {state.get("milestones", [])}
- Blockers: {state.get("blockers", [])}
- Project Status: {state.get("project_status", [])}
- Git State: {state.get("git_state", [])}
- Completed Artifacts: {state.get("completed_artifacts", [])}
- Next Tasks: {state.get("next_tasks", [])}
- Open Questions: {state.get("open_questions", [])}
- Latest User Message: {state.get("latest_user_message", "")}
- Latest Assistant Message: {state.get("latest_assistant_message", "")}

Full Conversation Transcript:
{transcript}
""".strip()


# ==================================================
# Transcript
# ==================================================

def _build_transcript(session: ParsedSession) -> str:
    lines = []

    for msg in session.messages:
        role = msg.role.capitalize()
        content = msg.content.strip()
        lines.append(f"{role}: {content}")

    return "\n\n".join(lines)


# ==================================================
# Repo Metadata
# ==================================================

def _collect_repo_metadata() -> Dict[str, str]:
    """
    Collects local git metadata automatically from the backend repo.

    This keeps the handoff strategy useful even if no explicit Git/PR
    details were mentioned in the conversation.
    """

    repo_root = Path(__file__).resolve().parents[3]

    metadata = {
        "git_branch": _git_command(repo_root, ["branch", "--show-current"]),
        "git_commit": _git_command(repo_root, ["rev-parse", "--short", "HEAD"]),
        "git_status": _git_command(repo_root, ["status", "--short", "--branch"]),
        "last_commit_message": _git_command(
            repo_root,
            ["log", "-1", "--pretty=%s"],
        ),
        "remote_tracking": _git_command(
            repo_root,
            ["branch", "-vv"],
        ),
    }

    # Clean up blank values
    return {
        key: value for key, value in metadata.items() if value
    }


def _git_command(repo_root: Path, args: list[str]) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_root), *args],
            capture_output=True,
            text=True,
            check=False,
        )

        output = (result.stdout or "").strip()
        return output

    except Exception:
        return ""


def _merge_metadata(
    auto_metadata: Dict[str, Any],
    manual_metadata: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Merge auto-collected repo metadata with optional caller-provided metadata.

    Caller-provided values win if keys overlap.
    """

    merged = dict(auto_metadata)

    if manual_metadata:
        for key, value in manual_metadata.items():
            if value is not None and value != "":
                merged[key] = value

    return merged


# ==================================================
# Fallback
# ==================================================

def _fallback_output(
    session: ParsedSession,
    state: dict,
    repo_metadata: Dict[str, Any],
) -> str:
    return (
        "# SCK Project Continuation Context\n\n"
        "Gemini did not return a response.\n\n"
        "## Project Overview\n"
        f"{state.get('topic', 'Not explicitly stated.')}\n\n"
        "## Current State\n"
        f"{state.get('latest_user_message', 'Not explicitly stated.')}\n\n"
        "## Git / PR State\n"
        f"- Git Branch: {repo_metadata.get('git_branch', 'Not explicitly stated.')}\n"
        f"- Git Commit: {repo_metadata.get('git_commit', 'Not explicitly stated.')}\n"
        f"- Git Status: {repo_metadata.get('git_status', 'Not explicitly stated.')}\n"
        f"- Last Commit Message: {repo_metadata.get('last_commit_message', 'Not explicitly stated.')}\n\n"
        "## Continuation Prompt\n"
        "Continue the project from the current focus using the available context."
    )