from fastapi import (
    APIRouter,
    UploadFile,
    File,
    HTTPException,
    Depends,
    Query,
)
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.orm import Session as DBSession
import json

from app.parsers.chatgpt_parser import ChatGPTParser
from app.parsers.claude_parser import ClaudeParser
from app.parsers.link_parser import LinkParser
from app.parsers.raw_text_parser import RawTextParser
from app.parsers.base_parser import ParsedMessage, ParsedSession

from app.engine.context_engine import ContextEngine
from app.models.database import get_db

from app.services.session_service import (
    create_session,
    get_session_by_id,
    get_all_sessions,
    delete_session,
)

from app.services.context_service import (
    generate_and_save_context,
    get_contexts_by_session,
)

from app.api.dependencies import get_pagination_params

router = APIRouter()
engine = ContextEngine()

# ============================================================================
# REQUEST MODELS
# ============================================================================

class LinkParseRequest(BaseModel):
    url: str
    strategy: Optional[str] = "full"
    target_platform: Optional[str] = "generic"

class RawTextRequest(BaseModel):
    text: str
    source_platform: Optional[str] = "unknown"
    strategy: Optional[str] = "full"
    target_platform: Optional[str] = "generic"

class ExtensionPayload(BaseModel):
    messages: List[dict]
    source_platform: Optional[str] = "unknown"
    strategy: Optional[str] = "full"
    target_platform: Optional[str] = "generic"

# ============================================================================
# HELPERS
# ============================================================================

def _normalize_raw_text(text: str) -> str:
    """
    Normalizes raw pasted text so it behaves consistently whether the caller
    sends actual newline characters or escaped sequences like \\n from curl/JSON.
    """
    if not text:
        return text

    return (
        text.replace("\\r\\n", "\n")
        .replace("\\n", "\n")
        .replace("\\r", "\n")
    )

# ============================================================================
# HEALTH
# ============================================================================

@router.get("/health", tags=["Health"], summary="Health check endpoint")
async def health():
    """
    Health check endpoint.
    
    Returns a simple status response to verify the API is running.
    
    **Response:**
    - 200: API is healthy and ready
    """
    return {"status": "healthy"}

# ============================================================================
# PARSE ENDPOINTS
# ============================================================================

