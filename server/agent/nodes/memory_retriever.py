"""Memory retriever node - fetches relevant context from Redis and PostgreSQL."""

from langchain_core.runnables import RunnableConfig
from loguru import logger

from ..state import AgentState, UserContext


async def memory_retriever_node(state: AgentState, config: RunnableConfig) -> dict:
    """Retrieve relevant memory for the current conversation.
    
    This node:
    1. Fetches user context from PostgreSQL
    2. Gets recent conversation from Redis
    3. Retrieves computed insights
    4. Builds context optimized for the session type
    """
    from ..memory import PostgresMemory, RedisMemory
    
    user_id = state.get("user_id")
    session_type = state.get("session_type", "discovery")
    session_id = state.get("session_id")
    
    if not user_id:
        logger.warning("No user_id in state, skipping memory retrieval")
        return {}
    
    # Get clients from config
    configurable = config.get("configurable", {})
    postgres: PostgresMemory = configurable.get("postgres")
    redis: RedisMemory = configurable.get("redis")
    
    user_context = state.get("user_context") or {}
    
    # Fetch fresh context from PostgreSQL if available
    if postgres:
        try:
            full_context = await postgres.get_full_user_context(user_id)
            user_context.update(full_context)
            logger.debug(f"Loaded user context from PostgreSQL")
        except Exception as e:
            logger.error(f"Error fetching from PostgreSQL: {e}")
    
    # Get recent messages from Redis if available
    recent_messages = []
    if redis and session_id:
        try:
            recent_messages = await redis.get_messages(session_id, limit=10)
            logger.debug(f"Loaded {len(recent_messages)} messages from Redis")
        except Exception as e:
            logger.error(f"Error fetching from Redis: {e}")
    
    # Build optimized context based on session type
    optimized_context = build_session_context(user_context, session_type)
    
    return {
        "user_context": optimized_context,
    }


def build_session_context(user_context: dict, session_type: str) -> dict:
    """Build context optimized for the specific session type.
    
    This is where we implement "intelligent retrieval" - 
    only including relevant information for the current session.
    """
    
    # Start with base user info
    optimized = {
        "user": user_context.get("user"),
        "name": user_context.get("user", {}).get("name") if user_context.get("user") else None,
    }
    
    profile = user_context.get("profile") or {}
    insights = user_context.get("insights", [])
    sessions = user_context.get("recent_sessions", [])
    
    if session_type == "discovery":
        # For discovery, we need minimal context - mainly check if returning user
        optimized["is_returning"] = len(sessions) > 0
        optimized["previous_sessions"] = [
            {
                "session_type": s.get("session_type"),
                "started_at": str(s.get("started_at"))[:10] if s.get("started_at") else None,
                "summary": s.get("summary"),
            }
            for s in sessions[:2]  # Only last 2 sessions
        ]
        
    elif session_type == "pitch":
        # For pitch, we need spending data and computed insights
        optimized["profile"] = {
            "spending_patterns": profile.get("spending_patterns", {}),
            "food_habits": profile.get("food_habits", {}),
            "financial_goals": profile.get("financial_goals", {}),
            "current_cards": profile.get("current_cards", {}),
        }
        
        # Include computed insights for calculations
        optimized["insights"] = {}
        for insight in insights:
            key = insight.get("insight_key")
            value = insight.get("insight_value")
            numeric = insight.get("numeric_value")
            if key:
                optimized["insights"][key] = numeric if numeric else value
        
        # Include discovery session summary if available
        discovery_sessions = [s for s in sessions if s.get("session_type") == "discovery"]
        if discovery_sessions:
            optimized["discovery_summary"] = discovery_sessions[0].get("summary")
        
    elif session_type == "objection":
        # For objection handling, we need everything - but organized
        optimized["profile"] = profile
        
        # Full insights for counter-arguments
        optimized["insights"] = {}
        for insight in insights:
            key = insight.get("insight_key")
            value = insight.get("insight_value")
            numeric = insight.get("numeric_value")
            if key:
                optimized["insights"][key] = numeric if numeric else value
        
        # Previous session summaries for context
        optimized["previous_sessions"] = [
            {
                "session_type": s.get("session_type"),
                "summary": s.get("summary"),
                "outcome": s.get("outcome"),
            }
            for s in sessions[:3]
        ]
        
        # Pain points are critical for objection handling
        optimized["pain_points"] = profile.get("pain_points", [])
        optimized["known_objections"] = profile.get("preferences", {}).get("objections", [])
    
    return optimized
