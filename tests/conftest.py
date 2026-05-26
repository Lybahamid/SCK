import pytest
import json
from datetime import datetime
from unittest.mock import MagicMock, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.main import app
from app.models.database import Base, SessionLocal, get_db
from app.parsers.base_parser import ParsedMessage, ParsedSession


# ============================================================================
# DATABASE FIXTURES
# ============================================================================

@pytest.fixture(scope="function")
def test_db():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        db = TestSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield engine
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_client(test_db):
    """FastAPI TestClient with in-memory database."""
    return TestClient(app)


# ============================================================================
# TEST DATA FIXTURES - CHATGPT
# ============================================================================

@pytest.fixture
def sample_chatgpt_data():
    """Valid ChatGPT export JSON format."""
    return {
        "title": "Testing ChatGPT Parser",
        "mapping": {
            "node_1": {
                "message": {
                    "id": "msg_1",
                    "author": {"role": "user"},
                    "create_time": 1704067200,
                    "content": {"content_type": "text", "parts": ["Hello, how can I learn Python?"]}
                }
            },
            "node_2": {
                "message": {
                    "id": "msg_2",
                    "author": {"role": "assistant"},
                    "create_time": 1704067260,
                    "content": {"content_type": "text", "parts": ["Python is a great language. Here are some tips..."]}
                }
            },
            "node_3": {
                "message": {
                    "id": "msg_3",
                    "author": {"role": "user"},
                    "create_time": 1704067320,
                    "content": {"content_type": "text", "parts": ["Can you show me a code example?"]}
                }
            },
            "node_4": {
                "message": {
                    "id": "msg_4",
                    "author": {"role": "assistant"},
                    "create_time": 1704067380,
                    "content": {"content_type": "text", "parts": ["```python\nprint('Hello World')\n```"]}
                }
            }
        }
    }


@pytest.fixture
def chatgpt_data_empty_mapping():
    """ChatGPT export with empty mapping."""
    return {"title": "Empty", "mapping": {}}


@pytest.fixture
def chatgpt_data_single_message():
    """ChatGPT export with only one message (fails validation)."""
    return {
        "title": "Single Message",
        "mapping": {
            "node_1": {
                "message": {
                    "id": "msg_1",
                    "author": {"role": "user"},
                    "create_time": 1704067200,
                    "content": {"content_type": "text", "parts": ["Just one message"]}
                }
            }
        }
    }


@pytest.fixture
def chatgpt_data_no_title():
    """ChatGPT export without title field."""
    return {
        "mapping": {
            "node_1": {
                "message": {
                    "id": "msg_1",
                    "author": {"role": "user"},
                    "create_time": 1704067200,
                    "content": {"content_type": "text", "parts": ["Message 1"]}
                }
            },
            "node_2": {
                "message": {
                    "id": "msg_2",
                    "author": {"role": "assistant"},
                    "create_time": 1704067260,
                    "content": {"content_type": "text", "parts": ["Message 2"]}
                }
            }
        }
    }


@pytest.fixture
def chatgpt_data_null_message():
    """ChatGPT export with null message (should be skipped)."""
    return {
        "title": "With Null",
        "mapping": {
            "node_1": {
                "message": {
                    "id": "msg_1",
                    "author": {"role": "user"},
                    "create_time": 1704067200,
                    "content": {"content_type": "text", "parts": ["Real message"]}
                }
            },
            "node_2": {"message": None},
            "node_3": {
                "message": {
                    "id": "msg_3",
                    "author": {"role": "assistant"},
                    "create_time": 1704067260,
                    "content": {"content_type": "text", "parts": ["Another real message"]}
                }
            }
        }
    }


@pytest.fixture
def chatgpt_data_invalid_role():
    """ChatGPT export with invalid roles (should be skipped)."""
    return {
        "title": "Invalid Roles",
        "mapping": {
            "node_1": {
                "message": {
                    "id": "msg_1",
                    "author": {"role": "user"},
                    "create_time": 1704067200,
                    "content": {"content_type": "text", "parts": ["User message"]}
                }
            },
            "node_2": {
                "message": {
                    "id": "msg_2",
                    "author": {"role": "system"},
                    "create_time": 1704067260,
                    "content": {"content_type": "text", "parts": ["System message (skipped)"]}
                }
            },
            "node_3": {
                "message": {
                    "id": "msg_3",
                    "author": {"role": "assistant"},
                    "create_time": 1704067320,
                    "content": {"content_type": "text", "parts": ["Assistant message"]}
                }
            }
        }
    }


