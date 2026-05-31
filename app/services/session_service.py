from sqlalchemy.orm import Session as DBSession
from sqlalchemy import desc
from app.models.database import Session, Message, GeneratedContext
from app.models.schemas import SessionCreate, GeneratedContextCreate
from app.parsers.base_parser import ParsedSession
import uuid


def create_session(db: DBSession, parsed_session: ParsedSession) -> Session:
    """
    Saves a parsed session and all its messages to the database.
    Returns the created Session object.
    """
    session_id = str(uuid.uuid4())

    # Create session record
    db_session = Session(
        id=session_id,
        title=parsed_session.title,
        source_platform=parsed_session.source_platform,
        input_method=parsed_session.input_method,
        message_count=parsed_session.message_count,
    )
    db.add(db_session)
    db.flush()

    # Create message records
    for msg in parsed_session.messages:
        db_message = Message(
            id=str(uuid.uuid4()),
            session_id=session_id,
            role=msg.role,
            content=msg.content,
            position=msg.position,
        )
        db.add(db_message)

    db.commit()
    db.refresh(db_session)
    return db_session


def get_session_by_id(db: DBSession, session_id: str) -> Session:
    """
    Retrieves a session by its ID including all messages.
    Returns None if not found.
    """
    return db.query(Session).filter(Session.id == session_id).first()


def get_all_sessions(
    db: DBSession,
    page: int = 1,
    limit: int = 10,
) -> dict:
    """
    Returns a paginated list of all sessions.
    Most recent sessions first.
    """
    offset = (page - 1) * limit

    total = db.query(Session).count()

    sessions = (
        db.query(Session)
        .order_by(desc(Session.created_at))
        .offset(offset)
        .limit(limit)
        .all()
    )

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "sessions": sessions,
    }


def delete_session(db: DBSession, session_id: str) -> bool:
    """
    Deletes a session and all its messages and contexts.
    Returns True if deleted, False if not found.
    """
    db_session = db.query(Session).filter(
        Session.id == session_id
    ).first()

    if not db_session:
        return False

    db.delete(db_session)
    db.commit()
    return True


def search_sessions(
    db: DBSession,
    platform: str = None,
    input_method: str = None,
    page: int = 1,
    limit: int = 10,
) -> dict:
    """
    Searches sessions with optional filters.
    Filters by platform and input method.
    """
    offset = (page - 1) * limit
    query = db.query(Session)

    if platform:
        query = query.filter(Session.source_platform == platform)

    if input_method:
        query = query.filter(Session.input_method == input_method)

    total = query.count()

    sessions = (
        query
        .order_by(desc(Session.created_at))
        .offset(offset)
        .limit(limit)
        .all()
    )

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "sessions": sessions,
    }