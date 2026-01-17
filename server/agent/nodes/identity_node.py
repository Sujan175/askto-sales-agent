"""Identity verification node - collects phone number and verifies/creates user."""

import re
from typing import Literal

from langchain_core.runnables import RunnableConfig
from loguru import logger

from ..state import AgentState


def extract_phone_number(text: str) -> str | None:
    """Extract phone number from user input."""
    # Remove common separators and spaces
    cleaned = re.sub(r'[\s\-\.\(\)]', '', text)
    
    # Look for phone number patterns (prioritize Indian mobile numbers)
    patterns = [
        r'(?:\+91|91)?([6-9]\d{9})',  # Indian mobile: +91/91 + 10 digits starting with 6-9
        r'([6-9]\d{9})',  # Just 10 digits starting with 6-9
        r'(\d{10})',  # Any 10 consecutive digits (fallback)
    ]
    
    for pattern in patterns:
        match = re.search(pattern, cleaned)
        if match:
            phone = match.group(1) if match.lastindex else match.group(0)
            # Ensure it's exactly 10 digits
            if len(phone) == 10:
                logger.info(f"Extracted phone number: ***{phone[-4:]}")
                return phone
    
    # Also try to find any sequence of 10+ digits and take last 10
    all_digits = re.sub(r'\D', '', text)
    if len(all_digits) >= 10:
        phone = all_digits[-10:]  # Take last 10 digits
        logger.info(f"Extracted phone from digits: ***{phone[-4:]}")
        return phone
    
    return None


def check_identity(state: AgentState) -> Literal["identity", "retrieve_memory"]:
    """Routing function to check if identity verification is needed."""
    if state.get("identity_verified", False):
        return "retrieve_memory"
    return "identity"


async def identity_node(state: AgentState, config: RunnableConfig) -> dict:
    """Handle identity verification flow.
    
    This node:
    1. If no phone number yet: prompts for phone number
    2. If phone provided: extracts and validates it
    3. Looks up user in database
    4. Creates new user if not found
    5. Updates state with user info
    """
    from ..memory import PostgresMemory
    
    current_input = state.get("current_input", "")
    phone_number = state.get("phone_number")
    messages = state.get("messages", [])
    turn_count = state.get("turn_count", 0)
    
    # Get postgres client from config
    postgres: PostgresMemory = config.get("configurable", {}).get("postgres")
    
    logger.info(f"Identity node: input='{current_input[:50] if current_input else '[empty]'}', phone={phone_number}, turn={turn_count}")
    
    # Check if this is the first turn (turn_count == 0 means no previous response yet)
    # Also treat empty input as first turn trigger
    is_first_turn = turn_count == 0 or not current_input
    
    if is_first_turn and not phone_number:
        # First interaction - warm introduction
        response = (
            "Hi there! I'm calling from HDFC Bank. "
            "I wanted to have a quick chat about credit cards. "
            "Do you currently use any credit cards?"
        )
        # Merge with existing messages instead of replacing
        updated_messages = list(messages) + [{"role": "assistant", "content": response}]
        return {
            "current_response": response,
            "messages": updated_messages,
            "turn_count": state.get("turn_count", 0) + 1,
        }
    
    # POC DEMO: Skip phone extraction and use test number
    # Any user response after greeting will proceed with demo phone
    if not phone_number and current_input:
        # Use demo phone number for POC
        phone_number = "9999999999"
        logger.info(f"POC Demo: Using test phone number ***{phone_number[-4:]}")
    
    # We have a phone number - look up or create user
    if phone_number and postgres:
        try:
            user, is_new = await postgres.get_or_create_user(phone_number)
            user_context = await postgres.get_full_user_context(user.id)
            
            logger.info(f"User {'created' if is_new else 'found'}: {user.id}")
            
            # POC Demo: Skip the greeting after identity, let response_node take over
            # Just return identity state, no response here
            return {
                "phone_number": phone_number,
                "identity_verified": True,
                "user_id": str(user.id),
                "user_context": user_context,
                "is_new_user": is_new,
            }
            
        except Exception as e:
            logger.error(f"Error during user lookup: {e}")
            # Continue without persistence - POC Demo mode
            return {
                "phone_number": phone_number,
                "identity_verified": True,
                "is_new_user": True,
                "turn_count": state.get("turn_count", 0) + 1,
            }
    
    # Fallback for POC Demo - just proceed
    logger.warning("Identity node fallback reached")
    return {
        "phone_number": "9999999999",
        "identity_verified": True,
        "is_new_user": True,
    }
