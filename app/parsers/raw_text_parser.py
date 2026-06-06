from app.parsers.base_parser import BaseParser, ParsedMessage, ParsedSession
from typing import List, Optional
import re


class RawTextParser(BaseParser):
    """
    Parses plain text pasted directly by the user.

    Supports a wide range of role indicator formats
    so users can paste conversations from any source
    without reformatting.

    Recognized user indicators:
        User:, You:, Human:, Me:, U:, H:

    Recognized assistant indicators:
        Assistant:, A:, AI:, Bot:, GPT:, Claude:,
        Gemini:, ChatGPT:
    """

    USER_PATTERNS = [
        r"^(user|you|me|human|u|h)\s*[:\-]\s*",
        r"^(user|you|me|human)\s*\n",
    ]

    ASSISTANT_PATTERNS = [
        r"^(assistant|a|ai|bot|gpt|chatgpt|claude|gemini)\s*[:\-]\s*",
        r"^(assistant|chatgpt|claude|gemini|gpt|ai|bot)\s*\n",
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
            raise ValueError(
                f"Failed to parse raw text: {str(e)}"
            )

    def _extract_messages(
        self,
        lines: List[str],
    ) -> List[ParsedMessage]:
        """
        Splits the text into user and assistant turns.

        Falls back to treating the entire text as a single
        user message if no role pattern is detected.
        """

        messages = []
        position = 0
        current_role: Optional[str] = None
        current_content: List[str] = []

        for line in lines:

            detected_role = self._detect_role(line)

            if detected_role:

                # Save previous message
                if current_role and current_content:
                    content = self.clean_content(
                        "\n".join(current_content)
                    )

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
                cleaned = self._strip_role_prefix(line)
                current_content = [cleaned] if cleaned else []

            else:
                current_content.append(line)

        # Save last message
        if current_role and current_content:
            content = self.clean_content(
                "\n".join(current_content)
            )

            if content:
                messages.append(
                    ParsedMessage(
                        role=current_role,
                        content=content,
                        position=position,
                        timestamp=None,
                    )
                )

        # Fallback
        if not messages:
            messages.append(
                ParsedMessage(
                    role="user",
                    content=self.clean_content(
                        "\n".join(lines)
                    ),
                    position=0,
                    timestamp=None,
                )
            )

        return messages

    def _detect_role(self, line: str) -> Optional[str]:
        """
        Returns 'user' or 'assistant' if the line starts
        with a recognized role indicator.
        Returns None otherwise.
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

        Examples:
            "User: Hello there"   -> "Hello there"
            "A: That's correct"   -> "That's correct"
            "Assistant: Sure"     -> "Sure"
        """

        return re.sub(
            r"^(user|you|me|human|u|h|assistant|a|ai|"
            r"bot|gpt|chatgpt|claude|gemini)\s*[:\-]\s*",
            "",
            line,
            flags=re.IGNORECASE,
        ).strip()