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
# HEALTH
# ============================================================================

@router.get("/health")
async def health():
    return {"status": "healthy"}


# ============================================================================
# PARSE ENDPOINTS
# ============================================================================

@router.post("/parse/upload")
async def parse_upload(
    file: UploadFile = File(...),
    strategy: str = Query(default="full"),
    target_platform: str = Query(default="generic"),
    source_platform: str = Query(default="chatgpt"),
    db: DBSession = Depends(get_db),
):
    """
    Accepts a JSON export file from ChatGPT or Claude.
    Parses it, saves the session, generates context,
    saves the generated context, and returns it.
    """

    try:
        # Read uploaded file
        content = await file.read()

        try:
            data = json.loads(content.decode("utf-8"))
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=400,
                detail="Invalid JSON file.",
            )

        # Select parser
        if source_platform == "chatgpt":
            parser = ChatGPTParser()
        elif source_platform == "claude":
            parser = ClaudeParser()
        else:
            raise HTTPException(
                status_code=400,
                detail="source_platform must be chatgpt or claude.",
            )

        # Handle list exports
        if isinstance(data, list):
            if not data:
                raise HTTPException(
                    status_code=400,
                    detail="Export file is empty.",
                )
            data = data[0]

        # Parse conversation
        parsed_session = parser.parse(data)

        # Save session
        db_session = create_session(db, parsed_session)

        # Generate and save context
        result = generate_and_save_context(
            db=db,
            parsed_session=parsed_session,
            session_id=db_session.id,
            strategy=strategy,
            target_platform=target_platform,
        )

        return JSONResponse(
            content={
                "success": True,
                "data": result,
            }
        )

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/parse/link")
async def parse_link(
    request: LinkParseRequest,
    db: DBSession = Depends(get_db),
):
    """
    Accepts a ChatGPT or Claude share link.
    Parses, saves, generates context, and returns it.
    """

    try:
        parser = LinkParser()

        parsed_session = parser.parse(request.url)

        # Save session
        db_session = create_session(db, parsed_session)

        # Generate and save context
        result = generate_and_save_context(
            db=db,
            parsed_session=parsed_session,
            session_id=db_session.id,
            strategy=request.strategy,
            target_platform=request.target_platform,
        )

        return JSONResponse(
            content={
                "success": True,
                "data": result,
            }
        )

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/parse/text")
async def parse_text(
    request: RawTextRequest,
    db: DBSession = Depends(get_db),
):
    """
    Accepts raw pasted conversation text.
    Parses, saves, generates context, and returns it.
    """

    try:
        if not request.text.strip():
            raise HTTPException(
                status_code=400,
                detail="Text input cannot be empty.",
            )

        parser = RawTextParser()

        parsed_session = parser.parse(request.text)

        # Override source platform
        parsed_session.source_platform = request.source_platform

        # Save session
        db_session = create_session(db, parsed_session)

        # Generate and save context
        result = generate_and_save_context(
            db=db,
            parsed_session=parsed_session,
            session_id=db_session.id,
            strategy=request.strategy,
            target_platform=request.target_platform,
        )

        return JSONResponse(
            content={
                "success": True,
                "data": result,
            }
        )

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/parse/extension")
async def parse_extension(
    payload: ExtensionPayload,
    db: DBSession = Depends(get_db),
):
    """
    Accepts messages captured by the browser extension.
    Saves session, generates context, saves context, returns it.
    """

    try:
        if not payload.messages:
            raise HTTPException(
                status_code=400,
                detail="No messages received from extension.",
            )

        parsed_messages = []

        for i, msg in enumerate(payload.messages):

            role = msg.get("role", "").lower()
            content = msg.get("content", "").strip()

            if role not in ("user", "assistant"):
                continue

            if not content:
                continue

            parsed_messages.append(
                ParsedMessage(
                    role=role,
                    content=content,
                    position=i,
                )
            )

        if not parsed_messages:
            raise HTTPException(
                status_code=400,
                detail="No valid messages found.",
            )

        parsed_session = ParsedSession(
            title=f"Live {payload.source_platform.title()} Session",
            source_platform=payload.source_platform,
            input_method="extension",
            messages=parsed_messages,
        )

        # Save session
        db_session = create_session(db, parsed_session)

        # Generate and save context
        result = generate_and_save_context(
            db=db,
            parsed_session=parsed_session,
            session_id=db_session.id,
            strategy=payload.strategy,
            target_platform=payload.target_platform,
        )

        return JSONResponse(
            content={
                "success": True,
                "data": result,
            }
        )

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# SESSION HISTORY ENDPOINTS
# ============================================================================

@router.get("/sessions")
async def list_sessions(
    pagination: dict = Depends(get_pagination_params),
    db: DBSession = Depends(get_db),
):
    """
    Returns paginated session history.
    """

    result = get_all_sessions(
        db=db,
        page=pagination["page"],
        limit=pagination["limit"],
    )

    return {
        "success": True,
        **result,
    }


@router.get("/sessions/{session_id}")
async def get_session(
    session_id: str,
    db: DBSession = Depends(get_db),
):
    """
    Returns a single session including messages.
    """

    session = get_session_by_id(db, session_id)

    if not session:
        raise HTTPException(
            status_code=404,
            detail="Session not found.",
        )

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


@router.get("/sessions/{session_id}/contexts")
async def get_session_contexts(
    session_id: str,
    db: DBSession = Depends(get_db),
):
    """
    Returns all generated contexts for a session.
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


@router.delete("/sessions/{session_id}")
async def remove_session(
    session_id: str,
    db: DBSession = Depends(get_db),
):
    """
    Deletes a session and all associated data.
    """

    deleted = delete_session(db, session_id)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Session not found.",
        )

    return {
        "success": True,
        "message": "Session deleted successfully.",
    }