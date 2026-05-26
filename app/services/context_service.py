from sqlalchemy.orm import Session as DBSession
from sqlalchemy import desc
from app.models.database import GeneratedContext, Session
from app.parsers.base_parser import ParsedSession
from app.engine.context_engine import ContextEngine
import uuid

engine = ContextEngine()


def generate_and_save_context(
    db: DBSession,
    parsed_session: ParsedSession,
    session_id: str,
    strategy: str = "full",
    target_platform: str = "generic",
) -> dict:
    """
    Generates a context document from a parsed session
    and saves it to the database.
    Returns the generated context data.
    """

    # Generate context using the context engine
    result = engine.generate(
        session=parsed_session,
        strategy=strategy,
        target_platform=target_platform,
    )

    # Save generated context to database
    db_context = GeneratedContext(
        id=str(uuid.uuid4()),
        session_id=session_id,
        strategy=strategy,
        target_platform=target_platform,
        content=result["context"],
    )

    db.add(db_context)
    db.commit()
    db.refresh(db_context)

    # Return enriched result with database ID
    result["context_id"] = db_context.id
    result["session_id"] = session_id
    return result


def get_contexts_by_session(
    db: DBSession,
    session_id: str,
) -> list:
    """
    Returns all generated contexts for a given session.
    Most recent first.
    """
    return (
        db.query(GeneratedContext)
        .filter(GeneratedContext.session_id == session_id)
        .order_by(desc(GeneratedContext.created_at))
        .all()
    )


def get_context_by_id(
    db: DBSession,
    context_id: str,
) -> GeneratedContext:
    """
    Returns a single generated context by its ID.
    Returns None if not found.
    """
    return (
        db.query(GeneratedContext)
        .filter(GeneratedContext.id == context_id)
        .first()
    )


def get_latest_context(
    db: DBSession,
    session_id: str,
) -> GeneratedContext:
    """
    Returns the most recently generated context for a session.
    Returns None if no contexts exist for this session.
    """
    return (
        db.query(GeneratedContext)
        .filter(GeneratedContext.session_id == session_id)
        .order_by(desc(GeneratedContext.created_at))
        .first()
    )


def delete_context(
    db: DBSession,
    context_id: str,
) -> bool:
    """
    Deletes a generated context by its ID.
    Returns True if deleted, False if not found.
    """
    db_context = (
        db.query(GeneratedContext)
        .filter(GeneratedContext.id == context_id)
        .first()
    )

    if not db_context:
        return False

    db.delete(db_context)
    db.commit()
    return True


def get_all_contexts(
    db: DBSession,
    page: int = 1,
    limit: int = 10,
) -> dict:
    """
    Returns a paginated list of all generated contexts.
    Most recent first.
    """
    offset = (page - 1) * limit

    total = db.query(GeneratedContext).count()

    contexts = (
        db.query(GeneratedContext)
        .order_by(desc(GeneratedContext.created_at))
        .offset(offset)
        .limit(limit)
        .all()
    )

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "contexts": contexts,
    }