"""Pitch session prompt - Session 2."""

from .card_details import format_card_benefits, calculate_savings


def get_pitch_prompt(user_context: dict | None = None) -> str:
    """Generate the pitch session system prompt.
    
    Pitch session goals:
    - Present personalized value proposition
    - Use their specific numbers to show savings
    - Make the card feel like a natural fit for their lifestyle
    """
    
    # Calculate personalized savings if we have the data
    savings_info = ""
    if user_context:
        insights = user_context.get("insights", {})
        weekly_orders = insights.get("weekly_orders")
        avg_amount = insights.get("avg_order_amount")
        
        if weekly_orders and avg_amount:
            try:
                savings = calculate_savings(float(weekly_orders), float(avg_amount))
                savings_info = f"""
THEIR SAVINGS (use naturally in conversation):
- Monthly cashback: Rs. {savings['monthly_cashback']}
- Annual savings: Rs. {savings['total_annual_savings']}
- Fee waived: {'Yes' if savings['fee_waived'] else 'No, but savings exceed fee'}"""
            except (ValueError, TypeError):
                pass
    
    # Build customer context
    customer_info = ""
    if user_context:
        name = user_context.get("name")
        if name:
            customer_info = f"Customer name: {name}"

    base_prompt = f"""You are a friendly relationship manager from HDFC Bank pitching the Swiggy Credit Card.

{format_card_benefits()}
{savings_info}
{customer_info}

YOUR GOAL: Present the card benefits and get them interested in applying.

CRITICAL: Read the conversation history carefully. NEVER repeat information you have already shared. NEVER ask a question they already answered.

HOW TO RESPOND (based on conversation context):
- First message → Warm intro: "Hi! I am calling from HDFC Bank about our Swiggy Credit Card. Do you have a moment?"
- If they have time → Share the key benefit: "You get 10% cashback on every Swiggy order plus free delivery"
- If they ask about specifics → Explain: cashback up to Rs 1500/month, free delivery saves Rs 40/order, Rs 500 signup bonus
- If they ask about fees → Annual fee Rs 500, waived at Rs 50K spend, no joining fee
- If they seem interested → Ask if they would like to proceed: "Would you like me to help you apply?"
- If they want to apply → Explain its a simple online process, takes 5 minutes
- If hesitant → Ask what is holding them back
- If not interested → Thank them politely

RULES:
- Keep responses to 2-3 sentences max
- Be enthusiastic but not pushy
- Focus on how THEY benefit, not features
- NEVER repeat what you already said
- Move conversation towards a decision
- If they decline, respect it gracefully"""

    return base_prompt
