from sqlalchemy.orm import Session as DBSession
from sqlalchemy import desc
from app.models.database import GeneratedContext
from app.parsers.base_parser import ParsedSession
from app.engine.context_engine import ContextEngine
import uuid


engine = ContextEngine()


# ============================================================================
# GENERATE + SAVE CONTEXT
# ============================================================================

def generate_and_save_context(
    db: DBSession,
    parsed_session: ParsedSession,
    session_id: str,
    strategy: str = "full",
    target_platform: str = "generic",
) -> dict:
    """
    Generates a context document using the ContextEngine
    and saves it to the database.
    """

    # Generate context
    result = engine.generate(
        session=parsed_session,
        strategy=strategy,
        target_platform=target_platform,
    )

    # Save generated context
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

    # Add IDs to response
    result["context_id"] = db_context.id
    result["session_id"] = session_id

    return result


# ============================================================================
# GET CONTEXTS BY SESSION
# ============================================================================

def get_contexts_by_session(
    db: DBSession,
    session_id: str,
) -> list:
    """
    Returns all generated contexts for a session.
    """

    return (
        db.query(GeneratedContext)
        .filter(
            GeneratedContext.session_id == session_id
        )
        .order_by(desc(GeneratedContext.created_at))
        .all()
    )


# ============================================================================
# GET CONTEXT BY ID
# ============================================================================

def get_context_by_id(
    db: DBSession,
    context_id: str,
) -> GeneratedContext | None:
    """
    Returns a generated context by ID.
    """

    return (
        db.query(GeneratedContext)
        .filter(
            GeneratedContext.id == context_id
        )
        .first()
    )


# ============================================================================
# GET LATEST CONTEXT
# ============================================================================

def get_latest_context(
    db: DBSession,
    session_id: str,
) -> GeneratedContext | None:
    """
    Returns the latest generated context for a session.
    """

    return (
        db.query(GeneratedContext)
        .filter(
            GeneratedContext.session_id == session_id
        )
        .order_by(desc(GeneratedContext.created_at))
        .first()
    )


# ============================================================================
# DELETE CONTEXT
# ============================================================================

def delete_context(
    db: DBSession,
    context_id: str,
) -> bool:
    """
    Deletes a generated context by ID.
    """

    db_context = (
        db.query(GeneratedContext)
        .filter(
            GeneratedContext.id == context_id
        )
        .first()
    )

    if not db_context:
        return False

    db.delete(db_context)
    db.commit()

    return True


# ============================================================================
# GET ALL CONTEXTS
# ============================================================================

def get_all_contexts(
    db: DBSession,
    page: int = 1,
    limit: int = 10,
) -> dict:
    """
    Returns paginated generated contexts.
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