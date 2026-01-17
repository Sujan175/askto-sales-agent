"""PostgreSQL client for persistent memory storage."""

import hashlib
import os
from datetime import datetime
from typing import Optional
from uuid import UUID

from loguru import logger
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import selectinload

from .models import (
    Base,
    ComputedInsightORM,
    ConversationTurnORM,
    SessionORM,
    UserORM,
    UserProfileORM,
    User,
    UserProfile,
    Session,
    ConversationTurn,
    ComputedInsight,
)


class PostgresMemory:
    """PostgreSQL-based persistent memory for user profiles and history."""
    
    def __init__(self, database_url: Optional[str] = None):
        """Initialize PostgreSQL connection."""
        self.database_url = database_url or os.getenv(
            "DATABASE_URL",
            "postgresql+asyncpg://askto:askto_secret@localhost:5433/askto_memory"
        )
        self._engine = None
        self._session_factory = None
    
    async def connect(self) -> None:
        """Establish database connection and create tables if needed."""
        self._engine = create_async_engine(
            self.database_url,
            echo=False,
            pool_size=5,
            max_overflow=10,
        )
        self._session_factory = async_sessionmaker(
            self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        
        # Create tables if they don't exist
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("Connected to PostgreSQL")
    
    async def disconnect(self) -> None:
        """Close database connection."""
        if self._engine:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None
            logger.info("Disconnected from PostgreSQL")
    
    def get_session(self) -> AsyncSession:
        """Get a new database session."""
        if self._session_factory is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self._session_factory()
    
    @staticmethod
    def hash_phone(phone_number: str) -> str:
        """Hash phone number for storage."""
        # Normalize phone number (remove spaces, dashes, etc.)
        normalized = "".join(c for c in phone_number if c.isdigit())
        return hashlib.sha256(normalized.encode()).hexdigest()
    
    @staticmethod
    def get_last_four(phone_number: str) -> str:
        """Get last 4 digits of phone number."""
        normalized = "".join(c for c in phone_number if c.isdigit())
        return normalized[-4:] if len(normalized) >= 4 else normalized
    
    async def find_user_by_phone(self, phone_number: str) -> Optional[User]:
        """Find user by phone number."""
        phone_hash = self.hash_phone(phone_number)
        
        async with self.get_session() as session:
            result = await session.execute(
                select(UserORM).where(UserORM.phone_number_hash == phone_hash)
            )
            user_orm = result.scalar_one_or_none()
            
            if user_orm:
                return User.model_validate(user_orm)
            return None
    
    async def create_user(self, phone_number: str, name: Optional[str] = None) -> User:
        """Create a new user."""
        phone_hash = self.hash_phone(phone_number)
        last_four = self.get_last_four(phone_number)
        
        async with self.get_session() as session:
            user_orm = UserORM(
                phone_number_hash=phone_hash,
                phone_last_four=last_four,
                name=name,
            )
            session.add(user_orm)
            await session.commit()
            await session.refresh(user_orm)
            
            # Create empty profile
            profile_orm = UserProfileORM(user_id=user_orm.id)
            session.add(profile_orm)
            await session.commit()
            
            logger.info(f"Created new user: {user_orm.id}")
            return User.model_validate(user_orm)
    
    async def get_or_create_user(self, phone_number: str) -> tuple[User, bool]:
        """Get existing user or create new one. Returns (user, is_new)."""
        user = await self.find_user_by_phone(phone_number)
        if user:
            return user, False
        
        user = await self.create_user(phone_number)
        return user, True
    
    async def update_user(self, user_id: UUID, **updates) -> Optional[User]:
        """Update user fields."""
        async with self.get_session() as session:
            await session.execute(
                update(UserORM)
                .where(UserORM.id == user_id)
                .values(**updates)
            )
            await session.commit()
            
            result = await session.execute(
                select(UserORM).where(UserORM.id == user_id)
            )
            user_orm = result.scalar_one_or_none()
            return User.model_validate(user_orm) if user_orm else None
    
    async def get_user_profile(self, user_id: UUID) -> Optional[UserProfile]:
        """Get user's profile."""
        async with self.get_session() as session:
            result = await session.execute(
                select(UserProfileORM).where(UserProfileORM.user_id == user_id)
            )
            profile_orm = result.scalar_one_or_none()
            return UserProfile.model_validate(profile_orm) if profile_orm else None
    
    async def update_user_profile(self, user_id: UUID, **updates) -> Optional[UserProfile]:
        """Update user profile fields."""
        async with self.get_session() as session:
            # Check if profile exists
            result = await session.execute(
                select(UserProfileORM).where(UserProfileORM.user_id == user_id)
            )
            profile_orm = result.scalar_one_or_none()
            
            if not profile_orm:
                # Create profile if doesn't exist
                profile_orm = UserProfileORM(user_id=user_id, **updates)
                session.add(profile_orm)
            else:
                # Update existing profile
                for key, value in updates.items():
                    if hasattr(profile_orm, key):
                        # For JSONB fields, merge instead of replace
                        current = getattr(profile_orm, key)
                        if isinstance(current, dict) and isinstance(value, dict):
                            current.update(value)
                            setattr(profile_orm, key, current)
                        elif isinstance(current, list) and isinstance(value, list):
                            # Append unique items for lists
                            for item in value:
                                if item not in current:
                                    current.append(item)
                            setattr(profile_orm, key, current)
                        else:
                            setattr(profile_orm, key, value)
            
            await session.commit()
            await session.refresh(profile_orm)
            return UserProfile.model_validate(profile_orm)
    
    async def create_session(
        self,
        user_id: UUID,
        session_type: str,
    ) -> Session:
        """Create a new conversation session."""
        async with self.get_session() as db_session:
            session_orm = SessionORM(
                user_id=user_id,
                session_type=session_type,
            )
            db_session.add(session_orm)
            await db_session.commit()
            await db_session.refresh(session_orm)
            
            logger.info(f"Created session: {session_orm.id} ({session_type})")
            return Session.model_validate(session_orm)
    
    async def end_session(
        self,
        session_id: UUID,
        summary: Optional[str] = None,
        outcome: Optional[str] = None,
        token_count: int = 0,
    ) -> Optional[Session]:
        """Mark session as ended with summary."""
        async with self.get_session() as db_session:
            await db_session.execute(
                update(SessionORM)
                .where(SessionORM.id == session_id)
                .values(
                    ended_at=datetime.utcnow(),
                    summary=summary,
                    outcome=outcome,
                    token_count=token_count,
                )
            )
            await db_session.commit()
            
            result = await db_session.execute(
                select(SessionORM).where(SessionORM.id == session_id)
            )
            session_orm = result.scalar_one_or_none()
            return Session.model_validate(session_orm) if session_orm else None
    
    async def get_user_sessions(
        self,
        user_id: UUID,
        session_type: Optional[str] = None,
        limit: int = 10,
    ) -> list[Session]:
        """Get user's previous sessions."""
        async with self.get_session() as db_session:
            query = select(SessionORM).where(SessionORM.user_id == user_id)
            
            if session_type:
                query = query.where(SessionORM.session_type == session_type)
            
            query = query.order_by(SessionORM.started_at.desc()).limit(limit)
            
            result = await db_session.execute(query)
            sessions = result.scalars().all()
            return [Session.model_validate(s) for s in sessions]
    
    async def add_conversation_turn(
        self,
        session_id: UUID,
        turn_index: int,
        role: str,
        content: str,
        extracted_entities: Optional[dict] = None,
    ) -> ConversationTurn:
        """Add a conversation turn to a session."""
        async with self.get_session() as db_session:
            turn_orm = ConversationTurnORM(
                session_id=session_id,
                turn_index=turn_index,
                role=role,
                content=content,
                extracted_entities=extracted_entities or {},
            )
            db_session.add(turn_orm)
            await db_session.commit()
            await db_session.refresh(turn_orm)
            return ConversationTurn.model_validate(turn_orm)
    
    async def get_session_turns(
        self,
        session_id: UUID,
        limit: Optional[int] = None,
    ) -> list[ConversationTurn]:
        """Get conversation turns for a session."""
        async with self.get_session() as db_session:
            query = (
                select(ConversationTurnORM)
                .where(ConversationTurnORM.session_id == session_id)
                .order_by(ConversationTurnORM.turn_index)
            )
            
            if limit:
                query = query.limit(limit)
            
            result = await db_session.execute(query)
            turns = result.scalars().all()
            return [ConversationTurn.model_validate(t) for t in turns]
    
    async def store_insight(
        self,
        user_id: UUID,
        insight_type: str,
        insight_key: str,
        insight_value: str,
        numeric_value: Optional[float] = None,
        confidence: float = 1.0,
        session_id: Optional[UUID] = None,
    ) -> ComputedInsight:
        """Store or update a computed insight."""
        async with self.get_session() as db_session:
            # Check for existing insight
            result = await db_session.execute(
                select(ComputedInsightORM).where(
                    ComputedInsightORM.user_id == user_id,
                    ComputedInsightORM.insight_type == insight_type,
                    ComputedInsightORM.insight_key == insight_key,
                )
            )
            insight_orm = result.scalar_one_or_none()
            
            if insight_orm:
                # Update existing
                insight_orm.insight_value = insight_value
                insight_orm.numeric_value = numeric_value
                insight_orm.confidence = confidence
                if session_id:
                    insight_orm.derived_from_session_id = session_id
            else:
                # Create new
                insight_orm = ComputedInsightORM(
                    user_id=user_id,
                    insight_type=insight_type,
                    insight_key=insight_key,
                    insight_value=insight_value,
                    numeric_value=numeric_value,
                    confidence=confidence,
                    derived_from_session_id=session_id,
                )
                db_session.add(insight_orm)
            
            await db_session.commit()
            await db_session.refresh(insight_orm)
            return ComputedInsight.model_validate(insight_orm)
    
    async def get_user_insights(
        self,
        user_id: UUID,
        insight_type: Optional[str] = None,
    ) -> list[ComputedInsight]:
        """Get computed insights for a user."""
        async with self.get_session() as db_session:
            query = select(ComputedInsightORM).where(
                ComputedInsightORM.user_id == user_id
            )
            
            if insight_type:
                query = query.where(ComputedInsightORM.insight_type == insight_type)
            
            result = await db_session.execute(query)
            insights = result.scalars().all()
            return [ComputedInsight.model_validate(i) for i in insights]
    
    async def get_full_user_context(self, user_id: UUID) -> dict:
        """Get complete user context for agent consumption."""
        user = None
        profile = None
        insights = []
        recent_sessions = []
        
        async with self.get_session() as db_session:
            # Get user with profile
            result = await db_session.execute(
                select(UserORM)
                .options(selectinload(UserORM.profile))
                .where(UserORM.id == user_id)
            )
            user_orm = result.scalar_one_or_none()
            
            if user_orm:
                user = User.model_validate(user_orm)
                if user_orm.profile:
                    profile = UserProfile.model_validate(user_orm.profile)
        
        # Get insights and sessions
        if user:
            insights = await self.get_user_insights(user_id)
            recent_sessions = await self.get_user_sessions(user_id, limit=5)
        
        return {
            "user": user.model_dump() if user else None,
            "profile": profile.model_dump() if profile else None,
            "insights": [i.model_dump() for i in insights],
            "recent_sessions": [s.model_dump() for s in recent_sessions],
        }
