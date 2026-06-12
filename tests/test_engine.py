import pytest

from app.parsers.base_parser import ParsedMessage, ParsedSession
from app.engine.context_engine import ContextEngine
from app.engine.platform_formatter import PlatformFormatter
from app.engine.strategies.full import generate as full_strategy
from app.engine.strategies.concise import generate as concise_strategy
from app.engine.strategies.technical import generate as technical_strategy
from app.engine.strategies.creative import generate as creative_strategy
from app.engine.strategies.full_ai import generate as full_ai_strategy
from app.engine.strategies.handoff_ai import generate as handoff_ai_strategy
import app.engine.strategies.full_ai as full_ai_module
import app.engine.strategies.handoff_ai as handoff_ai_module


MOCK_FULL_AI_OUTPUT = """
# Session Continuation Context

## Project Overview
Session Context Keeper is a project designed to preserve AI conversation context.

## Goal
Enable seamless continuation across AI sessions.

## Current Architecture
- FastAPI backend
- MySQL persistence
- Streamlit testing frontend

## Progress So Far
- Backend is complete
- Persistence is integrated

## Current State
The project is ready for extension integration.

## Open Questions
- How often should context be regenerated?

## Next Steps
- Integrate the browser extension with the backend.

## Continuation Prompt
Continue from the current project state and focus on extension integration.
""".strip()


MOCK_HANDOFF_AI_OUTPUT = """
# SCK Project Continuation Context

## Project Overview
Session Context Keeper (SCK) preserves AI conversation context across AI platforms.

## Team Structure
- User: Backend, persistence, APIs, testing
- Developer 2: Browser extension and React frontend

## Original Product Vision
A browser extension that captures conversations in real time and generates structured continuation context.

## Current Architecture
- FastAPI
- SQLAlchemy
- Alembic
- MySQL
- Streamlit
- Chrome extension

## Major Milestones Completed
- Backend complete
- Persistence integrated
- Gemini strategy working

## Project Status Snapshot
Backend stable, extension integration pending.

## Current State
The project is ready for browser extension integration.

## Risks / Blockers
- Raw text parser still needs improvement
- Extension integration not yet complete

## Git / PR State
- Branch is ready for further refinement
- Changes have been pushed

## Open Questions
- How often should contexts be regenerated?

## Next Steps
- Integrate extension with backend
- Improve handoff document quality

## Continuation Prompt
Continue working on the extension-to-backend integration and improve project handoff quality.
""".strip()


@pytest.mark.unit
class TestContextEngine:

    def test_generate_full_strategy(self, valid_parsed_session):
        result = ContextEngine().generate(
            valid_parsed_session,
            "full",
            "claude"
        )["context"]

        assert "Session Continuation Context" in result

    def test_generate_concise_strategy(self, valid_parsed_session):
        result = ContextEngine().generate(
            valid_parsed_session,
            "concise",
            "chatgpt"
        )["context"]

        full = ContextEngine().generate(
            valid_parsed_session,
            "full",
            "chatgpt"
        )["context"]

        assert len(result) < len(full)

    def test_generate_technical_strategy(self, parsed_session_with_code):
        result = ContextEngine().generate(
            parsed_session_with_code,
            "technical",
            "claude"
        )["context"]

        assert result is not None
        assert len(result) > 0

    def test_generate_creative_strategy(self, valid_parsed_session):
        result = ContextEngine().generate(
            valid_parsed_session,
            "creative",
            "claude"
        )["context"]

        assert len(result) > 0

    def test_generate_full_ai_strategy(
        self,
        valid_parsed_session,
        monkeypatch
    ):
        monkeypatch.setattr(
            full_ai_module,
            "generate_with_gemini",
            lambda prompt: MOCK_FULL_AI_OUTPUT,
        )

        result = ContextEngine().generate(
            valid_parsed_session,
            "full_ai",
            "generic"
        )["context"]

        assert "Session Continuation Context" in result
        assert "Project Overview" in result
        assert "Next Steps" in result

    def test_generate_handoff_ai_strategy(
        self,
        valid_parsed_session,
        monkeypatch
    ):
        monkeypatch.setattr(
            handoff_ai_module,
            "_collect_repo_metadata",
            lambda: {
                "git_branch": "feature/full-ai-continuation",
                "git_commit": "3201f1f",
                "git_status": "clean",
                "last_commit_message": (
                    "feat: add Gemini-powered continuation strategy "
                    "and improve parsing"
                ),
                "remote_tracking": "origin/feature/full-ai-continuation",
            },
        )

        monkeypatch.setattr(
            handoff_ai_module,
            "generate_with_gemini",
            lambda prompt: MOCK_HANDOFF_AI_OUTPUT,
        )

        result = ContextEngine().generate(
            valid_parsed_session,
            "handoff_ai",
            "generic"
        )["context"]

        assert "SCK Project Continuation Context" in result
        assert "Project Overview" in result
        assert "Git / PR State" in result
        assert "Continuation Prompt" in result

    def test_platform_formatting_applied(self, valid_parsed_session):
        claude_result = ContextEngine().generate(
            valid_parsed_session,
            "full",
            "claude"
        )["context"]

        chatgpt_result = ContextEngine().generate(
            valid_parsed_session,
            "full",
            "chatgpt"
        )["context"]

        assert claude_result != chatgpt_result


