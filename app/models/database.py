from sqlalchemy import (
    create_engine,
    Column,
    String,
    Text,
    Integer,
    DateTime,
    ForeignKey,
    Enum,
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import uuid

from app.config import settings


# ============================================================================
# DATABASE ENGINE
# ============================================================================

engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_recycle=3600,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()


# ============================================================================
# HELPERS
# ============================================================================

def generate_uuid():
    return str(uuid.uuid4())


def get_db():
    """
    FastAPI dependency that provides a database session.
    Automatically closes session after request completes.
    """
    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()


# ============================================================================
# SESSION MODEL
# ============================================================================

class Session(Base):
    """
    Stores imported AI conversation sessions.
    """

    __tablename__ = "sessions"

    id = Column(
        String(36),
        primary_key=True,
        default=generate_uuid,
    )

    title = Column(
        String(255),
        nullable=True,
    )

    source_platform = Column(
        Enum(
            "chatgpt",
            "claude",
            "gemini",
            "unknown",
            name="source_platform_enum",
        ),
        nullable=False,
        default="unknown",
    )

    input_method = Column(
        Enum(
            "json_upload",
            "share_link",
            "raw_text",
            "extension",
            name="input_method_enum",
        ),
        nullable=False,
    )

    message_count = Column(
        Integer,
        default=0,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    # Relationships
    messages = relationship(
        "Message",
        back_populates="session",
        cascade="all, delete",
        order_by="Message.position",
    )

    contexts = relationship(
        "GeneratedContext",
        back_populates="session",
        cascade="all, delete",
    )

    def __repr__(self):
        return (
            f"<Session "
            f"id={self.id} "
            f"platform={self.source_platform}>"
        )


# ============================================================================
# MESSAGE MODEL
# ============================================================================

class Message(Base):
    """
    Stores individual messages within a session.
    """

    __tablename__ = "messages"

    id = Column(
        String(36),
        primary_key=True,
        default=generate_uuid,
    )

    session_id = Column(
        String(36),
        ForeignKey("sessions.id"),
        nullable=False,
    )

    role = Column(
        Enum(
            "user",
            "assistant",
            name="message_role_enum",
        ),
        nullable=False,
    )

    content = Column(
        Text,
        nullable=False,
    )

    position = Column(
        Integer,
        nullable=False,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
    )

    # Relationships
    session = relationship(
        "Session",
        back_populates="messages",
    )

    def __repr__(self):
        return (
            f"<Message "
            f"id={self.id} "
            f"role={self.role} "
            f"position={self.position}>"
        )


# ============================================================================
# GENERATED CONTEXT MODEL
# ============================================================================

class GeneratedContext(Base):
    """
    Stores generated continuation contexts.
    """

    __tablename__ = "generated_contexts"

    id = Column(
        String(36),
        primary_key=True,
        default=generate_uuid,
    )

    session_id = Column(
        String(36),
        ForeignKey("sessions.id"),
        nullable=False,
    )

    strategy = Column(
        Enum(
            "full",
            "concise",
            "technical",
            "creative",
            name="context_strategy_enum",
        ),
        nullable=False,
        default="full",
    )

    target_platform = Column(
        Enum(
            "chatgpt",
            "claude",
            "gemini",
            "generic",
            name="target_platform_enum",
        ),
        nullable=False,
        default="generic",
    )

    content = Column(
        Text,
        nullable=False,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
    )

    # Relationships
    session = relationship(
        "Session",
        back_populates="contexts",
    )

    def __repr__(self):
        return (
            f"<GeneratedContext "
            f"id={self.id} "
            f"strategy={self.strategy}>"
        )