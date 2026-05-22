from abc import ABC, abstractmethod
from typing import List
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class ParsedMessage(BaseModel):
    """
    Unified message format that all parsers must return.
    Regardless of input source, every message becomes this.
    """
    role: str                           # "user" or "assistant"
    content: str                        # Raw message text
    position: int                       # Order in conversation (0-indexed)
    timestamp: Optional[datetime]       # Not always available


class ParsedSession(BaseModel):
    """
    Unified session format returned by all parsers.
    """
    title: Optional[str]                # Conversation title if available
    source_platform: str                # chatgpt, claude, gemini, unknown
    input_method: str                   # json_upload, share_link, raw_text, extension
    messages: List[ParsedMessage]       # All messages in order
    message_count: int                  # Total number of messages
    raw_input: Optional[str] = None     # Original raw input for debugging


class BaseParser(ABC):
    """
    Abstract base class that all parsers must inherit from.
    Every parser must implement the parse() method.
    """

    @abstractmethod
    def parse(self, raw_input) -> ParsedSession:
        """
        Takes raw input (JSON dict, string, URL, etc.)
        Returns a unified ParsedSession object.
        Must be implemented by every parser.
        """
        pass

    def validate_messages(self, messages: List[ParsedMessage]) -> bool:
        """
        Basic validation to ensure parsed messages are usable.
        """
        if not messages:
            return False
        if len(messages) < 2:
            return False
        return True

    def clean_content(self, text: str) -> str:
        """
        Cleans raw message text.
        Strips excessive whitespace and empty lines.
        """
        if not text:
            return ""
        lines = text.splitlines()
        cleaned = [line.strip() for line in lines if line.strip()]
        return "\n".join(cleaned)