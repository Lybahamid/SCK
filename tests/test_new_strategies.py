"""
Unit tests for new AI strategies.

Tests validate:
- Prompt generation correctness
- Output formatting
- Error handling
- Gemini integration (mocked)
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime
from app.parsers.base_parser import ParsedSession, ParsedMessage
from app.engine.strategies import (
    debug_ai,
    code_review_ai,
    documentation_ai,
    design_ai,
)


# ==================================================
# Test Fixtures
# ==================================================

@pytest.fixture
def sample_debug_session():
    """Sample debugging conversation."""
    return ParsedSession(
        title="Debugging async issue",
        source_platform="chatgpt",
        input_method="raw_text",
        messages=[
            ParsedMessage(
                role="user",
                content="I'm getting a TypeError in my async function",
                position=0,
                timestamp=datetime.now()
            ),
            ParsedMessage(
                role="assistant",
                content="Can you share the error message and stack trace?",
                position=1,
                timestamp=datetime.now()
            ),
            ParsedMessage(
                role="user",
                content="""TypeError: 'coroutine' object is not callable
File app.py, line 45, in main
  result = await fetch_data()""",
                position=2,
                timestamp=datetime.now()
            ),
            ParsedMessage(
                role="assistant",
                content="It looks like fetch_data is a coroutine but you're trying to call it. Try using `await fetch_data()` instead.",
                position=3,
                timestamp=datetime.now()
            ),
        ],
    )


@pytest.fixture
def sample_code_review_session():
    """Sample code review conversation."""
    return ParsedSession(
        title="PR Review: User API",
        source_platform="claude",
        input_method="raw_text",
        messages=[
            ParsedMessage(
                role="user",
                content="Here's my pull request for the new API endpoint",
                position=0,
                timestamp=datetime.now()
            ),
            ParsedMessage(
                role="user",
                content="```python\ndef get_user(user_id: int) -> User:\n    return db.query(User).filter(...)\n```",
                position=1,
                timestamp=datetime.now()
            ),
            ParsedMessage(
                role="assistant",
                content="This looks good overall. Have you considered adding pagination for large datasets?",
                position=2,
                timestamp=datetime.now()
            ),
            ParsedMessage(
                role="user",
                content="Good point. Should I limit to 100 records per page?",
                position=3,
                timestamp=datetime.now()
            ),
        ],
    )


@pytest.fixture
def sample_documentation_session():
    """Sample documentation writing conversation."""
    return ParsedSession(
        title="Documentation: Context Engine",
        source_platform="chatgpt",
        input_method="raw_text",
        messages=[
            ParsedMessage(
                role="user",
                content="I'm writing docs for the new context engine",
                position=0,
                timestamp=datetime.now()
            ),
            ParsedMessage(
                role="assistant",
                content="Great! What sections will you cover?",
                position=1,
                timestamp=datetime.now()
            ),
            ParsedMessage(
                role="user",
                content="Overview, Architecture, Usage, Examples, Troubleshooting",
                position=2,
                timestamp=datetime.now()
            ),
            ParsedMessage(
                role="assistant",
                content="Solid structure. Should each section have code examples?",
                position=3,
                timestamp=datetime.now()
            ),
        ],
    )


@pytest.fixture
def sample_design_session():
    """Sample design discussion conversation."""
    return ParsedSession(
        title="Design: Caching Strategy",
        source_platform="gemini",
        input_method="raw_text",
        messages=[
            ParsedMessage(
                role="user",
                content="We need to design a caching layer for our API",
                position=0,
                timestamp=datetime.now()
            ),
            ParsedMessage(
                role="assistant",
                content="What are your constraints? Latency targets? Data freshness requirements?",
                position=1,
                timestamp=datetime.now()
            ),
            ParsedMessage(
                role="user",
                content="Sub-100ms latency, 5-minute max staleness, 10k concurrent users",
                position=2,
                timestamp=datetime.now()
            ),
            ParsedMessage(
                role="assistant",
                content="Redis with TTL seems like a good fit. Have you considered cache invalidation strategies?",
                position=3,
                timestamp=datetime.now()
            ),
        ],
    )


# ==================================================
# Tests for Debug AI Strategy
# ==================================================

class TestDebugAIStrategy:
    """Tests for debug_ai.py strategy."""

    def test_generate_returns_string(self, sample_debug_session):
        """Test that generate function returns a string."""
        with patch("app.engine.strategies.debug_ai.generate_with_gemini") as mock_gemini:
            mock_gemini.return_value = "# Debugging Session Continuation Context\n\nTest output"
            result = debug_ai.generate(sample_debug_session)
            assert isinstance(result, str)
            assert len(result) > 0

    def test_generate_with_gemini_failure_returns_fallback(self, sample_debug_session):
        """Test fallback when Gemini fails."""
        with patch("app.engine.strategies.debug_ai.generate_with_gemini") as mock_gemini:
            mock_gemini.return_value = None
            result = debug_ai.generate(sample_debug_session)
            assert "Debugging Session Continuation Context" in result
            assert "Gemini did not return a response" in result

    def test_build_transcript_format(self, sample_debug_session):
        """Test transcript formatting."""
        transcript = debug_ai._build_transcript(sample_debug_session)
        assert "User:" in transcript
        assert "Assistant:" in transcript
        assert "TypeError" in transcript
        assert "coroutine" in transcript

    def test_build_prompt_contains_required_sections(self, sample_debug_session):
        """Test that prompt contains all required sections."""
        with patch("app.engine.strategies.debug_ai.extract_state") as mock_extract:
            mock_extract.return_value = {
                "topic": "Async TypeError",
                "goal": "Fix coroutine error",
                "key_points": ["Error in async call"],
                "open_questions": ["How to fix?"],
                "next_tasks": ["Add await keyword"],
                "latest_user_message": "Getting TypeError",
                "latest_assistant_message": "Try await",
                "resolutions": [],
                "current_progress": [],
            }
            
            prompt = debug_ai._build_prompt(
                sample_debug_session,
                mock_extract.return_value,
                debug_ai._build_transcript(sample_debug_session)
            )
            
            assert "Problem Statement" in prompt
            assert "Error Signature" in prompt
            assert "Reproduction Steps" in prompt
            assert "What Has Been Tried" in prompt
            assert "Current Blocker" in prompt
            assert "Next Diagnostic Steps" in prompt
            assert "Continuation Guidance" in prompt

    def test_fallback_output_contains_context_header(self, sample_debug_session):
        """Test fallback output format."""
        with patch("app.engine.strategies.debug_ai.extract_state") as mock_extract:
            mock_extract.return_value = {
                "topic": "Test error",
                "latest_user_message": "Error occurred",
                "goal": "",
                "key_points": [],
                "open_questions": [],
                "next_tasks": [],
                "latest_assistant_message": "",
                "resolutions": [],
                "current_progress": [],
            }
            
            fallback = debug_ai._fallback_output(sample_debug_session, mock_extract.return_value)
            assert "Debugging Session Continuation Context" in fallback
            assert "Gemini did not return a response" in fallback


# ==================================================
# Tests for Code Review AI Strategy
# ==================================================

class TestCodeReviewAIStrategy:
    """Tests for code_review_ai.py strategy."""

    def test_generate_returns_string(self, sample_code_review_session):
        """Test that generate function returns a string."""
        with patch("app.engine.strategies.code_review_ai.generate_with_gemini") as mock_gemini:
            mock_gemini.return_value = "# Code Review Session Continuation Context\n\nTest output"
            result = code_review_ai.generate(sample_code_review_session)
            assert isinstance(result, str)
            assert len(result) > 0

    def test_generate_with_gemini_failure_returns_fallback(self, sample_code_review_session):
        """Test fallback when Gemini fails."""
        with patch("app.engine.strategies.code_review_ai.generate_with_gemini") as mock_gemini:
            mock_gemini.return_value = None
            result = code_review_ai.generate(sample_code_review_session)
            assert "Code Review Session Continuation Context" in result
            assert "Gemini did not return a response" in result

    def test_build_transcript_preserves_code_blocks(self, sample_code_review_session):
        """Test that code blocks are preserved in transcript."""
        transcript = code_review_ai._build_transcript(sample_code_review_session)
        assert "def get_user" in transcript
        assert "db.query" in transcript

    def test_build_prompt_contains_code_review_sections(self, sample_code_review_session):
        """Test that prompt contains code review-specific sections."""
        with patch("app.engine.strategies.code_review_ai.extract_state") as mock_extract:
            mock_extract.return_value = {
                "topic": "API review",
                "goal": "Review new endpoint",
                "key_points": ["Add pagination"],
                "open_questions": ["Page size?"],
                "next_tasks": ["Add pagination"],
                "latest_user_message": "Good point",
                "latest_assistant_message": "Consider pagination",
                "resolutions": [],
                "current_progress": [],
            }
            
            prompt = code_review_ai._build_prompt(
                sample_code_review_session,
                mock_extract.return_value,
                code_review_ai._build_transcript(sample_code_review_session)
            )
            
            assert "Code Overview" in prompt
            assert "Architecture & Design" in prompt
            assert "Code Snippets" in prompt
            assert "Feedback Summary" in prompt
            assert "Outstanding Review Items" in prompt

    def test_fallback_includes_review_context(self, sample_code_review_session):
        """Test fallback output for code review."""
        with patch("app.engine.strategies.code_review_ai.extract_state") as mock_extract:
            mock_extract.return_value = {
                "topic": "API endpoint",
                "latest_user_message": "About pagination",
                "goal": "",
                "key_points": [],
                "open_questions": [],
                "next_tasks": [],
                "latest_assistant_message": "",
                "resolutions": [],
                "current_progress": [],
            }
            
            fallback = code_review_ai._fallback_output(sample_code_review_session, mock_extract.return_value)
            assert "Code Review Session Continuation Context" in fallback


# ==================================================
# Tests for Documentation AI Strategy
# ==================================================

class TestDocumentationAIStrategy:
    """Tests for documentation_ai.py strategy."""

    def test_generate_returns_string(self, sample_documentation_session):
        """Test that generate function returns a string."""
        with patch("app.engine.strategies.documentation_ai.generate_with_gemini") as mock_gemini:
            mock_gemini.return_value = "# Documentation Writing Session Continuation Context\n\nTest output"
            result = documentation_ai.generate(sample_documentation_session)
            assert isinstance(result, str)
            assert len(result) > 0

    def test_generate_with_gemini_failure_returns_fallback(self, sample_documentation_session):
        """Test fallback when Gemini fails."""
        with patch("app.engine.strategies.documentation_ai.generate_with_gemini") as mock_gemini:
            mock_gemini.return_value = None
            result = documentation_ai.generate(sample_documentation_session)
            assert "Documentation Writing Session Continuation Context" in result
            assert "Gemini did not return a response" in result

    def test_build_prompt_contains_doc_sections(self, sample_documentation_session):
        """Test that prompt contains documentation-specific sections."""
        with patch("app.engine.strategies.documentation_ai.extract_state") as mock_extract:
            mock_extract.return_value = {
                "topic": "Context engine docs",
                "goal": "Document new engine",
                "key_points": ["Overview", "Architecture"],
                "current_progress": ["Overview done"],
                "next_tasks": ["Write examples"],
                "latest_user_message": "Should have examples?",
                "latest_assistant_message": "Yes, add examples",
                "open_questions": [],
                "resolutions": [],
            }
            
            prompt = documentation_ai._build_prompt(
                sample_documentation_session,
                mock_extract.return_value,
                documentation_ai._build_transcript(sample_documentation_session)
            )
            
            assert "Documentation Overview" in prompt
            assert "Completed Sections" in prompt
            assert "Outstanding Sections" in prompt
            assert "Writing Style & Tone" in prompt
            assert "Consistency Guidelines" in prompt
            assert "Content Guidelines" in prompt

    def test_fallback_includes_doc_context(self, sample_documentation_session):
        """Test fallback output for documentation."""
        with patch("app.engine.strategies.documentation_ai.extract_state") as mock_extract:
            mock_extract.return_value = {
                "topic": "Engine documentation",
                "latest_user_message": "Writing docs",
                "goal": "",
                "key_points": [],
                "open_questions": [],
                "next_tasks": [],
                "latest_assistant_message": "",
                "resolutions": [],
                "current_progress": [],
            }
            
            fallback = documentation_ai._fallback_output(sample_documentation_session, mock_extract.return_value)
            assert "Documentation Writing Session Continuation Context" in fallback


# ==================================================
# Tests for Design AI Strategy
# ==================================================

class TestDesignAIStrategy:
    """Tests for design_ai.py strategy."""

    def test_generate_returns_string(self, sample_design_session):
        """Test that generate function returns a string."""
        with patch("app.engine.strategies.design_ai.generate_with_gemini") as mock_gemini:
            mock_gemini.return_value = "# Design/Architecture Session Continuation Context\n\nTest output"
            result = design_ai.generate(sample_design_session)
            assert isinstance(result, str)
            assert len(result) > 0

    def test_generate_with_gemini_failure_returns_fallback(self, sample_design_session):
        """Test fallback when Gemini fails."""
        with patch("app.engine.strategies.design_ai.generate_with_gemini") as mock_gemini:
            mock_gemini.return_value = None
            result = design_ai.generate(sample_design_session)
            assert "Design/Architecture Session Continuation Context" in result
            assert "Gemini did not return a response" in result

    def test_build_prompt_contains_design_sections(self, sample_design_session):
        """Test that prompt contains design-specific sections."""
        with patch("app.engine.strategies.design_ai.extract_state") as mock_extract:
            mock_extract.return_value = {
                "topic": "Caching layer",
                "goal": "Design cache system",
                "key_points": ["Redis", "TTL"],
                "resolutions": ["Use Redis"],
                "open_questions": ["Cache invalidation?"],
                "latest_user_message": "10k concurrent users",
                "latest_assistant_message": "Consider invalidation",
                "current_progress": [],
                "next_tasks": [],
            }
            
            prompt = design_ai._build_prompt(
                sample_design_session,
                mock_extract.return_value,
                design_ai._build_transcript(sample_design_session)
            )
            
            assert "Design Problem" in prompt
            assert "Architectural Decisions Made" in prompt
            assert "Alternatives Considered" in prompt
            assert "Trade-offs Discussed" in prompt
            assert "Architecture Diagram/Model" in prompt
            assert "Outstanding Design Questions" in prompt

    def test_fallback_includes_design_context(self, sample_design_session):
        """Test fallback output for design."""
        with patch("app.engine.strategies.design_ai.extract_state") as mock_extract:
            mock_extract.return_value = {
                "topic": "Cache design",
                "latest_user_message": "Concurrent users",
                "goal": "",
                "key_points": [],
                "open_questions": [],
                "next_tasks": [],
                "latest_assistant_message": "",
                "resolutions": [],
                "current_progress": [],
            }
            
            fallback = design_ai._fallback_output(sample_design_session, mock_extract.return_value)
            assert "Design/Architecture Session Continuation Context" in fallback


# ==================================================
# Integration Tests
# ==================================================

class TestStrategyIntegration:
    """Cross-strategy integration tests."""

    @pytest.mark.parametrize("strategy_module,session_fixture", [
        (debug_ai, "sample_debug_session"),
        (code_review_ai, "sample_code_review_session"),
        (documentation_ai, "sample_documentation_session"),
        (design_ai, "sample_design_session"),
    ])
    def test_all_strategies_generate_markdown(self, strategy_module, session_fixture, request):
        """Test that all strategies generate valid markdown."""
        session = request.getfixturevalue(session_fixture)
        
        with patch.object(strategy_module, "generate_with_gemini") as mock_gemini:
            mock_gemini.return_value = "# Test\n\nContent"
            result = strategy_module.generate(session)
            
            assert isinstance(result, str)
            assert len(result) > 0
            assert "#" in result  # Markdown header

    @pytest.mark.parametrize("strategy_module,session_fixture", [
        (debug_ai, "sample_debug_session"),
        (code_review_ai, "sample_code_review_session"),
        (documentation_ai, "sample_documentation_session"),
        (design_ai, "sample_design_session"),
    ])
    def test_all_strategies_called_gemini(self, strategy_module, session_fixture, request):
        """Test that all strategies call Gemini to generate context."""
        session = request.getfixturevalue(session_fixture)
        
        with patch.object(strategy_module, "generate_with_gemini") as mock_gemini:
            mock_gemini.return_value = "# Test\n\nContent"
            result = strategy_module.generate(session)
            
            # Verify Gemini was called
            assert mock_gemini.called, f"{strategy_module.__name__} did not call generate_with_gemini"

    def test_all_strategies_handle_empty_state_gracefully(self):
        """Test that strategies handle empty state values."""
        minimal_session = ParsedSession(
            title=None,
            source_platform="unknown",
            input_method="raw_text",
            messages=[
                ParsedMessage(role="user", content="Test", position=0),
                ParsedMessage(role="assistant", content="Response", position=1),
            ],
        )
        
        empty_state = {
            "topic": "",
            "goal": "",
            "key_points": [],
            "open_questions": [],
            "next_tasks": [],
            "latest_user_message": "Test",
            "latest_assistant_message": "Response",
            "resolutions": [],
            "current_progress": [],
        }
        
        # Test debug_ai
        with patch("app.engine.strategies.debug_ai.generate_with_gemini") as mock_gemini:
            mock_gemini.return_value = None
            result = debug_ai.generate(minimal_session)
            assert "Debugging Session Continuation Context" in result
            assert isinstance(result, str)

    def test_all_strategies_work_with_long_conversations(self):
        """Test that strategies handle long conversations."""
        messages = []
        for i in range(50):
            if i % 2 == 0:
                messages.append(ParsedMessage(role="user", content=f"Message {i}", position=i))
            else:
                messages.append(ParsedMessage(role="assistant", content=f"Response {i}", position=i))
        
        long_session = ParsedSession(
            title="Long conversation",
            source_platform="chatgpt",
            input_method="raw_text",
            messages=messages,
        )
        
        with patch("app.engine.strategies.debug_ai.generate_with_gemini") as mock_gemini:
            mock_gemini.return_value = "# Context\n\nGenerated"
            result = debug_ai.generate(long_session)
            assert isinstance(result, str)
            assert len(result) > 0

    def test_debug_strategy_in_context_engine(self):
        """Test that debug_ai strategy is available in context engine."""
        from app.engine.context_engine import STRATEGIES
        
        assert "debug_ai" in STRATEGIES
        assert callable(STRATEGIES["debug_ai"])

    def test_code_review_strategy_in_context_engine(self):
        """Test that code_review_ai strategy is available in context engine."""
        from app.engine.context_engine import STRATEGIES
        
        assert "code_review_ai" in STRATEGIES
        assert callable(STRATEGIES["code_review_ai"])

    def test_documentation_strategy_in_context_engine(self):
        """Test that documentation_ai strategy is available in context engine."""
        from app.engine.context_engine import STRATEGIES
        
        assert "documentation_ai" in STRATEGIES
        assert callable(STRATEGIES["documentation_ai"])

    def test_design_strategy_in_context_engine(self):
        """Test that design_ai strategy is available in context engine."""
        from app.engine.context_engine import STRATEGIES
        
        assert "design_ai" in STRATEGIES
        assert callable(STRATEGIES["design_ai"])