@router.post(
    "/parse/upload",
    tags=["Parsing"],
    summary="Parse JSON export file"
)
async def parse_upload(
    file: UploadFile = File(...),
    strategy: str = Query(default="full"),
    target_platform: str = Query(default="generic"),
    source_platform: str = Query(default="chatgpt"),
    db: DBSession = Depends(get_db),
):
    """
    Parse conversation from JSON export file.

    Upload a JSON export file from ChatGPT or Claude. The file will be parsed,
    the session saved to the database, and a continuation context generated.

    ## Input

    **Query Parameters:**
    - **file** (required): JSON export file from ChatGPT or Claude
    - **source_platform**: Platform the conversation came from (default: chatgpt)
      - `chatgpt`: ChatGPT export format
      - `claude`: Claude export format
    - **strategy**: Context generation strategy (default: full)
      - Rule-based: `full`, `concise`, `technical`, `creative`
      - AI-powered: `full_ai`, `handoff_ai`, `debug_ai`, `code_review_ai`, `documentation_ai`, `design_ai`
    - **target_platform**: Target AI platform for context (default: generic)
      - `chatgpt`: ChatGPT markdown format
      - `claude`: Claude XML tags format
      - `gemini`: Google Gemini format
      - `generic`: Universal markdown format

    ## Output

    Returns generated context with metadata:
    - **context**: The continuation context (main output)
    - **strategy**: Which strategy was used
    - **target_platform**: Which format was applied
    - **source_platform**: Original conversation platform
    - **message_count**: Number of messages in session
    - **title**: Session title if available
    - **session_id**: Unique session ID for future reference

    ## Error Responses

    - **400 Bad Request**: Invalid JSON file or invalid parameters
    - **422 Unprocessable Entity**: File format not recognized
    - **500 Internal Server Error**: Database or processing error

    ## Example

    ```bash
    curl -X POST "http://localhost:8000/api/parse/upload?strategy=full_ai&target_platform=generic&source_platform=chatgpt" \\
      -H "Content-Type: application/json" \\
      -F "file=@export.json"
    ```
    """
    try:
        content = await file.read()
        try:
            data = json.loads(content.decode("utf-8"))
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON file.")

        if source_platform == "chatgpt":
            parser = ChatGPTParser()
        elif source_platform == "claude":
            parser = ClaudeParser()
        else:
            raise HTTPException(status_code=400, detail="source_platform must be chatgpt or claude.")

        if isinstance(data, list):
            if not data:
                raise HTTPException(status_code=400, detail="Export file is empty.")
            data = data[0]

        parsed_session = parser.parse(data)
        db_session = create_session(db, parsed_session)

        result = generate_and_save_context(
            db=db,
            parsed_session=parsed_session,
            session_id=db_session.id,
            strategy=strategy,
            target_platform=target_platform,
        )

        return JSONResponse(content={"success": True, "data": result})

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post(
    "/parse/link",
    tags=["Parsing"],
    summary="Parse shared conversation link"
)
async def parse_link(
    request: LinkParseRequest,
    db: DBSession = Depends(get_db),
):
    """
    Parse conversation from ChatGPT or Claude share link.

    Provides a shareable link URL from ChatGPT or Claude. The conversation
    will be fetched, parsed, saved, and a continuation context generated.

    ## Input

    **Request Body:**
    - **url** (required): Shareable conversation link from ChatGPT or Claude
    - **strategy**: Context generation strategy (default: full)
      - Rule-based: `full`, `concise`, `technical`, `creative`
      - AI-powered: `full_ai`, `handoff_ai`, `debug_ai`, `code_review_ai`, `documentation_ai`, `design_ai`
    - **target_platform**: Target AI platform (default: generic)
      - `chatgpt`: ChatGPT format
      - `claude`: Claude format
      - `gemini`: Gemini format
      - `generic`: Universal markdown

    ## Supported Link Formats

    **ChatGPT:**
    - https://chatgpt.com/share/...
    - https://chat.openai.com/share/...

    **Claude:**
    - https://claude.ai/share/...
    """
    try:
        parser = LinkParser()
        parsed_session = parser.parse(request.url)
        db_session = create_session(db, parsed_session)

        result = generate_and_save_context(
            db=db,
            parsed_session=parsed_session,
            session_id=db_session.id,
            strategy=request.strategy,
            target_platform=request.target_platform,
        )

        return JSONResponse(content={"success": True, "data": result})

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post(
    "/parse/text",
    tags=["Parsing"],
    summary="Parse raw conversation text"
)
async def parse_text(
    request: RawTextRequest,
    db: DBSession = Depends(get_db),
):
    """
    Parse raw conversation text.

    Accepts manually pasted or formatted conversation text. The text is parsed
    to identify user and assistant messages, the session is saved, and a
    continuation context is generated.

    ## Input

    **Request Body:**
    - **text** (required): Raw conversation text
    - **source_platform**: Platform the conversation is from (default: unknown)
      - `chatgpt`, `claude`, `gemini`, `unknown`
    - **strategy**: Context generation strategy (default: full)
      - Rule-based: `full`, `concise`, `technical`, `creative`
      - AI-powered: `full_ai`, `handoff_ai`, `debug_ai`, `code_review_ai`, `documentation_ai`, `design_ai`
    - **target_platform**: Target AI platform (default: generic)
      - `chatgpt`, `claude`, `gemini`, `generic`

    ## Text Format

    The parser recognizes these role labels:
    - **User messages:** User:, You:, Me:, Human:, U:, H:
    - **Assistant messages:** Assistant:, A:, AI:, Bot:, GPT:, ChatGPT:, Claude:, Gemini:
    """
    try:
        normalized_text = _normalize_raw_text(request.text)

        if not normalized_text.strip():
            raise HTTPException(status_code=400, detail="Text input cannot be empty.")

        parser = RawTextParser()
        parsed_session = parser.parse(normalized_text)
        parsed_session.source_platform = request.source_platform

        db_session = create_session(db, parsed_session)

        result = generate_and_save_context(
            db=db,
            parsed_session=parsed_session,
            session_id=db_session.id,
            strategy=request.strategy,
            target_platform=request.target_platform,
        )

        return JSONResponse(content={"success": True, "data": result})

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post(
    "/parse/extension",
    tags=["Parsing"],
    summary="Parse browser extension messages"
)
async def parse_extension(
    payload: ExtensionPayload,
    db: DBSession = Depends(get_db),
):
    """
    Parse conversation from browser extension.

    This endpoint accepts live-captured conversation messages from the SCK browser
    extension, saves the session to the database, and generates a continuation
    context that the user can paste into a new AI session.

    ## Input Format

    **Request Body:**
    - **messages** (required): Array of conversation messages
      - Each message must have: `role` ("user" or "assistant") and `content` (text)
    - **source_platform**: Where the conversation is from (default: unknown)
      - `chatgpt`, `claude`, `gemini`, `unknown`
    - **strategy**: Context generation strategy (default: full)
      - Rule-based: `full`, `concise`, `technical`, `creative`
      - AI-powered: `full_ai`, `handoff_ai`, `debug_ai`, `code_review_ai`, `documentation_ai`, `design_ai`
    - **target_platform**: Target AI platform for the context (default: generic)

    ## Strategy Selection Guide

    **Use `full_ai` (recommended):**
    - For most general conversations
    - Want high-quality intelligent context

    **Use `debug_ai`:**
    - Debugging/troubleshooting conversations
    - Error messages and stack traces present

    **Use `code_review_ai`:**
    - Code review discussions
    - Pull request feedback

    **Use `documentation_ai`:**
    - Writing/editing documentation
    - Need style consistency

    **Use `design_ai`:**
    - System design discussions
    - Architecture decisions

    **Use `full` (rule-based):**
    - Need instant response (< 100ms)
    - Don't want external API calls

    ## Response Structure

    ```json
    {
      "success": true,
      "data": {
        "context": "# Session Continuation Context\n\n...",
        "strategy": "full_ai",
        "target_platform": "generic",
        "source_platform": "chatgpt",
        "message_count": 5,
        "title": "Live ChatGPT Session",
        "session_id": "uuid-here"
      }
    }
    ```
    """
    try:
        if not payload.messages:
            raise HTTPException(status_code=400, detail="No messages received from extension.")

        parsed_messages = []
        for i, msg in enumerate(payload.messages):
            role = msg.get("role", "").lower()
            content = msg.get("content", "").strip()

            if role not in ("user", "assistant") or not content:
                continue

            parsed_messages.append(
                ParsedMessage(role=role, content=content, position=i)
            )

        if not parsed_messages:
            raise HTTPException(status_code=400, detail="No valid messages found.")

        parsed_session = ParsedSession(
            title=f"Live {payload.source_platform.title()} Session",
            source_platform=payload.source_platform,
            input_method="extension",
            messages=parsed_messages,
        )

        db_session = create_session(db, parsed_session)

        result = generate_and_save_context(
            db=db,
            parsed_session=parsed_session,
            session_id=db_session.id,
            strategy=payload.strategy,
            target_platform=payload.target_platform,
        )

        return JSONResponse(content={"success": True, "data": result})

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# SESSION HISTORY ENDPOINTS
# ============================================================================