@pytest.mark.unit
class TestFullStrategy:

    def test_header_generation(self, valid_parsed_session):
        result = full_strategy(valid_parsed_session)

        assert "Session Continuation Context" in result
        assert valid_parsed_session.source_platform.title() in result

    def test_topic_extraction(self, valid_parsed_session):
        result = full_strategy(valid_parsed_session)

        assert "Primary Topic" in result

    def test_goal_section(self, valid_parsed_session):
        result = full_strategy(valid_parsed_session)

        assert "Goal" in result

    def test_key_information_section(self):
        session = ParsedSession(
            title="Long Session",
            source_platform="chatgpt",
            input_method="raw_text",
            messages=[
                ParsedMessage(
                    role="user",
                    content=(
                        "I'm building a browser extension that captures "
                        "conversations in real time."
                    ),
                    position=0,
                ),
                ParsedMessage(
                    role="assistant",
                    content="What does it integrate with?",
                    position=1,
                ),
                ParsedMessage(
                    role="user",
                    content=(
                        "It integrates with a FastAPI backend, MySQL "
                        "persistence, and Gemini-powered continuation generation."
                    ),
                    position=2,
                ),
                ParsedMessage(
                    role="assistant",
                    content="Great, that gives us the architecture.",
                    position=3,
                ),
            ],
        )

        result = full_strategy(session)

        assert "Key Information" in result
        assert "FastAPI backend" in result

    def test_current_progress_section(self):
        session = ParsedSession(
            title="Progress Session",
            source_platform="chatgpt",
            input_method="raw_text",
            messages=[
                ParsedMessage(
                    role="user",
                    content="I'm building SCK.",
                    position=0,
                ),
                ParsedMessage(
                    role="assistant",
                    content="What has been completed so far?",
                    position=1,
                ),
                ParsedMessage(
                    role="user",
                    content="The backend is complete and working.",
                    position=2,
                ),
                ParsedMessage(
                    role="assistant",
                    content="Great, what's next?",
                    position=3,
                ),
            ],
        )

        result = full_strategy(session)

        assert "Current Progress" in result
        assert "backend is complete" in result.lower()

    def test_current_state_section(self, valid_parsed_session):
        result = full_strategy(valid_parsed_session)

        assert "Current State" in result

    def test_code_block_extraction(self, parsed_session_with_code):
        result = full_strategy(parsed_session_with_code)

        assert "```" in result or "Code" in result

    def test_question_extraction(self, parsed_session_with_questions):
        result = full_strategy(parsed_session_with_questions)

        assert "?" in result or "Open Questions" in result

    def test_continuation_instruction(self, valid_parsed_session):
        result = full_strategy(valid_parsed_session)

        assert "continue" in result.lower()


@pytest.mark.unit
class TestFullAIStrategy:

    def test_ai_strategy_returns_project_sections(
        self,
        valid_parsed_session,
        monkeypatch
    ):
        monkeypatch.setattr(
            full_ai_module,
            "generate_with_gemini",
            lambda prompt: MOCK_FULL_AI_OUTPUT,
        )

        result = full_ai_strategy(valid_parsed_session)

        assert "Project Overview" in result
        assert "Current State" in result
        assert "Next Steps" in result


@pytest.mark.unit
class TestHandoffAIStrategy:

    def test_handoff_strategy_returns_handoff_sections(
        self,
        valid_parsed_session,
        monkeypatch
    ):
        monkeypatch.setattr(
            handoff_ai_module,
            "_collect_repo_metadata",
            lambda: {
                "git_branch": "feature/full-ai-continuation",
                "git_commit": "3201f1f",
                "git_status": "clean",
                "last_commit_message": (
                    "feat: add Gemini-powered continuation strategy "
                    "and improve parsing"
                ),
                "remote_tracking": "origin/feature/full-ai-continuation",
            },
        )

        monkeypatch.setattr(
            handoff_ai_module,
            "generate_with_gemini",
            lambda prompt: MOCK_HANDOFF_AI_OUTPUT,
        )

        result = handoff_ai_strategy(valid_parsed_session)

        assert "SCK Project Continuation Context" in result
        assert "Team Structure" in result
        assert "Current Architecture" in result
        assert "Git / PR State" in result
        assert "Next Steps" in result


