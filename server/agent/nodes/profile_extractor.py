"""Profile extractor node - extracts user information from conversation turns."""

import json
import os
import re
from typing import Optional

from langchain_core.runnables import RunnableConfig
from loguru import logger

from ..state import AgentState, ExtractedInfo


# Extraction prompt for the LLM
EXTRACTION_PROMPT = """You are an information extraction assistant. Analyze the user's message and extract any relevant information for a credit card sales context.

Extract the following if mentioned:
- name: The user's name
- location: City, area, or region they're from
- work_status: Their employment (employed, freelance, business owner, student, etc.)
- swiggy_frequency: How often they order from Swiggy (e.g., "3-4 times per week", "daily", "occasionally")
- swiggy_amount_per_order: Average amount per Swiggy order in rupees (just the number)
- monthly_food_spend: Total monthly food delivery spend (just the number)
- budget_conscious: true/false if they mention being careful with money
- savings_focused: true/false if they mention saving money as a goal
- financial_concerns: List any financial worries mentioned
- existing_cards: List any credit cards they mention having
- card_satisfaction: Their feelings about current cards (satisfied, unsatisfied, neutral)
- card_pain_points: Any issues with current cards
- objections_raised: Any objections to the credit card offer

Return a JSON object with ONLY the fields that have clear values from the user's message.
Return {} if no relevant information can be extracted.

User message: {message}

JSON output:"""


async def profile_extractor_node(state: AgentState, config: RunnableConfig) -> dict:
    """Extract profile information from the current user message.
    
    This node:
    1. Analyzes the user's input for relevant information
    2. Uses LLM for semantic extraction
    3. Also applies rule-based extraction for common patterns
    4. Returns extracted info for storage
    """
    current_input = state.get("current_input", "")
    
    if not current_input:
        return {}
    
    # Combine rule-based and LLM extraction
    rule_based = extract_with_rules(current_input)
    
    # Use LLM for semantic extraction
    llm_extracted = await extract_with_llm(current_input, config)
    
    # Merge results (LLM takes precedence for semantic understanding)
    extracted = {**rule_based, **llm_extracted}
    
    if extracted:
        logger.info(f"Extracted info: {list(extracted.keys())}")
    
    return {
        "extracted_info": extracted if extracted else None,
    }


def extract_with_rules(text: str) -> dict:
    """Rule-based extraction for common patterns."""
    extracted = {}
    text_lower = text.lower()
    
    # Swiggy frequency patterns
    frequency_patterns = [
        (r'(\d+)\s*(?:to|-)\s*(\d+)\s*times?\s*(?:a|per)\s*week', lambda m: f"{m.group(1)}-{m.group(2)} times per week"),
        (r'(\d+)\s*times?\s*(?:a|per)\s*week', lambda m: f"{m.group(1)} times per week"),
        (r'daily|every\s*day', lambda m: "daily"),
        (r'once\s*(?:a|per)\s*week', lambda m: "once per week"),
        (r'twice\s*(?:a|per)\s*week', lambda m: "twice per week"),
        (r'rarely|occasionally|sometimes', lambda m: "occasionally"),
    ]
    
    for pattern, formatter in frequency_patterns:
        match = re.search(pattern, text_lower)
        if match:
            extracted["swiggy_frequency"] = formatter(match)
            break
    
    # Amount patterns (rupees)
    amount_patterns = [
        r'(?:rs\.?|₹|rupees?)\s*(\d+(?:,\d+)?)',
        r'(\d+(?:,\d+)?)\s*(?:rs\.?|₹|rupees?)',
        r'around\s*(\d+(?:,\d+)?)',
        r'about\s*(\d+(?:,\d+)?)',
        r'(\d{3,})',  # 3+ digit numbers likely amounts
    ]
    
    for pattern in amount_patterns:
        match = re.search(pattern, text_lower)
        if match:
            amount = match.group(1).replace(',', '')
            try:
                amount_int = int(amount)
                if 100 <= amount_int <= 2000:  # Likely per-order amount
                    extracted["swiggy_amount_per_order"] = amount_int
                elif 2000 < amount_int <= 50000:  # Likely monthly spend
                    extracted["monthly_food_spend"] = amount_int
                break
            except ValueError:
                pass
    
    # Budget consciousness
    if any(phrase in text_lower for phrase in [
        'budget', 'careful with', 'save money', 'saving', 'tight', 
        'can\'t afford', 'expensive', 'costly', 'watching my spend'
    ]):
        extracted["budget_conscious"] = True
    
    # Existing cards
    card_patterns = [
        r'(hdfc|icici|sbi|axis|kotak|citi|amex|american express)\s*(?:credit)?\s*card',
        r'have\s*(?:a|an)?\s*(\w+)\s*card',
    ]
    
    cards = []
    for pattern in card_patterns:
        matches = re.findall(pattern, text_lower)
        cards.extend(matches)
    
    if cards:
        extracted["existing_cards"] = list(set(cards))
    
    # Objections
    objection_keywords = {
        'too many cards': 'too_many_cards',
        'annual fee': 'annual_fee_concern',
        'fee': 'fee_concern',
        'overspend': 'overspending_worry',
        'spend too much': 'overspending_worry',
        'not interested': 'not_interested',
        'think about it': 'needs_time',
        'let me think': 'needs_time',
        'complicated': 'complexity_concern',
        'confusing': 'complexity_concern',
    }
    
    objections = []
    for phrase, objection_type in objection_keywords.items():
        if phrase in text_lower:
            objections.append(objection_type)
    
    if objections:
        extracted["objections_raised"] = objections
    
    return extracted


async def extract_with_llm(text: str, config: dict) -> dict:
    """Use LLM for semantic extraction."""
    import httpx
    
    api_key = os.getenv("OPENROUTER_API_KEY")
    model = os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")
    
    if not api_key:
        return {}
    
    prompt = EXTRACTION_PROMPT.format(message=text)
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 500,
                    "temperature": 0,
                },
                timeout=10.0,
            )
            
            if response.status_code != 200:
                logger.warning(f"LLM extraction failed: {response.status_code}")
                return {}
            
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            
            # Parse JSON from response
            # Try to find JSON in the response
            json_match = re.search(r'\{[^{}]*\}', content, re.DOTALL)
            if json_match:
                extracted = json.loads(json_match.group())
                return extracted
            
            return {}
            
    except Exception as e:
        logger.warning(f"LLM extraction error: {e}")
        return {}
