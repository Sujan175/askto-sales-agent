"""Main LangGraph workflow for the sales agent."""

from typing import Literal
from uuid import uuid4

from langgraph.graph import END, StateGraph
from loguru import logger

from .state import AgentState, create_initial_state
from .nodes import (
    identity_node,
    check_identity,
    memory_retriever_node,
    response_node,
    profile_extractor_node,
    memory_writer_node,
)
from .memory import PostgresMemory, RedisMemory


def create_sales_agent() -> StateGraph:
    """Create the LangGraph sales agent workflow.
    
    The workflow follows this pattern:
    
    1. Check if identity is verified
       - No: Go to identity node (collect phone, lookup user)
       - Yes: Continue to memory retrieval
    
    2. Retrieve memory (user context from Redis + PostgreSQL)
    
    3. Generate response (using session-specific prompts)
    
    4. Extract profile info from current turn
    
    5. Write to memory (Redis + PostgreSQL)
    
    6. Return response (or loop back for next turn)
    """
    
    # Create the graph
    graph = StateGraph(AgentState)
    
    # Add nodes
    graph.add_node("identity", identity_node)
    graph.add_node("retrieve_memory", memory_retriever_node)
    graph.add_node("generate_response", response_node)
    graph.add_node("extract_profile", profile_extractor_node)
    graph.add_node("write_memory", memory_writer_node)
    
    # Set entry point with conditional routing
    graph.set_conditional_entry_point(
        check_identity,
        {
            "identity": "identity",
            "retrieve_memory": "retrieve_memory",
        }
    )
    
    # Add edges
    # After identity verification, either end (response ready) or continue
    graph.add_conditional_edges(
        "identity",
        lambda state: "end" if state.get("current_response") and not state.get("identity_verified") else (
            "retrieve_memory" if state.get("identity_verified") else "end"
        ),
        {
            "retrieve_memory": "retrieve_memory",
            "end": END,
        }
    )
    
    # Memory retrieval -> Generate response
    graph.add_edge("retrieve_memory", "generate_response")
    
    # Generate response -> Extract profile
    graph.add_edge("generate_response", "extract_profile")
    
    # Extract profile -> Write memory
    graph.add_edge("extract_profile", "write_memory")
    
    # Write memory -> End (response is ready)
    graph.add_edge("write_memory", END)
    
    return graph.compile()


