from abc import ABC, abstractmethod
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime


class ParsedMessage(BaseModel):
    """
    Unified message format that all parsers must return.
    Regardless of input source, every message becomes this.
    """

    role: str
    content: str
    position: int
    timestamp: Optional[datetime] = None


class ParsedSession(BaseModel):
    """
    Unified session format returned by all parsers.
    """

    title: Optional[str] = None
    source_platform: str
    input_method: str
    messages: List[ParsedMessage]
    message_count: Optional[int] = None
    raw_input: Optional[str] = None

    def model_post_init(self, __context):
        """
        Automatically calculate message_count
        if not explicitly provided.
        """
        if self.message_count is None:
            self.message_count = len(self.messages)


class BaseParser(ABC):
    """
    Abstract base class that all parsers must inherit from.
    Every parser must implement the parse() method.
    """

    @abstractmethod
    def parse(self, raw_input) -> ParsedSession:
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
        """

        if not text:
            return ""

        lines = text.splitlines()

        cleaned = [
            line.strip()
            for line in lines
            if line.strip()
        ]

        return "\n".join(cleaned)