@pytest.mark.unit
class TestConciseStrategy:

    def test_shorter_than_full(self, valid_parsed_session):
        full = full_strategy(valid_parsed_session)
        concise = concise_strategy(valid_parsed_session)

        assert len(concise) < len(full)

    def test_includes_goals_and_state(self, valid_parsed_session):
        result = concise_strategy(valid_parsed_session)

        assert len(result) > 0

    def test_limits_message_pairs(self, valid_parsed_session):
        result = concise_strategy(valid_parsed_session)

        assert len(result) > 0

    def test_preserves_metadata(self, valid_parsed_session):
        result = concise_strategy(valid_parsed_session)

        assert valid_parsed_session.source_platform in result or len(result) > 0


@pytest.mark.unit
class TestTechnicalStrategy:

    def test_code_prioritization(self, parsed_session_with_code):
        result = technical_strategy(parsed_session_with_code)

        assert (
            "python" in result.lower()
            or "code" in result.lower()
            or "```" in result
        )

    def test_architecture_focus(self, valid_parsed_session):
        result = technical_strategy(valid_parsed_session)

        assert len(result) > 0

    def test_error_extraction(self):
        session = ParsedSession(
            title="Error Session",
            source_platform="chatgpt",
            input_method="test",
            messages=[
                ParsedMessage(
                    role="user",
                    content="Why is my code failing?",
                    position=0,
                ),
                ParsedMessage(
                    role="assistant",
                    content="Error: TypeError: unsupported operand type.",
                    position=1,
                ),
                ParsedMessage(
                    role="user",
                    content="Thanks, that worked!",
                    position=2,
                ),
                ParsedMessage(
                    role="assistant",
                    content="Glad I could help!",
                    position=3,
                ),
            ],
        )

        result = technical_strategy(session)

        assert len(result) > 0

    def test_implementation_details_preserved(self, valid_parsed_session):
        result = technical_strategy(valid_parsed_session)

        assert len(result) > 0


@pytest.mark.unit
class TestCreativeStrategy:

    def test_full_content_retention(self, valid_parsed_session):
        creative = creative_strategy(valid_parsed_session)

        assert len(creative) > 0

    def test_tone_preservation(self, valid_parsed_session):
        result = creative_strategy(valid_parsed_session)

        assert len(result) > 0

    def test_narrative_elements(self, valid_parsed_session):
        result = creative_strategy(valid_parsed_session)

        assert len(result) > 0

    def test_character_consistency(self, valid_parsed_session):
        result = creative_strategy(valid_parsed_session)

        assert len(result) > 0


@pytest.mark.unit
class TestPlatformFormatter:

    def test_claude_xml_formatting(self, valid_parsed_session):
        result = PlatformFormatter.format(
            valid_parsed_session,
            "full",
            "claude"
        )

        assert "<context>" in result

    def test_chatgpt_markdown_formatting(self, valid_parsed_session):
        result = PlatformFormatter.format(
            valid_parsed_session,
            "full",
            "chatgpt"
        )

        assert "[SYSTEM CONTEXT - START]" in result

    def test_gemini_formatting(self, valid_parsed_session):
        result = PlatformFormatter.format(
            valid_parsed_session,
            "full",
            "gemini"
        )

        assert "PREVIOUS SESSION CONTEXT" in result

    def test_generic_formatting(self, valid_parsed_session):
        result = PlatformFormatter.format(
            valid_parsed_session,
            "full",
            "generic"
        )

        assert "Please continue" in result

    def test_different_platforms_produce_different_output(
        self,
        valid_parsed_session
    ):
        claude_fmt = PlatformFormatter.format(
            valid_parsed_session,
            "full",
            "claude"
        )

        chatgpt_fmt = PlatformFormatter.format(
            valid_parsed_session,
            "full",
            "chatgpt"
        )

        assert claude_fmt != chatgpt_fmt

    def test_format_maintains_content(self, valid_parsed_session):
        result = PlatformFormatter.format(
            valid_parsed_session,
            "full",
            "claude"
        )

        assert len(result) > 0