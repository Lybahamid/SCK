"""
Documentation-focused context generation strategy.

Specializes in extracting documentation writing sessions,
highlighting covered sections, outstanding sections,
writing style/guidelines, and next sections to document.

Use case: User is writing documentation and wants to continue
in a fresh session without losing progress or tone.
"""

from app.parsers.base_parser import ParsedSession
from app.engine.extractors import extract_state
from app.engine.llm import generate_with_gemini


def generate(session: ParsedSession) -> str:
    """
    Documentation AI Context Strategy

    Optimized for documentation writing conversations.
    Uses rule-based extraction + Gemini to produce
    documentation-focused continuation context.
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

Your job is to generate a documentation-focused continuation context
for an AI conversation about writing documentation.
The output will be pasted into a new ChatGPT, Claude, or Gemini
session so the documentation writing can continue without loss of context.

Follow these rules:

- Output Markdown only.
- Do not include any introductory text.
- Do not include closing remarks.
- Do not invent information that is not in the transcript.
- Be concise but informative.
- Preserve writing style, tone, and formatting guidelines.
- Extract what sections are done, what's pending, and style consistency rules.

Use this exact section structure:

# Documentation Writing Session Continuation Context

## Documentation Overview
What is being documented?
Target audience and documentation type (API docs, guide, tutorial, etc.).

## Completed Sections
What sections have already been written?
Brief summary of each completed section.
Status indicator (draft, reviewed, final).

## Outstanding Sections
What sections still need to be written?
Priority order for writing.
Estimated scope for each section.

## Writing Style & Tone
Formal or casual tone?
Technical depth level expected.
Code examples - how many and what scope?
Specific terminology or abbreviations to use.

## Consistency Guidelines
Formatting standards (headings, lists, code blocks).
Cross-reference and linking style.
Abbreviations and terminology consistency.
Any brand or project-specific guidelines.

## Content Guidelines
Should sections include examples? How many?
Level of detail expected per section.
Common pitfalls or anti-patterns to avoid.
Assumed reader knowledge level.

## Next Documentation Steps
Which section to write next?
Recommended approach or structure.
Content that depends on other sections.
Estimated effort for completion.

## Continuation Guidance
Brief instruction for the next AI on how to continue the documentation
from where this session ended while maintaining consistency.

---

Conversation Metadata:

- Platform: {session.source_platform}
- Title: {session.title or "Untitled"}
- Messages: {session.message_count}

Extracted Hints:

- Topic: {state.get("topic", "")}
- Goal: {state.get("goal", "")}
- Key Points: {state.get("key_points", [])}
- Current Progress: {state.get("current_progress", [])}
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
        "# Documentation Writing Session Continuation Context\n\n"
        "Gemini did not return a response.\n\n"
        f"Documentation: {state.get('topic', '')}\n\n"
        f"Latest user message: "
        f"{state.get('latest_user_message', '')}"
    )