import pytest
from datetime import datetime
from unittest.mock import patch

from app.parsers.chatgpt_parser import ChatGPTParser
from app.parsers.claude_parser import ClaudeParser
from app.parsers.link_parser import LinkParser
from app.parsers.raw_text_parser import RawTextParser
from app.parsers.base_parser import ParsedSession, ParsedMessage


# ============================================================================
# CHATGPT PARSER TESTS
# ============================================================================

@pytest.mark.unit
class TestChatGPTParser:

    def setup_method(self):
        self.parser = ChatGPTParser()

    def test_valid_json(self, sample_chatgpt_data):
        result = self.parser.parse(sample_chatgpt_data)

        assert isinstance(result, ParsedSession)
        assert result.title == "Testing ChatGPT Parser"
        assert result.source_platform == "chatgpt"
        assert len(result.messages) == 4
        assert result.messages[0].role == "user"
        assert result.messages[1].role == "assistant"

    def test_empty_mapping(self, chatgpt_data_empty_mapping):
        result = self.parser.parse(chatgpt_data_empty_mapping)
        assert len(result.messages) == 0

    def test_single_message(self, chatgpt_data_single_message):
        result = self.parser.parse(chatgpt_data_single_message)
        assert len(result.messages) == 1

    def test_no_title_uses_default(self, chatgpt_data_no_title):
        result = self.parser.parse(chatgpt_data_no_title)
        assert result.title == "Untitled ChatGPT Conversation"

    def test_null_message_skipped(self, chatgpt_data_null_message):
        result = self.parser.parse(chatgpt_data_null_message)
        assert len(result.messages) == 2

    def test_invalid_role_skipped(self, chatgpt_data_invalid_role):
        result = self.parser.parse(chatgpt_data_invalid_role)

        assert len(result.messages) == 2
        assert all(m.role in ["user", "assistant"] for m in result.messages)

    def test_whitespace_content_skipped(self, chatgpt_data_whitespace_content):
        result = self.parser.parse(chatgpt_data_whitespace_content)

        assert len(result.messages) == 1
        assert result.messages[0].content.strip() != ""

    def test_message_ordering_by_timestamp(self):
        data = {
            "title": "Order Test",
            "mapping": {
                "node_3": {
                    "message": {
                        "author": {"role": "assistant"},
                        "create_time": 1704067320,
                        "content": {"parts": ["Message 3"]}
                    }
                },
                "node_1": {
                    "message": {
                        "author": {"role": "user"},
                        "create_time": 1704067200,
                        "content": {"parts": ["Message 1"]}
                    }
                },
                "node_2": {
                    "message": {
                        "author": {"role": "assistant"},
                        "create_time": 1704067260,
                        "content": {"parts": ["Message 2"]}
                    }
                }
            }
        }

        result = self.parser.parse(data)

        assert result.messages[0].content == "Message 1"
        assert result.messages[1].content == "Message 2"
        assert result.messages[2].content == "Message 3"

    def test_multipart_content_concatenation(self):
        data = {
            "title": "Multipart Test",
            "mapping": {
                "node_1": {
                    "message": {
                        "author": {"role": "user"},
                        "create_time": 1704067200,
                        "content": {"parts": ["Part 1", " ", "Part 2"]}
                    }
                },
                "node_2": {
                    "message": {
                        "author": {"role": "assistant"},
                        "create_time": 1704067260,
                        "content": {"parts": ["Response"]}
                    }
                }
            }
        }

        result = self.parser.parse(data)

        assert "Part 1" in result.messages[0].content
        assert "Part 2" in result.messages[0].content

    def test_invalid_timestamp_handled(self):
        data = {
            "title": "Invalid Time",
            "mapping": {
                "node_1": {
                    "message": {
                        "author": {"role": "user"},
                        "create_time": None,
                        "content": {"parts": ["Message 1"]}
                    }
                },
                "node_2": {
                    "message": {
                        "author": {"role": "assistant"},
                        "create_time": 1704067260,
                        "content": {"parts": ["Message 2"]}
                    }
                }
            }
        }

        result = self.parser.parse(data)
        assert len(result.messages) >= 1

    def test_invalid_json_raises_error(self):
        with pytest.raises(Exception):
            self.parser.parse("not valid json")


