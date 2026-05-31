class PlatformFormatter:
    """
    Class wrapper around platform formatting functions.
    Provides a static interface for the test suite and
    any other code that prefers class-based access.
    """

    @staticmethod
    def format(
        session,
        strategy: str = "full",
        target_platform: str = "generic",
    ) -> str:
        """
        Generates and formats context for a given session.
        Accepts a ParsedSession object, strategy, and target platform.
        Returns a formatted context string.
        """
        from app.engine.context_engine import ContextEngine

        engine = ContextEngine()
        result = engine.generate(
            session=session,
            strategy=strategy,
            target_platform=target_platform,
        )
        return result["context"]


def format_for_platform(context: str, platform: str) -> str:
    """
    Formats the generated context document for the target AI platform.
    Different platforms respond better to different formatting styles.

    Parameters:
        context  : Raw generated context string
        platform : chatgpt | claude | gemini | generic

    Returns:
        Formatted context string ready to paste into the target platform
    """

    formatters = {
        "chatgpt": _format_for_chatgpt,
        "claude": _format_for_claude,
        "gemini": _format_for_gemini,
        "generic": _format_generic,
    }

    formatter = formatters.get(platform, _format_generic)
    return formatter(context)


def _format_for_chatgpt(context: str) -> str:
    """
    ChatGPT responds well to system-message style context blocks.
    """
    return (
        "[SYSTEM CONTEXT - START]\n\n"
        f"{context}\n\n"
        "[SYSTEM CONTEXT - END]\n\n"
        "Please acknowledge that you have read and understood "
        "the above context, then continue assisting from where we left off."
    )


def _format_for_claude(context: str) -> str:
    """
    Claude responds well to XML-style structured context.
    """
    return (
        "<context>\n\n"
        f"{context}\n\n"
        "</context>\n\n"
        "Please review the context above and continue "
        "the conversation from where it left off."
    )


def _format_for_gemini(context: str) -> str:
    """
    Gemini responds well to clearly labeled sections.
    """
    return (
        "**PREVIOUS SESSION CONTEXT**\n\n"
        f"{context}\n\n"
        "**END OF CONTEXT**\n\n"
        "Please continue from where we left off."
    )


def _format_generic(context: str) -> str:
    """
    Generic format that works across all platforms.
    """
    return (
        f"{context}\n\n"
        "---\n"
        "Please continue from where we left off."
    )
    