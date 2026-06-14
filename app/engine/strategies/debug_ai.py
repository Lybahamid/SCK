"""
Debug-focused context generation strategy.

Specializes in extracting debugging sessions, error traces,
attempted solutions, and next diagnostic steps.

Use case: User is debugging a problem and wants to continue
the debugging session with a fresh AI instance.
"""

from app.parsers.base_parser import ParsedSession
from app.engine.extractors import extract_state
from app.engine.llm import generate_with_gemini


def generate(session: ParsedSession) -> str:
    """
    Debug AI Context Strategy

    Optimized for debugging conversations.
    Uses rule-based extraction + Gemini to produce
    debugging-focused continuation context.
    """

    state = extract_state(session)

    transcript = _build_transcript(session)

    prompt = _build_prompt(
        session=session,
        state=state,
        transcript=transcript,
    )

    ai_output = generate_with_gemini(prompt)

    if not ai_output:
        return _fallback_output(session, state)

    return ai_output


# ==================================================
# Prompt Construction
# ==================================================

def _build_prompt(
    session: ParsedSession,
    state: dict,
    transcript: str,
) -> str:

    return f"""
You are SCK (Session Context Keeper).

Your job is to generate a debugging-focused continuation context
for an AI conversation about troubleshooting a problem.
The output will be pasted into a new ChatGPT, Claude, or Gemini
session so the debugging can continue without loss of context.

Follow these rules:

- Output Markdown only.
- Do not include any introductory text.
- Do not include closing remarks.
- Do not invent information that is not in the transcript.
- Be concise but informative.
- Preserve error messages, stack traces, and reproduction steps.
- Extract what has been tried and why it didn't work.

Use this exact section structure:

# Debugging Session Continuation Context

## Problem Statement
1-2 sentence description of what is being debugged.

## Error Signature
The exact error message(s) and/or exception type(s).
Include stack traces if provided.

## Reproduction Steps
How to reproduce the error.
Prerequisites or setup needed.

## What Has Been Tried
Solutions or approaches already attempted.
Why each approach didn't work or what was learned.

## Current Blocker
What is the current error or blocker?
What was the last action taken?
Any new observations?

## Next Diagnostic Steps
What to try next.
Tools or techniques to consider.
Alternative approaches to investigate.

## Continuation Guidance
Brief instruction for the next AI on how to continue debugging
from where this session ended.

---

Conversation Metadata:

- Platform: {session.source_platform}
- Title: {session.title or "Untitled"}
- Messages: {session.message_count}

Extracted Hints:

- Topic: {state.get("topic", "")}
- Goal: {state.get("goal", "")}
- Key Points: {state.get("key_points", [])}
- Open Questions: {state.get("open_questions", [])}
- Next Tasks: {state.get("next_tasks", [])}
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
# Fallback
# ==================================================

def _fallback_output(
    session: ParsedSession,
    state: dict,
) -> str:

    return (
        "# Debugging Session Continuation Context\n\n"
        "Gemini did not return a response.\n\n"
        f"Problem: {state.get('topic', '')}\n\n"
        f"Latest user message: "
        f"{state.get('latest_user_message', '')}"
    )