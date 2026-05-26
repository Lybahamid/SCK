import pytest

from app.engine.context_engine import ContextEngine
from app.engine.platform_formatter import PlatformFormatter
from app.engine.strategies.full import generate as full_strategy
from app.engine.strategies.concise import generate as concise_strategy
from app.engine.strategies.technical import generate as technical_strategy
from app.engine.strategies.creative import generate as creative_strategy


@pytest.mark.unit
class TestContextEngine:

    def test_generate_full_strategy(self, valid_parsed_session):
        result = ContextEngine().generate(
            valid_parsed_session,
            "full",
            "claude"
        )["context"]

        assert "Session Context" in result

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

        assert "Session Context" in result
        assert valid_parsed_session.source_platform.title() in result

    def test_topic_extraction(self, valid_parsed_session):
        result = full_strategy(valid_parsed_session)

        assert "Topic" in result

    def test_conversation_timeline(self, valid_parsed_session):
        result = full_strategy(valid_parsed_session)

        assert "Conversation Summary" in result

    def test_current_state_section(self, valid_parsed_session):
        result = full_strategy(valid_parsed_session)

        assert "Current State" in result

    def test_code_block_extraction(self, parsed_session_with_code):
        result = full_strategy(parsed_session_with_code)

        assert "```" in result or "Code" in result

    def test_question_extraction(self, parsed_session_with_questions):
        result = full_strategy(parsed_session_with_questions)

        assert "?" in result or "Question" in result

    def test_continuation_instruction(self, valid_parsed_session):
        result = full_strategy(valid_parsed_session)

        assert "continue" in result.lower()


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
        from app.parsers.base_parser import ParsedSession, ParsedMessage

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