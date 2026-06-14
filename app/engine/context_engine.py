from app.parsers.base_parser import ParsedSession
from app.engine.strategies import (
    full,
    concise,
    technical,
    creative,
    full_ai,
    handoff_ai,
    debug_ai,
    code_review_ai,
    documentation_ai,
    design_ai,
)

from app.engine.platform_formatter import format_for_platform


STRATEGIES = {
    "full": full.generate,
    "concise": concise.generate,
    "technical": technical.generate,
    "creative": creative.generate,
    "full_ai": full_ai.generate,
    "handoff_ai": handoff_ai.generate,
    "debug_ai": debug_ai.generate,
    "code_review_ai": code_review_ai.generate,
    "documentation_ai": documentation_ai.generate,
    "design_ai": design_ai.generate,
}


class ContextEngine:
    """
    Core context generation engine.
    Accepts a ParsedSession and returns a formatted context document.
    """

    def generate(
        self,
        session: ParsedSession,
        strategy: str = "full",
        target_platform: str = "generic",
    ) -> dict:
        """
        Main entry point for context generation.

        Parameters:
            session         : ParsedSession object from any parser
            strategy        : full | concise | technical | creative | full_ai | handoff_ai |
                             debug_ai | code_review_ai | documentation_ai | design_ai
            target_platform : chatgpt | claude | gemini | generic

        Returns:
            dict with generated context and metadata
        """

        # Validate strategy
        if strategy not in STRATEGIES:
            raise ValueError(
                f"Invalid strategy '{strategy}'. "
                f"Choose from: {list(STRATEGIES.keys())}"
            )

        # Validate session has messages
        if not session.messages:
            raise ValueError("Session has no messages to process.")

        if session.message_count < 2:
            raise ValueError(
                "Session must have at least 2 messages to generate context."
            )

        # Generate raw context using selected strategy
        raw_context = STRATEGIES[strategy](session)

        # Format for target platform
        formatted_context = format_for_platform(raw_context, target_platform)

        return {
            "context": formatted_context,
            "strategy": strategy,
            "target_platform": target_platform,
            "source_platform": session.source_platform,
            "message_count": session.message_count,
            "title": session.title,
        }