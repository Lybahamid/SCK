from app.parsers.base_parser import BaseParser, ParsedMessage, ParsedSession
from typing import List
import re


class RawTextParser(BaseParser):
    """
    Parses plain text pasted directly by the user.
    This is the fallback parser when no structured input is available.
    Best effort parsing based on common conversation patterns.
    """

    # Common patterns users use when copying chats
    USER_PATTERNS = [
        r"^(you|user|me|human)\s*[:\-]\s*",
        r"^(you|user|me|human)\s*\n",
    ]

    ASSISTANT_PATTERNS = [
        r"^(chatgpt|claude|gemini|gpt|assistant|ai|bot)\s*[:\-]\s*",
        r"^(chatgpt|claude|gemini|gpt|assistant|ai|bot)\s*\n",
    ]

    def parse(self, raw_input: str) -> ParsedSession:
        """
        Accepts a plain text string of a conversation.
        Attempts to detect user and assistant turns.
        """
        try:
            lines = raw_input.strip().splitlines()
            messages = self._extract_messages(lines)

            return ParsedSession(
                title="Pasted Conversation",
                source_platform="unknown",
                input_method="raw_text",
                messages=messages,
                message_count=len(messages),
                raw_input=raw_input,
            )

        except Exception as e:
            raise ValueError(f"Failed to parse raw text: {str(e)}")

    def _extract_messages(self, lines: List[str]) -> List[ParsedMessage]:
        """
        Attempts to split the text into user and assistant turns.
        Falls back to treating the entire text as a single user message
        if no pattern is detected.
        """
        messages = []
        position = 0
        current_role = None
        current_content = []

        for line in lines:
            detected_role = self._detect_role(line)

            if detected_role:
                # Save previous message if exists
                if current_role and current_content:
                    content = self.clean_content("\n".join(current_content))
                    if content:
                        messages.append(
                            ParsedMessage(
                                role=current_role,
                                content=content,
                                position=position,
                                timestamp=None,
                            )
                        )
                        position += 1

                # Start new message
                current_role = detected_role
                cleaned_line = self._strip_role_prefix(line)
                current_content = [cleaned_line] if cleaned_line else []

            else:
                # Continue current message
                current_content.append(line)

        # Save last message
        if current_role and current_content:
            content = self.clean_content("\n".join(current_content))
            if content:
                messages.append(
                    ParsedMessage(
                        role=current_role,
                        content=content,
                        position=position,
                        timestamp=None,
                    )
                )

        # Fallback: treat entire input as single user message
        if not messages:
            messages.append(
                ParsedMessage(
                    role="user",
                    content=self.clean_content("\n".join(lines)),
                    position=0,
                    timestamp=None,
                )
            )

        return messages

    def _detect_role(self, line: str) -> str:
        """
        Returns 'user' or 'assistant' if the line starts with a role indicator.
        Returns None if no role is detected.
        """
        line_lower = line.lower().strip()

        for pattern in self.USER_PATTERNS:
            if re.match(pattern, line_lower):
                return "user"

        for pattern in self.ASSISTANT_PATTERNS:
            if re.match(pattern, line_lower):
                return "assistant"

        return None

    def _strip_role_prefix(self, line: str) -> str:
        """
        Removes the role label from the start of the line.
        Example: "You: Hello" becomes "Hello"
        """
        return re.sub(
            r"^(you|user|me|human|chatgpt|claude|gemini|gpt|assistant|ai|bot)\s*[:\-]\s*",
            "",
            line,
            flags=re.IGNORECASE,
        ).strip()