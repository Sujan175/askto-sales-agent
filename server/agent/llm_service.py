"""Custom Pipecat LLM service that uses LangGraph agent."""

import asyncio
from typing import AsyncGenerator, Literal
from uuid import uuid4

from loguru import logger
from pipecat.frames.frames import (
    Frame,
    LLMContextFrame,
    LLMFullResponseEndFrame,
    LLMFullResponseStartFrame,
    LLMTextFrame,
    LLMMessagesFrame,
)
from pipecat.processors.frame_processor import FrameDirection
from pipecat.services.llm_service import LLMService
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.openai_llm_context import (
    OpenAILLMContext,
    OpenAILLMContextFrame,
)

from .graph import SalesAgentRunner


class LangGraphLLMService(LLMService):
    """Pipecat LLM service that uses LangGraph sales agent.
    
    This service replaces the standard LLM service in the Pipecat pipeline,
    routing all LLM calls through the LangGraph agent which handles:
    - Identity verification
    - Memory retrieval and storage
    - Session-specific response generation
    - Profile extraction
    """
    
    def __init__(
        self,
        session_type: Literal["discovery", "pitch", "objection"] = "discovery",
        redis_url: str | None = None,
        database_url: str | None = None,
        **kwargs,
    ):
        """Initialize the LangGraph LLM service.
        
        Args:
            session_type: Type of sales session (discovery, pitch, objection)
            redis_url: Redis connection URL
            database_url: PostgreSQL connection URL
        """
        super().__init__(**kwargs)
        
        self.session_type = session_type
        self.agent_runner = SalesAgentRunner(
            redis_url=redis_url,
            database_url=database_url,
        )
        self.session_id: str | None = None
        self._connected = False
    
    async def start(self, frame: Frame):
        """Start the service and connect to memory stores."""
        await super().start(frame)
        
        if not self._connected:
            await self.agent_runner.connect()
            self._connected = True
            
            # Start a new session
            session_data = await self.agent_runner.start_session(self.session_type)
            self.session_id = session_data["session_id"]
            
            logger.info(f"LangGraphLLMService started with session: {self.session_id}")
    
    async def stop(self, frame: Frame):
        """Stop the service and disconnect from memory stores."""
        if self._connected:
            if self.session_id:
                await self.agent_runner.end_session(self.session_id)
            
            await self.agent_runner.disconnect()
            self._connected = False
            
            logger.info("LangGraphLLMService stopped")
        
        await super().stop(frame)
    
    async def _process_context(self, context: LLMContext | OpenAILLMContext) -> AsyncGenerator[Frame, None]:
        """Process the LLM context and generate response frames.
        
        This is the main entry point called by Pipecat when it needs an LLM response.
        
        Args:
            context: Either LLMContext or OpenAILLMContext from the aggregator
        """
        # Ensure we have a session
        if not self.session_id:
            session_data = await self.agent_runner.start_session(self.session_type)
            self.session_id = session_data["session_id"]
        
        # Get the latest user message from context
        # Both LLMContext and OpenAILLMContext have get_messages()
        messages = context.get_messages()
        user_input = ""
        
        logger.debug(f"Context has {len(messages)} messages")
        
        # Find the last user message
        for msg in reversed(messages):
            role = msg.get("role") if isinstance(msg, dict) else getattr(msg, "role", None)
            if role == "user":
                content = msg.get("content", "") if isinstance(msg, dict) else getattr(msg, "content", "")
                # Handle content that might be a list (multimodal)
                if isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict) and item.get("type") == "text":
                            user_input = item.get("text", "")
                            break
                else:
                    user_input = str(content) if content else ""
                break
        
        # For initial greeting, user_input will be empty - that's OK
        logger.info(f"Processing user input: '{user_input[:100] if user_input else '[Initial greeting]'}'...")
        
        # Yield start frame
        yield LLMFullResponseStartFrame()
        
        try:
            # Process through LangGraph agent
            result = await self.agent_runner.process_message(
                session_id=self.session_id,
                user_input=user_input,
                session_type=self.session_type,
            )
            
            response = result.get("response", "")
            
            if response:
                # Yield response as LLM text frame (RTVI will capture this for transcripts)
                yield LLMTextFrame(text=response)
                
                logger.debug(f"Agent response: {response[:100]}...")
            else:
                logger.warning("Empty response from agent")
                yield LLMTextFrame(text="I'm sorry, could you repeat that?")
                
        except Exception as e:
            logger.error(f"Error in LangGraph processing: {e}")
            yield LLMTextFrame(text="I apologize, I'm having a brief technical issue. Could you repeat that?")
        
        # Yield end frame
        yield LLMFullResponseEndFrame()
    
    async def process_frame(self, frame: Frame, direction: FrameDirection):
        """Process incoming frames.
        
        Handles OpenAILLMContextFrame, LLMContextFrame, and LLMMessagesFrame
        to trigger LLM completions through our LangGraph agent.
        """
        await super().process_frame(frame, direction)
        
        context = None
        
        if isinstance(frame, OpenAILLMContextFrame):
            # Handle OpenAI-specific context frames (main path from aggregators)
            logger.info(f"LangGraphLLMService received OpenAILLMContextFrame")
            context = frame.context
        elif isinstance(frame, LLMContextFrame):
            # Handle universal LLM context frames
            logger.info(f"LangGraphLLMService received LLMContextFrame")
            context = frame.context
        elif isinstance(frame, LLMMessagesFrame):
            # Handle deprecated LLMMessagesFrame for backwards compatibility
            logger.info(f"LangGraphLLMService received LLMMessagesFrame with {len(frame.messages)} messages")
            context = LLMContext(frame.messages)
        else:
            # For all other frames, pass through
            await self.push_frame(frame, direction)
        
        if context:
            # Process through our LangGraph agent
            async for response_frame in self._process_context(context):
                await self.push_frame(response_frame, direction)
    
    def set_session_type(self, session_type: Literal["discovery", "pitch", "objection"]):
        """Update the session type (for dynamic switching)."""
        self.session_type = session_type
        logger.info(f"Session type updated to: {session_type}")


class LangGraphContextAggregator:
    """Helper class to manage context for LangGraph integration.
    
    This bridges Pipecat's context aggregation with LangGraph's state management.
    """
    
    def __init__(self, llm_service: LangGraphLLMService):
        self.llm_service = llm_service
        self._messages: list[dict] = []
    
    def add_user_message(self, content: str):
        """Add a user message to the context."""
        self._messages.append({"role": "user", "content": content})
    
    def add_assistant_message(self, content: str):
        """Add an assistant message to the context."""
        self._messages.append({"role": "assistant", "content": content})
    
    def get_messages(self) -> list[dict]:
        """Get all messages in context."""
        return self._messages.copy()
    
    def clear(self):
        """Clear all messages."""
        self._messages = []
