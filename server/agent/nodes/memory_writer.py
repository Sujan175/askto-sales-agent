"""Memory writer node - stores extracted information to Redis and PostgreSQL."""

from decimal import Decimal
from uuid import UUID

from langchain_core.runnables import RunnableConfig
from loguru import logger

from ..state import AgentState
from ..prompts.card_details import calculate_savings


async def memory_writer_node(state: AgentState, config: RunnableConfig) -> dict:
    """Store extracted information and conversation to memory.
    
    This node:
    1. Stores the current turn to Redis (short-term)
    2. Updates user profile in PostgreSQL with extracted info
    3. Computes and stores derived insights
    4. Stores conversation turn for history
    """
    from ..memory import PostgresMemory, RedisMemory
    
    user_id = state.get("user_id")
    session_id = state.get("session_id")
    current_input = state.get("current_input", "")
    current_response = state.get("current_response", "")
    extracted_info = state.get("extracted_info") or {}
    turn_count = state.get("turn_count", 0)
    
    # Get clients from config
    configurable = config.get("configurable", {})
    postgres: PostgresMemory = configurable.get("postgres")
    redis: RedisMemory = configurable.get("redis")
    
    # Store to Redis (short-term memory)
    if redis and session_id:
        try:
            # Add user message
            if current_input:
                await redis.add_message(session_id, "user", current_input)
            
            # Add assistant response
            if current_response:
                await redis.add_message(session_id, "assistant", current_response)
            
            # Update session metadata
            await redis.update_session_metadata(
                session_id,
                turn_count=turn_count,
                identity_verified=state.get("identity_verified", False),
            )
            
            logger.debug(f"Stored turn {turn_count} to Redis")
            
        except Exception as e:
            logger.error(f"Redis write error: {e}")
    
    # Store to PostgreSQL (persistent memory)
    if postgres and user_id:
        try:
            user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
            session_uuid = UUID(session_id) if session_id and isinstance(session_id, str) else session_id
            
            # Update user profile with extracted info
            if extracted_info:
                await update_user_profile(postgres, user_uuid, extracted_info)
            
            # Store conversation turn
            if session_uuid and (current_input or current_response):
                # Store user turn
                if current_input:
                    await postgres.add_conversation_turn(
                        session_id=session_uuid,
                        turn_index=turn_count * 2 - 1,
                        role="user",
                        content=current_input,
                        extracted_entities=extracted_info,
                    )
                
                # Store assistant turn
                if current_response:
                    await postgres.add_conversation_turn(
                        session_id=session_uuid,
                        turn_index=turn_count * 2,
                        role="assistant",
                        content=current_response,
                    )
            
            # Compute and store insights if we have enough data
            await compute_and_store_insights(postgres, user_uuid, extracted_info, session_uuid)
            
            logger.debug(f"Stored turn {turn_count} to PostgreSQL")
            
        except Exception as e:
            logger.error(f"PostgreSQL write error: {e}")
    
    return {}