@router.get(
    "/sessions",
    tags=["Sessions"],
    summary="List all sessions"
)
async def list_sessions(
    pagination: dict = Depends(get_pagination_params),
    db: DBSession = Depends(get_db),
):
    """
    Get paginated list of all sessions.

    Returns a paginated list of all saved conversation sessions with metadata.
    Use pagination parameters to control which sessions are returned.

    ## Query Parameters

    - **page** (optional, default: 1): Page number for pagination
    - **limit** (optional, default: 10): Number of results per page
    """
    result = get_all_sessions(
        db=db,
        page=pagination["page"],
        limit=pagination["limit"],
    )
    return {"success": True, **result}

@router.get(
    "/sessions/{session_id}",
    tags=["Sessions"],
    summary="Get session details"
)
async def get_session(
    session_id: str,
    db: DBSession = Depends(get_db),
):
    """
    Get a single session with all its messages.

    Retrieves complete details of a specific session including metadata and
    the full conversation message transcript.
    """
    session = get_session_by_id(db, session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")

    return {
        "success": True,
        "data": {
            "id": session.id,
            "title": session.title,
            "source_platform": session.source_platform,
            "input_method": session.input_method,
            "message_count": session.message_count,
            "created_at": str(session.created_at),
            "messages": [
                {
                    "id": msg.id,
                    "role": msg.role,
                    "content": msg.content,
                    "position": msg.position,
                }
                for msg in session.messages
            ]
        }
    }

@router.get(
    "/sessions/{session_id}/contexts",
    tags=["Sessions"],
    summary="Get generated contexts"
)
async def get_session_contexts(
    session_id: str,
    db: DBSession = Depends(get_db),
):
    """
    Get all generated contexts for a session.

    Returns all continuation contexts that have been generated for a specific
    session using different strategies and target platforms.
    """
    contexts = get_contexts_by_session(db, session_id)

    return {
        "success": True,
        "contexts": [
            {
                "id": ctx.id,
                "strategy": ctx.strategy,
                "target_platform": ctx.target_platform,
                "content": ctx.content,
                "created_at": str(ctx.created_at),
            }
            for ctx in contexts
        ]
    }

@router.delete(
    "/sessions/{session_id}",
    tags=["Sessions"],
    summary="Delete session"
)
async def remove_session(
    session_id: str,
    db: DBSession = Depends(get_db),
):
    """
    Delete a session and all associated data.

    Permanently removes a session and all its messages and generated contexts
    from the database. **This action cannot be undone.**
    """
    deleted = delete_session(db, session_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found.")

    return {
        "success": True,
        "message": "Session deleted successfully.",
    }