def format_for_platform(
    context: str,
    platform: str,
) -> str:
    """
    Formats generated context for a specific target AI platform.
    """

    formatters = {
        "chatgpt": _format_for_chatgpt,
        "claude": _format_for_claude,
        "gemini": _format_for_gemini,
        "generic": _format_generic,
    }

    formatter = formatters.get(
        platform,
        _format_generic,
    )

    return formatter(context)


# ============================================================================
# CHATGPT FORMAT
# ============================================================================

def _format_for_chatgpt(context: str) -> str:
    return (
        "[SYSTEM CONTEXT - START]\n\n"
        f"{context}\n\n"
        "[SYSTEM CONTEXT - END]\n\n"
        "Please acknowledge that you have read and understood "
        "the above context, then continue assisting from where we left off."
    )


# ============================================================================
# CLAUDE FORMAT
# ============================================================================

def _format_for_claude(context: str) -> str:
    return (
        "<context>\n\n"
        f"{context}\n\n"
        "</context>\n\n"
        "Please review the context above and continue "
        "the conversation from where it left off."
    )


# ============================================================================
# GEMINI FORMAT
# ============================================================================

def _format_for_gemini(context: str) -> str:
    return (
        "**PREVIOUS SESSION CONTEXT**\n\n"
        f"{context}\n\n"
        "**END OF CONTEXT**\n\n"
        "Please continue from where we left off."
    )


# ============================================================================
# GENERIC FORMAT
# ============================================================================

def _format_generic(context: str) -> str:
    return (
        f"{context}\n\n"
        "---\n"
        "Please continue from where we left off."
    )


# ============================================================================
# PLATFORM FORMATTER CLASS
# ============================================================================

class PlatformFormatter:
    """
    Class wrapper around formatting functions.
    Used by the test suite and any class-based integrations.
    """

    @staticmethod
    def format(
        session,
        strategy: str = "full",
        target_platform: str = "generic",
    ) -> str:

        from app.engine.context_engine import ContextEngine

        engine = ContextEngine()

        result = engine.generate(
            session=session,
            strategy=strategy,
            target_platform=target_platform,
        )

        return result["context"]