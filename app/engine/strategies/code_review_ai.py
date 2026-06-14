"""
Code review-focused context generation strategy.

Specializes in extracting code review sessions, highlighting
reviewable code, feedback given, outstanding comments, and
next review steps.

Use case: User is in a code review discussion and wants to
continue the review in a fresh session.
"""

from app.parsers.base_parser import ParsedSession
from app.engine.extractors import extract_state
from app.engine.llm import generate_with_gemini


def generate(session: ParsedSession) -> str:
    """
    Code Review AI Context Strategy

    Optimized for code review conversations.
    Uses rule-based extraction + Gemini to produce
    code review-focused continuation context.
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

Your job is to generate a code review-focused continuation context
for an AI conversation about reviewing code.
The output will be pasted into a new ChatGPT, Claude, or Gemini
session so the code review can continue without loss of context.

Follow these rules:

- Output Markdown only.
- Do not include any introductory text.
- Do not include closing remarks.
- Do not invent information that is not in the transcript.
- Be concise but informative.
- Preserve exact code snippets and formatting.
- Extract feedback given, feedback received, and outstanding comments.

Use this exact section structure:

# Code Review Session Continuation Context

## Code Overview
What code is being reviewed?
File names, modules, or scope.
Number of lines or components involved.

## Architecture & Design
Key architectural decisions discussed.
Design patterns or principles applied.
Trade-offs or alternatives discussed.

## Code Snippets
Important code sections being reviewed.
Problematic areas identified.
Well-implemented sections praised.

## Feedback Summary
Feedback already given by reviewer(s).
Feedback received from author(s).
Questions asked or clarifications needed.

## Outstanding Review Items
Comments not yet addressed.
Items awaiting response from author.
Ambiguous feedback needing clarification.

## Recommendations
Suggested changes or improvements.
Approval readiness assessment.
Next review steps.

## Continuation Guidance
Brief instruction for the next AI on how to continue the code review
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
- Resolutions: {state.get("resolutions", [])}
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
        "# Code Review Session Continuation Context\n\n"
        "Gemini did not return a response.\n\n"
        f"Code being reviewed: {state.get('topic', '')}\n\n"
        f"Latest reviewer comment: "
        f"{state.get('latest_user_message', '')}"
    )