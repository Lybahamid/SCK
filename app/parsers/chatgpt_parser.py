from app.parsers.base_parser import BaseParser, ParsedMessage, ParsedSession
from typing import List
from datetime import datetime


class ChatGPTParser(BaseParser):
    """
    Parses the official ChatGPT JSON export file.
    ChatGPT exports a conversations.json file from Settings > Data Controls.
    """

    def parse(self, raw_input: dict) -> ParsedSession:
        """
        Accepts a single conversation dict from ChatGPT export.
        ChatGPT export contains a list of conversations.
        This parser handles one conversation at a time.
        """
        try:
            title = raw_input.get("title", "Untitled ChatGPT Conversation")
            messages = self._extract_messages(raw_input)

            return ParsedSession(
                title=title,
                source_platform="chatgpt",
                input_method="json_upload",
                messages=messages,
                message_count=len(messages),
            )

        except Exception as e:
            raise ValueError(f"Failed to parse ChatGPT export: {str(e)}")

    def _extract_messages(self, conversation: dict) -> List[ParsedMessage]:
        """
        ChatGPT export stores messages in a 'mapping' dict.
        Each entry is a node with a message object inside.
        We extract only user and assistant messages in order.
        """
        mapping = conversation.get("mapping", {})
        messages = []
        position = 0

        # Collect all valid messages from mapping
        raw_messages = []
        for node_id, node in mapping.items():
            message = node.get("message")
            if not message:
                continue

            author = message.get("author", {})
            role = author.get("role")

            # Only keep user and assistant messages
            if role not in ("user", "assistant"):
                continue

            content_obj = message.get("content", {})
            parts = content_obj.get("parts", [])

            # Join all parts into one string
            content = " ".join(
                str(part) for part in parts if isinstance(part, str)
            ).strip()

            if not content:
                continue

            # Extract timestamp if available
            timestamp = None
            create_time = message.get("create_time")
            if create_time:
                try:
                    timestamp = datetime.utcfromtimestamp(create_time)
                except Exception:
                    pass

            raw_messages.append({
                "role": role,
                "content": self.clean_content(content),
                "timestamp": timestamp,
                "create_time": create_time or 0,
            })

        # Sort by create_time to preserve conversation order
        raw_messages.sort(key=lambda x: x["create_time"])

        # Build final ParsedMessage list
        for msg in raw_messages:
            messages.append(
                ParsedMessage(
                    role=msg["role"],
                    content=msg["content"],
                    position=position,
                    timestamp=msg["timestamp"],
                )
            )
            position += 1

        return messages