# ============================================================================
# CLAUDE PARSER TESTS
# ============================================================================

@pytest.mark.unit
class TestClaudeParser:

    def setup_method(self):
        self.parser = ClaudeParser()

    def test_valid_json(self, sample_claude_data):
        result = self.parser.parse(sample_claude_data)

        assert isinstance(result, ParsedSession)
        assert result.title == "My Claude Conversation"
        assert result.source_platform == "claude"
        assert len(result.messages) == 4

    def test_empty_messages(self, claude_data_empty_messages):
        result = self.parser.parse(claude_data_empty_messages)
        assert len(result.messages) == 0

    def test_single_message(self, claude_data_single_message):
        result = self.parser.parse(claude_data_single_message)
        assert len(result.messages) == 1

    def test_invalid_sender_skipped(self, claude_data_invalid_sender):
        result = self.parser.parse(claude_data_invalid_sender)

        assert len(result.messages) == 2
        assert all(m.role in ["user", "assistant"] for m in result.messages)

    def test_invalid_timestamp_handled(self, claude_data_invalid_timestamp):
        result = self.parser.parse(claude_data_invalid_timestamp)
        assert len(result.messages) >= 1

    def test_iso_timestamp_parsing(self):
        data = {
            "name": "Time Test",
            "chat_messages": [
                {
                    "sender": "human",
                    "text": "Message 1",
                    "created_at": "2024-01-01T10:00:00Z"
                },
                {
                    "sender": "assistant",
                    "text": "Message 2",
                    "created_at": "2024-01-01T10:01:00Z"
                }
            ]
        }

        result = self.parser.parse(data)
        assert len(result.messages) == 2

    def test_sender_mapping(self):
        data = {
            "name": "Role Test",
            "chat_messages": [
                {
                    "sender": "human",
                    "text": "Human message",
                    "created_at": "2024-01-01T10:00:00Z"
                },
                {
                    "sender": "assistant",
                    "text": "Assistant message",
                    "created_at": "2024-01-01T10:01:00Z"
                }
            ]
        }

        result = self.parser.parse(data)

        assert result.messages[0].role == "user"
        assert result.messages[1].role == "assistant"

    def test_empty_text_skipped(self):
        data = {
            "name": "Empty Text Test",
            "chat_messages": [
                {
                    "sender": "human",
                    "text": "Real message",
                    "created_at": "2024-01-01T10:00:00Z"
                },
                {
                    "sender": "assistant",
                    "text": "",
                    "created_at": "2024-01-01T10:01:00Z"
                },
                {
                    "sender": "human",
                    "text": "Another real message",
                    "created_at": "2024-01-01T10:02:00Z"
                }
            ]
        }

        result = self.parser.parse(data)
        assert len(result.messages) >= 2

    def test_missing_name_uses_default(self):
        data = {
            "chat_messages": [
                {
                    "sender": "human",
                    "text": "Message 1",
                    "created_at": "2024-01-01T10:00:00Z"
                },
                {
                    "sender": "assistant",
                    "text": "Message 2",
                    "created_at": "2024-01-01T10:01:00Z"
                }
            ]
        }

        result = self.parser.parse(data)
        assert result.title == "Untitled Claude Conversation"


# ============================================================================
# LINK PARSER TESTS
# ============================================================================

