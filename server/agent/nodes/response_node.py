"""Response generation node - generates contextual responses using LLM."""

import os
from typing import Any

from langchain_core.runnables import RunnableConfig
from loguru import logger

from ..state import AgentState
from ..prompts import get_discovery_prompt, get_pitch_prompt, get_objection_prompt


async def response_node(state: AgentState, config: RunnableConfig) -> dict:
    """Generate a response using the LLM with appropriate prompt and context.
    
    This node:
    1. Selects the appropriate prompt based on session type
    2. Injects user context into the prompt
    3. Calls the LLM
    4. Returns the response
    """
    logger.info("=== RESPONSE NODE START ===")
    
    session_type = state.get("session_type", "discovery")
    user_context = state.get("user_context") or {}
    messages = state.get("messages", [])
    current_input = state.get("current_input", "")
    
    # Debug: Log what messages are in state
    logger.info(f"Response node received {len(messages)} messages in state")
    for i, m in enumerate(messages):
        if isinstance(m, dict):
            role = m.get("role", "?")
            content = m.get("content", "")[:60]
        else:
            role = getattr(m, "role", "?")
            content = str(getattr(m, "content", ""))[:60]
        logger.info(f"  State msg [{i}]: {role}: {content}")
    
    # Get the appropriate prompt
    if session_type == "discovery":
        system_prompt = get_discovery_prompt(user_context)
    elif session_type == "pitch":
        system_prompt = get_pitch_prompt(user_context)
    elif session_type == "objection":
        system_prompt = get_objection_prompt(user_context)
    else:
        system_prompt = get_discovery_prompt(user_context)
    
    # Build messages for LLM
    llm_messages = [{"role": "system", "content": system_prompt}]
    
    # Add conversation history (limit to recent messages for token efficiency)
    # Handle both dict and LangChain message objects
    def get_msg_role(m):
        return m.get("role") if isinstance(m, dict) else getattr(m, "role", None)
    
    def get_msg_content(m):
        return m.get("content", "") if isinstance(m, dict) else getattr(m, "content", "")
    
    history_messages = [m for m in messages if get_msg_role(m) in ("user", "assistant", "human", "ai")]
    # Keep last 10 turns for context
    for msg in history_messages[-20:]:
        role = get_msg_role(msg)
        # Normalize LangChain role names
        if role == "human":
            role = "user"
        elif role == "ai":
            role = "assistant"
        llm_messages.append({
            "role": role,
            "content": get_msg_content(msg),
        })
    
    # Add current user input if not already in messages
    last_content = get_msg_content(history_messages[-1]) if history_messages else ""
    if current_input and last_content != current_input:
        llm_messages.append({"role": "user", "content": current_input})
    
    # Debug: Log the conversation being sent to LLM
    logger.info(f"Sending {len(llm_messages)} messages to LLM (including system prompt)")
    for i, msg in enumerate(llm_messages[1:], 1):  # Skip system prompt in log
        content = msg['content'][:80] if len(msg['content']) > 80 else msg['content']
        logger.info(f"  [{i}] {msg['role']}: {content}")
    
    # Get LLM client from config
    llm_client = config.get("configurable", {}).get("llm_client")
    
    if llm_client:
        try:
            response = await call_llm(llm_client, llm_messages)
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            response = "I apologize, I'm having a brief technical issue. Could you repeat that?"
    else:
        # Fallback - use OpenRouter directly
        response = await call_openrouter(llm_messages)
    
    # Merge the new assistant response with existing messages
    updated_messages = list(messages) + [{"role": "assistant", "content": response}]
    
    logger.info(f"Response node returning {len(updated_messages)} messages")
    
    return {
        "current_response": response,
        "messages": updated_messages,
        "turn_count": state.get("turn_count", 0) + 1,
    }


async def call_llm(client: Any, messages: list[dict]) -> str:
    """Call the LLM client."""
    # This will be implemented based on the specific LLM client used
    # For now, using a simple interface
    if hasattr(client, "ainvoke"):
        # LangChain style
        from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
        
        lc_messages = []
        for msg in messages:
            if msg["role"] == "system":
                lc_messages.append(SystemMessage(content=msg["content"]))
            elif msg["role"] == "user":
                lc_messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                lc_messages.append(AIMessage(content=msg["content"]))
        
        response = await client.ainvoke(lc_messages)
        return response.content
    
    # Fallback to OpenRouter
    return await call_openrouter(messages)


async def call_openrouter(messages: list[dict]) -> str:
    """Call OpenRouter API directly."""
    import httpx
    
    api_key = os.getenv("OPENROUTER_API_KEY")
    model = os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")
    
    if not api_key:
        logger.error("OPENROUTER_API_KEY not set")
        return "I apologize, I'm experiencing technical difficulties."
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": messages,
                "max_tokens": 500,
                "temperature": 0.7,
            },
            timeout=30.0,
        )
        
        if response.status_code != 200:
            logger.error(f"OpenRouter error: {response.status_code} - {response.text}")
            return "I apologize, I'm experiencing technical difficulties."
        
        data = response.json()
        return data["choices"][0]["message"]["content"]