@pytest.fixture
def chatgpt_data_whitespace_content():
    """ChatGPT export with whitespace-only content."""
    return {
        "title": "Whitespace",
        "mapping": {
            "node_1": {
                "message": {
                    "id": "msg_1",
                    "author": {"role": "user"},
                    "create_time": 1704067200,
                    "content": {"content_type": "text", "parts": ["Real message"]}
                }
            },
            "node_2": {
                "message": {
                    "id": "msg_2",
                    "author": {"role": "assistant"},
                    "create_time": 1704067260,
                    "content": {"content_type": "text", "parts": ["   \n\n  \t  "]}
                }
            }
        }
    }


# ============================================================================
# TEST DATA FIXTURES - CLAUDE
# ============================================================================

@pytest.fixture
def sample_claude_data():
    """Valid Claude export JSON format."""
    return {
        "name": "My Claude Conversation",
        "chat_messages": [
            {
                "sender": "human",
                "text": "What is machine learning?",
                "created_at": "2024-01-01T10:00:00Z"
            },
            {
                "sender": "assistant",
                "text": "Machine learning is a subset of artificial intelligence...",
                "created_at": "2024-01-01T10:01:00Z"
            },
            {
                "sender": "human",
                "text": "Can you give me an example?",
                "created_at": "2024-01-01T10:02:00Z"
            },
            {
                "sender": "assistant",
                "text": "Sure! A classic example is email spam filtering...",
                "created_at": "2024-01-01T10:03:00Z"
            }
        ]
    }


@pytest.fixture
def claude_data_empty_messages():
    """Claude export with empty chat_messages."""
    return {"name": "Empty", "chat_messages": []}


@pytest.fixture
def claude_data_single_message():
    """Claude export with only one message."""
    return {
        "name": "Single",
        "chat_messages": [
            {
                "sender": "human",
                "text": "Single message",
                "created_at": "2024-01-01T10:00:00Z"
            }
        ]
    }


@pytest.fixture
def claude_data_invalid_sender():
    """Claude export with invalid sender roles."""
    return {
        "name": "Invalid Sender",
        "chat_messages": [
            {
                "sender": "human",
                "text": "Valid message",
                "created_at": "2024-01-01T10:00:00Z"
            },
            {
                "sender": "bot",
                "text": "Invalid sender (skipped)",
                "created_at": "2024-01-01T10:01:00Z"
            },
            {
                "sender": "assistant",
                "text": "Valid message",
                "created_at": "2024-01-01T10:02:00Z"
            }
        ]
    }


@pytest.fixture
def claude_data_invalid_timestamp():
    """Claude export with invalid timestamp format."""
    return {
        "name": "Invalid Time",
        "chat_messages": [
            {
                "sender": "human",
                "text": "First message",
                "created_at": "2024-01-01T10:00:00Z"
            },
            {
                "sender": "assistant",
                "text": "Invalid timestamp below",
                "created_at": "not-a-date"
            }
        ]
    }


# ============================================================================
# TEST DATA FIXTURES - RAW TEXT
# ============================================================================

@pytest.fixture
def sample_raw_text():
    """Valid raw text conversation format."""
    return """You: What is the capital of France?
Claude: The capital of France is Paris.
You: What is its population?
Claude: As of recent data, Paris has a population of approximately 2.1 million people within the city proper."""


@pytest.fixture
def raw_text_empty():
    """Empty raw text (should fail validation)."""
    return ""


@pytest.fixture
def raw_text_whitespace_only():
    """Whitespace-only raw text."""
    return "   \n\n\t  "


@pytest.fixture
def raw_text_no_roles():
    """Raw text without role patterns (fallback to single user message)."""
    return "Just some text without any role prefixes or patterns."


