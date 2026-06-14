"""
Design/Architecture-focused context generation strategy.

Specializes in extracting design discussions, architectural
decisions made, trade-offs considered, alternatives evaluated,
and remaining design questions.

Use case: User is discussing system design and wants to continue
the design session in a fresh conversation.
"""

from app.parsers.base_parser import ParsedSession
from app.engine.extractors import extract_state
from app.engine.llm import generate_with_gemini


def generate(session: ParsedSession) -> str:
    """
    Design AI Context Strategy

    Optimized for design/architecture conversations.
    Uses rule-based extraction + Gemini to produce
    design-focused continuation context.
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

Your job is to generate a design/architecture-focused continuation context
for an AI conversation about system design.
The output will be pasted into a new ChatGPT, Claude, or Gemini
session so the design discussion can continue without loss of context.

Follow these rules:

- Output Markdown only.
- Do not include any introductory text.
- Do not include closing remarks.
- Do not invent information that is not in the transcript.
- Be precise about design decisions and rationale.
- Use technical language appropriate to architecture level.
- Extract all decisions made, alternatives considered, and trade-offs evaluated.

Use this exact section structure:

# Design/Architecture Session Continuation Context

## Design Problem
What problem is being solved?
Key constraints and requirements.
Scale and performance targets.
Non-functional requirements (security, reliability, etc.).

## Architectural Decisions Made
For each major decision:
- Decision: [What was decided?]
- Rationale: [Why this choice?]
- Implications: [What does this enable or constrain?]

## Alternatives Considered
For each alternative:
- Approach: [Name or description]
- Pros: [Advantages of this approach]
- Cons: [Disadvantages of this approach]
- Why rejected: [Why not chosen over the selected approach]

## Trade-offs Discussed
Trade-off 1: [One dimension vs. another]
- Analysis: [How was this trade-off analyzed?]
- Decision made: [Which side was chosen and why?]

(repeat for each significant trade-off)

## Architecture Diagram/Model
High-level components and their relationships.
Data flow between components.
Integration points and interfaces.
Any diagrams, sketches, or models discussed.

## Outstanding Design Questions
Questions still to be resolved.
Items needing more research or investigation.
Follow-up discussions needed.

## Design Validation & Next Steps
How to validate this design?
Prototyping or proof-of-concept needed?
What is the next design phase?
Risk areas to monitor during implementation.

## Continuation Guidance
Brief instruction for the next AI on how to continue the design discussion
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
- Resolutions: {state.get("resolutions", [])}
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
        "# Design/Architecture Session Continuation Context\n\n"
        "Gemini did not return a response.\n\n"
        f"Design topic: {state.get('topic', '')}\n\n"
        f"Latest user message: "
        f"{state.get('latest_user_message', '')}"
    )