"""Redis client for short-term memory storage."""

import json
import os
from typing import Any, Optional
from uuid import UUID

import redis.asyncio as redis
from loguru import logger


class RedisMemory:
    """Redis-based short-term memory for conversation state."""
    
    # TTL settings
    SESSION_TTL = 60 * 60 * 24  # 24 hours
    CONTEXT_TTL = 60 * 60 * 2   # 2 hours for computed context
    
    def __init__(self, redis_url: Optional[str] = None):
        """Initialize Redis connection."""
        self.redis_url = redis_url or os.getenv(
            "REDIS_URL", 
            "redis://localhost:6379/0"
        )
        self._client: Optional[redis.Redis] = None
    
    async def connect(self) -> None:
        """Establish Redis connection."""
        if self._client is None:
            self._client = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            logger.info("Connected to Redis")
    
    async def disconnect(self) -> None:
        """Close Redis connection."""
        if self._client:
            await self._client.close()
            self._client = None
            logger.info("Disconnected from Redis")
    
    @property
    def client(self) -> redis.Redis:
        """Get Redis client, raising if not connected."""
        if self._client is None:
            raise RuntimeError("Redis not connected. Call connect() first.")
        return self._client
    
    def _session_key(self, session_id: str | UUID) -> str:
        """Generate Redis key for session data."""
        return f"session:{session_id}"
    
    def _messages_key(self, session_id: str | UUID) -> str:
        """Generate Redis key for session messages."""
        return f"session:{session_id}:messages"
    
    def _context_key(self, session_id: str | UUID) -> str:
        """Generate Redis key for computed context."""
        return f"session:{session_id}:context"
    
    def _user_active_session_key(self, user_id: str | UUID) -> str:
        """Generate Redis key for user's active session."""
        return f"user:{user_id}:active_session"
    
    async def store_session_metadata(
        self,
        session_id: str | UUID,
        user_id: str | UUID,
        session_type: str,
        phone_number: Optional[str] = None,
        identity_verified: bool = False,
    ) -> None:
        """Store session metadata in Redis."""
        key = self._session_key(session_id)
        data = {
            "session_id": str(session_id),
            "user_id": str(user_id) if user_id else None,
            "session_type": session_type,
            "phone_number": phone_number,
            "identity_verified": identity_verified,
            "turn_count": 0,
        }
        await self.client.hset(key, mapping={k: json.dumps(v) for k, v in data.items()})
        await self.client.expire(key, self.SESSION_TTL)
        
        # Track active session for user
        if user_id:
            user_key = self._user_active_session_key(user_id)
            await self.client.set(user_key, str(session_id), ex=self.SESSION_TTL)
        
        logger.debug(f"Stored session metadata: {session_id}")
    
    async def get_session_metadata(self, session_id: str | UUID) -> Optional[dict]:
        """Retrieve session metadata from Redis."""
        key = self._session_key(session_id)
        data = await self.client.hgetall(key)
        if not data:
            return None
        return {k: json.loads(v) for k, v in data.items()}
    
    async def update_session_metadata(
        self,
        session_id: str | UUID,
        **updates: Any
    ) -> None:
        """Update specific fields in session metadata."""
        key = self._session_key(session_id)
        if updates:
            await self.client.hset(
                key, 
                mapping={k: json.dumps(v) for k, v in updates.items()}
            )
            await self.client.expire(key, self.SESSION_TTL)
    
    async def add_message(
        self,
        session_id: str | UUID,
        role: str,
        content: str,
    ) -> int:
        """Add a message to the session's message list."""
        key = self._messages_key(session_id)
        message = {"role": role, "content": content}
        count = await self.client.rpush(key, json.dumps(message))
        await self.client.expire(key, self.SESSION_TTL)
        
        # Update turn count
        await self.update_session_metadata(session_id, turn_count=count)
        
        return count
    
    async def get_messages(
        self,
        session_id: str | UUID,
        limit: Optional[int] = None
    ) -> list[dict]:
        """Retrieve messages for a session."""
        key = self._messages_key(session_id)
        if limit:
            messages = await self.client.lrange(key, -limit, -1)
        else:
            messages = await self.client.lrange(key, 0, -1)
        return [json.loads(m) for m in messages]
    
    async def store_context(
        self,
        session_id: str | UUID,
        context: dict
    ) -> None:
        """Store computed context for quick retrieval."""
        key = self._context_key(session_id)
        await self.client.set(key, json.dumps(context), ex=self.CONTEXT_TTL)
    
    async def get_context(self, session_id: str | UUID) -> Optional[dict]:
        """Retrieve computed context."""
        key = self._context_key(session_id)
        data = await self.client.get(key)
        return json.loads(data) if data else None
    
    async def get_user_active_session(self, user_id: str | UUID) -> Optional[str]:
        """Get user's currently active session ID."""
        key = self._user_active_session_key(user_id)
        return await self.client.get(key)
    
    async def clear_session(self, session_id: str | UUID) -> None:
        """Clear all data for a session."""
        keys = [
            self._session_key(session_id),
            self._messages_key(session_id),
            self._context_key(session_id),
        ]
        await self.client.delete(*keys)
        logger.debug(f"Cleared session data: {session_id}")