@pytest.mark.unit
class TestLinkParser:

    def setup_method(self):
        self.parser = LinkParser()

    def test_empty_url(self):
        with pytest.raises(Exception):
            self.parser.parse("   ")

    def test_invalid_url_format(self):
        with pytest.raises(Exception):
            self.parser.parse("not-a-valid-url")

    def test_chatgpt_platform_detection(self):
        url = "https://chatgpt.com/share/abc123"
        platform = self.parser._detect_platform(url)

        assert platform == "chatgpt"

    def test_claude_platform_detection(self):
        url = "https://claude.ai/share/abc123"
        platform = self.parser._detect_platform(url)

        assert platform == "claude"

    def test_unknown_platform_detection(self):
        url = "https://example.com/chat"
        platform = self.parser._detect_platform(url)

        assert platform == "unknown"

    @patch("httpx.Client.get")
    def test_network_error_handling(self, mock_get):
        mock_get.side_effect = Exception("Network timeout")

        with pytest.raises(Exception):
            self.parser.parse("https://chatgpt.com/share/test")


# ============================================================================
# RAW TEXT PARSER TESTS
# ============================================================================

@pytest.mark.unit
class TestRawTextParser:

    def setup_method(self):
        self.parser = RawTextParser()

    def test_valid_text(self, sample_raw_text):
        result = self.parser.parse(sample_raw_text)

        assert isinstance(result, ParsedSession)
        assert len(result.messages) >= 2

    def test_empty_text(self, raw_text_empty):
        result = self.parser.parse(raw_text_empty)
        assert len(result.messages) == 1

    def test_whitespace_only(self, raw_text_whitespace_only):
        result = self.parser.parse(raw_text_whitespace_only)
        assert len(result.messages) == 1

    def test_no_roles_fallback(self, raw_text_no_roles):
        result = self.parser.parse(raw_text_no_roles)
        assert len(result.messages) == 1
        assert result.messages[0].role == "user"

    def test_only_user_messages(self, raw_text_only_user_messages):
        result = self.parser.parse(raw_text_only_user_messages)

        assert all(m.role == "user" for m in result.messages)

    def test_mixed_role_patterns(self, raw_text_mixed_roles):
        result = self.parser.parse(raw_text_mixed_roles)

        assert len(result.messages) >= 2

    def test_case_insensitive_role_detection(self):
        text = """YOU: First message
CLAUDE: Response
Assistant: Another response
Human: Yet another"""

        result = self.parser.parse(text)

        assert len(result.messages) >= 2

    def test_multiline_messages(self):
        text = """You: This is a multiline message
with multiple lines
of content
Claude: This is the response
with its own multiple
lines"""

        result = self.parser.parse(text)

        assert len(result.messages) >= 2

    def test_special_characters(self):
        text = """You: What about special chars? !@#$%^&*()
Claude: Here are some: 你好 🎉 émojis"""

        result = self.parser.parse(text)

        assert len(result.messages) >= 2

    def test_windows_line_endings(self):
        text = "You: Message 1\r\nClaude: Response 1\r\nYou: Message 2\r\nClaude: Response 2"

        result = self.parser.parse(text)

        assert len(result.messages) >= 2


# ============================================================================
# BASE PARSER VALIDATION TESTS
# ============================================================================

@pytest.mark.unit
class TestBaseParserValidation:

    def test_valid_parsed_session(self, valid_parsed_session):
        assert valid_parsed_session.message_count == len(valid_parsed_session.messages)

    def test_minimum_message_requirement(self):
        session = ParsedSession(
            title="Single",
            source_platform="test",
            input_method="test",
            messages=[
                ParsedMessage(
                    role="user",
                    content="Only one",
                    position=0,
                )
            ]
        )

        assert session.message_count == 1

    def test_role_enum_validation(self, valid_parsed_session):
        for msg in valid_parsed_session.messages:
            assert msg.role in ["user", "assistant"]

    def test_content_cleaning(self):
        from app.parsers.base_parser import BaseParser

        class DummyParser(BaseParser):
            def parse(self, raw_input):
                pass

        parser = DummyParser()

        cleaned = parser.clean_content("  message with spaces  ")

        assert cleaned == "message with spaces"

    def test_message_count_accuracy(self, valid_parsed_session):
        assert valid_parsed_session.message_count == len(valid_parsed_session.messages)