async def update_user_profile(postgres, user_id: UUID, extracted: dict) -> None:
    """Update user profile with extracted information."""
    
    # Map extracted fields to profile fields
    profile_updates = {}
    user_updates = {}
    
    # User-level fields
    if extracted.get("name"):
        user_updates["name"] = extracted["name"]
    if extracted.get("location"):
        user_updates["location"] = extracted["location"]
    if extracted.get("work_status"):
        user_updates["work_status"] = extracted["work_status"]
    
    # Update user if needed
    if user_updates:
        await postgres.update_user(user_id, **user_updates)
    
    # Profile-level fields
    if extracted.get("swiggy_frequency") or extracted.get("swiggy_amount_per_order") or extracted.get("monthly_food_spend"):
        spending = {}
        if extracted.get("swiggy_frequency"):
            spending["swiggy_frequency"] = extracted["swiggy_frequency"]
        if extracted.get("swiggy_amount_per_order"):
            spending["avg_order_amount"] = extracted["swiggy_amount_per_order"]
        if extracted.get("monthly_food_spend"):
            spending["monthly_food_spend"] = extracted["monthly_food_spend"]
        profile_updates["spending_patterns"] = spending
    
    if extracted.get("budget_conscious") is not None or extracted.get("savings_focused") is not None:
        goals = {}
        if extracted.get("budget_conscious"):
            goals["budget_conscious"] = True
        if extracted.get("savings_focused"):
            goals["savings_focused"] = True
        if extracted.get("financial_concerns"):
            goals["concerns"] = extracted["financial_concerns"]
        profile_updates["financial_goals"] = goals
    
    if extracted.get("existing_cards") or extracted.get("card_satisfaction"):
        cards = {}
        if extracted.get("existing_cards"):
            cards["cards"] = extracted["existing_cards"]
        if extracted.get("card_satisfaction"):
            cards["satisfaction"] = extracted["card_satisfaction"]
        if extracted.get("card_pain_points"):
            cards["pain_points"] = extracted["card_pain_points"]
        profile_updates["current_cards"] = cards
    
    if extracted.get("objections_raised"):
        profile_updates["pain_points"] = extracted["objections_raised"]
    
    # Update profile if there are changes
    if profile_updates:
        await postgres.update_user_profile(user_id, **profile_updates)


async def compute_and_store_insights(
    postgres,
    user_id: UUID,
    extracted: dict,
    session_id: UUID | None = None,
) -> None:
    """Compute derived insights and store them."""
    
    # Get current profile to compute insights
    profile = await postgres.get_user_profile(user_id)
    if not profile:
        return
    
    spending = profile.spending_patterns or {}
    
    # Try to compute weekly orders
    frequency = extracted.get("swiggy_frequency") or spending.get("swiggy_frequency", "")
    weekly_orders = parse_frequency_to_weekly(frequency)
    
    if weekly_orders:
        await postgres.store_insight(
            user_id=user_id,
            insight_type="spending",
            insight_key="weekly_orders",
            insight_value=str(weekly_orders),
            numeric_value=weekly_orders,
            session_id=session_id,
        )
    
    # Store average order amount
    avg_amount = extracted.get("swiggy_amount_per_order") or spending.get("avg_order_amount")
    if avg_amount:
        await postgres.store_insight(
            user_id=user_id,
            insight_type="spending",
            insight_key="avg_order_amount",
            insight_value=str(avg_amount),
            numeric_value=float(avg_amount),
            session_id=session_id,
        )
    
    # Compute savings potential if we have both values
    if weekly_orders and avg_amount:
        savings = calculate_savings(weekly_orders, float(avg_amount))
        
        # Store computed savings
        for key, value in savings.items():
            if isinstance(value, (int, float)):
                await postgres.store_insight(
                    user_id=user_id,
                    insight_type="computed_savings",
                    insight_key=key,
                    insight_value=str(value),
                    numeric_value=float(value),
                    session_id=session_id,
                )


def parse_frequency_to_weekly(frequency: str) -> float | None:
    """Parse frequency string to weekly order count."""
    if not frequency:
        return None
    
    frequency = frequency.lower()
    
    # Handle range (e.g., "3-4 times per week")
    import re
    range_match = re.search(r'(\d+)\s*(?:to|-)\s*(\d+)', frequency)
    if range_match:
        low, high = int(range_match.group(1)), int(range_match.group(2))
        return (low + high) / 2
    
    # Handle single number
    num_match = re.search(r'(\d+)', frequency)
    if num_match:
        num = int(num_match.group(1))
        if 'week' in frequency:
            return float(num)
        elif 'month' in frequency:
            return num / 4.33
        elif 'day' in frequency:
            return num * 7
        return float(num)  # Assume weekly
    
    # Handle text
    if 'daily' in frequency or 'every day' in frequency:
        return 7.0
    elif 'twice' in frequency and 'week' in frequency:
        return 2.0
    elif 'once' in frequency and 'week' in frequency:
        return 1.0
    elif 'occasionally' in frequency or 'rarely' in frequency:
        return 0.5
    
    return None
