from app.parsers.base_parser import BaseParser, ParsedMessage, ParsedSession
from typing import List
from datetime import datetime


class ClaudeParser(BaseParser):
    """
    Parses the official Claude JSON export file.
    Claude exports conversations from Settings > Export Data.
    """

    def parse(self, raw_input: dict) -> ParsedSession:
        """
        Accepts a single conversation dict from Claude export.
        """
        try:
            title = raw_input.get("name", "Untitled Claude Conversation")
            messages = self._extract_messages(raw_input)

            return ParsedSession(
                title=title,
                source_platform="claude",
                input_method="json_upload",
                messages=messages,
                message_count=len(messages),
            )

        except Exception as e:
            raise ValueError(f"Failed to parse Claude export: {str(e)}")

    def _extract_messages(self, conversation: dict) -> List[ParsedMessage]:
        """
        Claude export stores messages in a 'chat_messages' list.
        Each message has a 'sender' field (human or assistant)
        and a 'text' field with the content.
        """
        raw_messages = conversation.get("chat_messages", [])
        messages = []
        position = 0

        for msg in raw_messages:
            sender = msg.get("sender", "")

            # Map Claude roles to unified roles
            if sender == "human":
                role = "user"
            elif sender == "assistant":
                role = "assistant"
            else:
                continue

            # Extract text content
            content = ""
            text = msg.get("text", "")
            if text:
                content = self.clean_content(text)

            if not content:
                continue

            # Extract timestamp
            timestamp = None
            created_at = msg.get("created_at", "")
            if created_at:
                try:
                    timestamp = datetime.fromisoformat(
                        created_at.replace("Z", "+00:00")
                    )
                except Exception:
                    pass

            messages.append(
                ParsedMessage(
                    role=role,
                    content=content,
                    position=position,
                    timestamp=timestamp,
                )
            )
            position += 1

        return messages