class SalesAgentRunner:
    """Runner class for the sales agent with memory management."""
    
    def __init__(
        self,
        redis_url: str | None = None,
        database_url: str | None = None,
    ):
        """Initialize the agent runner."""
        self.redis = RedisMemory(redis_url)
        self.postgres = PostgresMemory(database_url)
        self.graph = create_sales_agent()
        self._connected = False
    
    async def connect(self) -> None:
        """Connect to memory stores."""
        if not self._connected:
            await self.redis.connect()
            await self.postgres.connect()
            self._connected = True
            logger.info("SalesAgentRunner connected to memory stores")
    
    async def disconnect(self) -> None:
        """Disconnect from memory stores."""
        if self._connected:
            await self.redis.disconnect()
            await self.postgres.disconnect()
            self._connected = False
            logger.info("SalesAgentRunner disconnected from memory stores")
    
    async def start_session(
        self,
        session_type: Literal["discovery", "pitch", "objection"] = "discovery",
    ) -> dict:
        """Start a new conversation session.
        
        Returns initial state with session_id.
        """
        session_id = str(uuid4())
        
        state = create_initial_state(session_type)
        state["session_id"] = session_id
        
        # Store initial session in Redis
        await self.redis.store_session_metadata(
            session_id=session_id,
            user_id=None,
            session_type=session_type,
        )
        
        logger.info(f"Started new {session_type} session: {session_id}")
        
        return {
            "session_id": session_id,
            "session_type": session_type,
            "state": state,
        }
    
    async def process_message(
        self,
        session_id: str,
        user_input: str,
        session_type: Literal["discovery", "pitch", "objection"] = "discovery",
        llm_client = None,
    ) -> dict:
        """Process a user message and return agent response.
        
        Args:
            session_id: The session ID
            user_input: The user's message
            session_type: Type of session (discovery, pitch, objection)
            llm_client: Optional LLM client to use
        
        Returns:
            Dict with response and updated state
        """
        await self.connect()
        
        # Get existing session state from Redis
        session_metadata = await self.redis.get_session_metadata(session_id)
        messages = await self.redis.get_messages(session_id)
        
        # Build current state
        state: AgentState = {
            "messages": messages,
            "phone_number": session_metadata.get("phone_number") if session_metadata else None,
            "identity_verified": session_metadata.get("identity_verified", False) if session_metadata else False,
            "user_id": session_metadata.get("user_id") if session_metadata else None,
            "user_context": None,
            "is_new_user": True,
            "session_id": session_id,
            "session_type": session_type,
            "turn_count": session_metadata.get("turn_count", 0) if session_metadata else 0,
            "current_input": user_input,
            "current_response": None,
            "extracted_info": None,
            "should_end": False,
            "error": None,
        }
        
        # Add user message to state (only if there's actual input)
        if user_input:
            state["messages"].append({"role": "user", "content": user_input})
        
        # Run the graph
        config = {
            "configurable": {
                "postgres": self.postgres,
                "redis": self.redis,
                "llm_client": llm_client,
            }
        }
        
        try:
            logger.info(f"Invoking graph with input: {user_input[:50]}...")
            result = await self.graph.ainvoke(state, config)
            
            response = result.get("current_response", "")
            logger.info(f"Graph returned response: {response[:100] if response else 'None'}...")
            
            # Always update turn_count in Redis
            new_turn_count = result.get("turn_count", state.get("turn_count", 0) + 1)
            await self.redis.update_session_metadata(
                session_id,
                turn_count=new_turn_count,
            )
            
            # Always save messages to Redis (important for conversation continuity)
            if user_input:
                await self.redis.add_message(session_id, "user", user_input)
            if response:
                await self.redis.add_message(session_id, "assistant", response)
            
            # Update Redis with identity info when verified
            if result.get("identity_verified"):
                await self.redis.update_session_metadata(
                    session_id,
                    identity_verified=True,
                    user_id=result.get("user_id"),
                    phone_number=result.get("phone_number"),
                )
            
            # Create PostgreSQL session if user is verified and we don't have one
            if result.get("identity_verified") and result.get("user_id"):
                user_id = result.get("user_id")
                
                # Check if we need to create a DB session
                existing_sessions = await self.postgres.get_user_sessions(
                    user_id, 
                    session_type=session_type,
                    limit=1
                )
                
                # Create new DB session if this is a new conversation
                if result.get("turn_count", 0) <= 1:
                    from uuid import UUID
                    db_session = await self.postgres.create_session(
                        user_id=UUID(user_id) if isinstance(user_id, str) else user_id,
                        session_type=session_type,
                    )
                    logger.info(f"Created DB session: {db_session.id}")
            
            return {
                "response": response,
                "session_id": session_id,
                "identity_verified": result.get("identity_verified", False),
                "user_id": result.get("user_id"),
                "turn_count": result.get("turn_count", 0),
                "state": result,
            }
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return {
                "response": "I apologize, I'm experiencing a technical issue. Could you please try again?",
                "session_id": session_id,
                "error": str(e),
            }
    
    async def end_session(
        self,
        session_id: str,
        summary: str | None = None,
        outcome: str | None = None,
    ) -> None:
        """End a session and store summary."""
        session_metadata = await self.redis.get_session_metadata(session_id)
        
        if session_metadata and session_metadata.get("user_id"):
            # End the PostgreSQL session
            # Note: We'd need to track the DB session ID to do this properly
            pass
        
        # Clear Redis session data
        await self.redis.clear_session(session_id)
        
        logger.info(f"Ended session: {session_id}")


# Singleton instance for use in Pipecat
_agent_runner: SalesAgentRunner | None = None


async def get_agent_runner() -> SalesAgentRunner:
    """Get or create the singleton agent runner."""
    global _agent_runner
    
    if _agent_runner is None:
        _agent_runner = SalesAgentRunner()
        await _agent_runner.connect()
    
    return _agent_runner