@pytest.fixture
def raw_text_only_user_messages():
    """Raw text with only user messages."""
    return """You: First message
Me: Second message
User: Third message"""


@pytest.fixture
def raw_text_mixed_roles():
    """Raw text with various role patterns."""
    return """Human: Let's talk about Python
ChatGPT: Sure, what would you like to know?
You: How do I write a loop?
Assistant: Here's an example...
Me: Can I use it in production?
AI: Yes, absolutely."""


# ============================================================================
# TEST DATA FIXTURES - PARSED SESSION
# ============================================================================

def _create_message(role: str, content: str, position: int = 0) -> ParsedMessage:
    """Helper to create ParsedMessage objects."""
    return ParsedMessage(
        role=role,
        content=content,
        position=position,
        timestamp=None
    )


@pytest.fixture
def valid_parsed_session() -> ParsedSession:
    """Valid ParsedSession with multiple messages."""
    return ParsedSession(
        title="Test Session",
        source_platform="chatgpt",
        input_method="json_upload",
        messages=[
            _create_message("user", "First user message", 0),
            _create_message("assistant", "First assistant response", 1),
            _create_message("user", "Second user message", 2),
            _create_message("assistant", "Second assistant response", 3),
        ]
    )


@pytest.fixture
def parsed_session_with_code() -> ParsedSession:
    """ParsedSession containing code blocks."""
    return ParsedSession(
        title="Code Discussion",
        source_platform="claude",
        input_method="raw_text",
        messages=[
            _create_message("user", "How do I write a for loop in Python?", 0),
            _create_message("assistant", "```python\nfor i in range(10):\n    print(i)\n```", 1),
            _create_message("user", "Can you explain this?", 2),
            _create_message("assistant", "This loop iterates from 0 to 9...", 3),
        ]
    )


@pytest.fixture
def parsed_session_with_questions() -> ParsedSession:
    """ParsedSession with interrogative sentences."""
    return ParsedSession(
        title="Q&A Session",
        source_platform="chatgpt",
        input_method="json_upload",
        messages=[
            _create_message("user", "What is Python? Why is it popular?", 0),
            _create_message("assistant", "Python is a programming language...", 1),
            _create_message("user", "Can I use it for web development?", 2),
            _create_message("assistant", "Yes, absolutely. Django and Flask are popular...", 3),
        ]
    )


# ============================================================================
# EXTENSION PAYLOAD FIXTURES
# ============================================================================

@pytest.fixture
def extension_payload_valid():
    """Valid extension payload."""
    return {
        "source_platform": "chatgpt",
        "strategy": "full",
        "target_platform": "claude",
        "messages": [
            {"role": "user", "content": "Hello!"},
            {"role": "assistant", "content": "Hi there!"},
            {"role": "user", "content": "How are you?"},
            {"role": "assistant", "content": "I'm doing well, thanks for asking!"},
        ]
    }


@pytest.fixture
def extension_payload_minimal():
    """Extension payload with minimal required fields."""
    return {
        "source_platform": "claude",
        "messages": [
            {"role": "user", "content": "Test"},
            {"role": "assistant", "content": "Response"},
        ]
    }


# ============================================================================
# MOCK FIXTURES
# ============================================================================

@pytest.fixture
def mock_httpx_success(monkeypatch):
    """Mock successful httpx response."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = """
    <html>
        <div data-message-author-role="user" class="message">User message</div>
        <div data-message-author-role="assistant" class="message">Assistant response</div>
    </html>
    """

    async def mock_get(*args, **kwargs):
        return mock_response

    monkeypatch.setattr("httpx.AsyncClient.get", mock_get)


@pytest.fixture
def mock_httpx_404(monkeypatch):
    """Mock 404 httpx response."""
    mock_response = MagicMock()
    mock_response.status_code = 404

    def raise_for_status():
        raise Exception("404 Not Found")

    mock_response.raise_for_status = raise_for_status

    async def mock_get(*args, **kwargs):
        return mock_response

    monkeypatch.setattr("httpx.AsyncClient.get", mock_get)


# ============================================================================
# PYTEST CONFIGURATION
# ============================================================================

def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "asyncio: mark test as async (deselect with '-m \"not asyncio\"')"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as unit test"
    )
