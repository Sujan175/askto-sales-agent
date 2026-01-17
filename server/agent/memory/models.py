"""SQLAlchemy and Pydantic models for memory storage."""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    """SQLAlchemy declarative base."""
    pass


class UserORM(Base):
    """User database model."""
    
    __tablename__ = "users"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    phone_number_hash = Column(String(64), unique=True, nullable=False)
    phone_last_four = Column(String(4))
    name = Column(String(255))
    location = Column(String(255))
    work_status = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    profile = relationship("UserProfileORM", back_populates="user", uselist=False)
    sessions = relationship("SessionORM", back_populates="user")
    insights = relationship("ComputedInsightORM", back_populates="user")


class UserProfileORM(Base):
    """User profile database model."""
    
    __tablename__ = "user_profiles"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    spending_patterns = Column(JSONB, default=dict)
    food_habits = Column(JSONB, default=dict)
    financial_goals = Column(JSONB, default=dict)
    current_cards = Column(JSONB, default=dict)
    preferences = Column(JSONB, default=dict)
    pain_points = Column(JSONB, default=list)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    user = relationship("UserORM", back_populates="profile")


class SessionORM(Base):
    """Session database model."""
    
    __tablename__ = "sessions"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    session_type = Column(String(50), nullable=False)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    ended_at = Column(DateTime(timezone=True))
    summary = Column(Text)
    token_count = Column(Integer, default=0)
    outcome = Column(String(50))
    
    user = relationship("UserORM", back_populates="sessions")
    turns = relationship("ConversationTurnORM", back_populates="session")
    insights = relationship("ComputedInsightORM", back_populates="derived_from_session")


class ConversationTurnORM(Base):
    """Conversation turn database model."""
    
    __tablename__ = "conversation_turns"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    session_id = Column(PGUUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    turn_index = Column(Integer, nullable=False)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    extracted_entities = Column(JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    session = relationship("SessionORM", back_populates="turns")


class ComputedInsightORM(Base):
    """Computed insight database model."""
    
    __tablename__ = "computed_insights"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    insight_type = Column(String(100), nullable=False)
    insight_key = Column(String(100), nullable=False)
    insight_value = Column(Text, nullable=False)
    numeric_value = Column(Numeric)
    confidence = Column(Numeric, default=1.0)
    derived_from_session_id = Column(PGUUID(as_uuid=True), ForeignKey("sessions.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    user = relationship("UserORM", back_populates="insights")
    derived_from_session = relationship("SessionORM", back_populates="insights")


# Pydantic models for API/State usage

class User(BaseModel):
    """User Pydantic model."""
    
    id: Optional[UUID] = None
    phone_number_hash: str
    phone_last_four: Optional[str] = None
    name: Optional[str] = None
    location: Optional[str] = None
    work_status: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class UserProfile(BaseModel):
    """User profile Pydantic model."""
    
    id: Optional[UUID] = None
    user_id: UUID
    spending_patterns: dict = Field(default_factory=dict)
    food_habits: dict = Field(default_factory=dict)
    financial_goals: dict = Field(default_factory=dict)
    current_cards: dict = Field(default_factory=dict)
    preferences: dict = Field(default_factory=dict)
    pain_points: list = Field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class Session(BaseModel):
    """Session Pydantic model."""
    
    id: Optional[UUID] = None
    user_id: UUID
    session_type: str
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    summary: Optional[str] = None
    token_count: int = 0
    outcome: Optional[str] = None
    
    class Config:
        from_attributes = True


class ConversationTurn(BaseModel):
    """Conversation turn Pydantic model."""
    
    id: Optional[UUID] = None
    session_id: UUID
    turn_index: int
    role: str
    content: str
    extracted_entities: dict = Field(default_factory=dict)
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ComputedInsight(BaseModel):
    """Computed insight Pydantic model."""
    
    id: Optional[UUID] = None
    user_id: UUID
    insight_type: str
    insight_key: str
    insight_value: str
    numeric_value: Optional[Decimal] = None
    confidence: Decimal = Decimal("1.0")
    derived_from_session_id: Optional[UUID] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
