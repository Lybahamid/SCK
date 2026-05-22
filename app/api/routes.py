from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List
import json

from app.parsers.chatgpt_parser import ChatGPTParser
from app.parsers.claude_parser import ClaudeParser
from app.parsers.link_parser import LinkParser
from app.parsers.raw_text_parser import RawTextParser
from app.engine.context_engine import ContextEngine
from app.api.dependencies import get_pagination_params

router = APIRouter()
engine = ContextEngine()


# -----------------------------------------------
# REQUEST AND RESPONSE MODELS
# -----------------------------------------------

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


class ContextRequest(BaseModel):
    session_id: str
    strategy: Optional[str] = "full"
    target_platform: Optional[str] = "generic"


# -----------------------------------------------
# HEALTH
# -----------------------------------------------

@router.get("/health")
async def health():
    return {"status": "healthy"}


# -----------------------------------------------
# PARSE ENDPOINTS
# -----------------------------------------------

@router.post("/parse/upload")
async def parse_upload(
    file: UploadFile = File(...),
    strategy: str = Query(default="full"),
    target_platform: str = Query(default="generic"),
    source_platform: str = Query(default="chatgpt"),
):
    """
    Accepts a JSON export file from ChatGPT or Claude.
    Parses it and generates a context document.
    """
    try:
        # Read and decode file
        content = await file.read()
        try:
            data = json.loads(content.decode("utf-8"))
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=400,
                detail="Invalid JSON file. Please upload a valid export file.",
            )

        # Select correct parser
        if source_platform == "chatgpt":
            parser = ChatGPTParser()
            # ChatGPT export is a list of conversations
            # We take the first one if it is a list
            if isinstance(data, list):
                if not data:
                    raise HTTPException(
                        status_code=400,
                        detail="Export file is empty.",
                    )
                data = data[0]
        elif source_platform == "claude":
            parser = ClaudeParser()
            if isinstance(data, list):
                if not data:
                    raise HTTPException(
                        status_code=400,
                        detail="Export file is empty.",
                    )
                data = data[0]
        else:
            raise HTTPException(
                status_code=400,
                detail="source_platform must be chatgpt or claude.",
            )

        # Parse the session
        session = parser.parse(data)

        # Generate context
        result = engine.generate(
            session=session,
            strategy=strategy,
            target_platform=target_platform,
        )

        return JSONResponse(content={
            "success": True,
            "data": result,
        })

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/parse/link")
async def parse_link(request: LinkParseRequest):
    """
    Accepts a ChatGPT or Claude share link URL.
    Fetches, parses, and generates a context document.
    """
    try:
        parser = LinkParser()
        session = parser.parse(request.url)

        result = engine.generate(
            session=session,
            strategy=request.strategy,
            target_platform=request.target_platform,
        )

        return JSONResponse(content={
            "success": True,
            "data": result,
        })

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/parse/text")
async def parse_text(request: RawTextRequest):
    """
    Accepts raw pasted conversation text.
    Parses and generates a context document.
    """
    try:
        if not request.text.strip():
            raise HTTPException(
                status_code=400,
                detail="Text input cannot be empty.",
            )

        parser = RawTextParser()
        session = parser.parse(request.text)

        # Override platform if provided
        session.source_platform = request.source_platform

        result = engine.generate(
            session=session,
            strategy=request.strategy,
            target_platform=request.target_platform,
        )

        return JSONResponse(content={
            "success": True,
            "data": result,
        })

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/parse/extension")
async def parse_extension(payload: ExtensionPayload):
    """
    Accepts messages captured directly by the browser extension.
    Each message is a dict with role and content keys.
    """
    try:
        if not payload.messages:
            raise HTTPException(
                status_code=400,
                detail="No messages received from extension.",
            )

        # Convert raw dicts to ParsedMessage objects
        from app.parsers.base_parser import ParsedMessage, ParsedSession

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
                    timestamp=None,
                )
            )

        if not parsed_messages:
            raise HTTPException(
                status_code=400,
                detail="No valid messages found in extension payload.",
            )

        session = ParsedSession(
            title=f"Live {payload.source_platform.title()} Session",
            source_platform=payload.source_platform,
            input_method="extension",
            messages=parsed_messages,
            message_count=len(parsed_messages),
        )

        result = engine.generate(
            session=session,
            strategy=payload.strategy,
            target_platform=payload.target_platform,
        )

        return JSONResponse(content={
            "success": True,
            "data": result,
        })

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))