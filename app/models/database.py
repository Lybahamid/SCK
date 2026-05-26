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
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import uuid
from app.config import settings


# Create database engine
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_recycle=3600,
)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# Base class for all models
Base = declarative_base()


def generate_uuid():
    return str(uuid.uuid4())


class Session(Base):
    """
    Stores each imported AI conversation session.
    """
    __tablename__ = "sessions"

    id = Column(
        String(36),
        primary_key=True,
        default=generate_uuid
    )
    title = Column(String(255), nullable=True)
    source_platform = Column(
        Enum("chatgpt", "claude", "gemini", "unknown"),
        nullable=False,
        default="unknown",
    )
    input_method = Column(
        Enum("json_upload", "share_link", "raw_text", "extension"),
        nullable=False,
    )
    message_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
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
        return f"<Session id={self.id} platform={self.source_platform}>"


class Message(Base):
    """
    Stores individual messages within a session.
    """
    __tablename__ = "messages"

    id = Column(
        String(36),
        primary_key=True,
        default=generate_uuid
    )
    session_id = Column(
        String(36),
        ForeignKey("sessions.id"),
        nullable=False
    )
    role = Column(
        Enum("user", "assistant"),
        nullable=False,
    )
    content = Column(Text, nullable=False)
    position = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    session = relationship("Session", back_populates="messages")

    def __repr__(self):
        return (
            f"<Message id={self.id} "
            f"role={self.role} "
            f"position={self.position}>"
        )


class GeneratedContext(Base):
    """
    Stores each generated context document for a session.
    """
    __tablename__ = "generated_contexts"

    id = Column(
        String(36),
        primary_key=True,
        default=generate_uuid
    )
    session_id = Column(
        String(36),
        ForeignKey("sessions.id"),
        nullable=False
    )
    strategy = Column(
        Enum("full", "concise", "technical", "creative"),
        nullable=False,
        default="full",
    )
    target_platform = Column(
        Enum("chatgpt", "claude", "gemini", "generic"),
        nullable=False,
        default="generic",
    )
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    session = relationship("Session", back_populates="contexts")

    def __repr__(self):
        return (
            f"<GeneratedContext id={self.id} "
            f"strategy={self.strategy}>"
        )


def get_db():
    """
    Dependency function that provides a database session.
    Used in FastAPI route dependencies.
    Automatically closes session after request is done.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()