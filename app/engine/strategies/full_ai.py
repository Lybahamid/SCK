from app.parsers.base_parser import ParsedSession
from app.engine.extractors import extract_state
from app.engine.llm import generate_with_gemini


def generate(session: ParsedSession) -> str:
    """
    Full AI Context Strategy

    Uses rule-based extraction to build a deterministic
    prompt skeleton, then uses Gemini to produce a
    structured continuation context.
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

Your job is to generate a structured continuation context
for an AI conversation. The output will be pasted into a
new ChatGPT, Claude, or Gemini session so the conversation
can continue without loss of context.

Follow these rules:

- Output Markdown only.
- Do not include any introductory text.
- Do not include closing remarks.
- Do not invent information that is not implied.
- Be concise but informative.
- Preserve technical decisions, project state, and next steps.
- Use the exact section structure provided below.

Use this exact section structure:

# Session Continuation Context

## Project Overview
Short description of what the user is working on.

## Goal
The primary objective of the conversation.

## Current Architecture
List key components, technologies, decisions.

## Progress So Far
What has already been completed, implemented, or resolved.

## Current State
The user's current focus and the present situation.

## Open Questions
Any unanswered questions or ongoing decisions.

## Next Steps
Concrete next actions to take.

## Continuation Prompt
A short instruction telling the next AI how to continue
from where the previous session ended.

---

Conversation Metadata:

- Platform: {session.source_platform}
- Title: {session.title or "Untitled"}
- Messages: {session.message_count}

Extracted Hints:

- Topic: {state.get("topic", "")}
- Goal: {state.get("goal", "")}
- Key Points: {state.get("key_points", [])}
- Resolutions: {state.get("resolutions", [])}
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
# Fallback
# ==================================================

def _fallback_output(
    session: ParsedSession,
    state: dict,
) -> str:

    return (
        "# Session Continuation Context\n\n"
        "Gemini did not return a response.\n\n"
        f"Topic: {state.get('topic', '')}\n\n"
        f"Latest user message: "
        f"{state.get('latest_user_message', '')}"
    )