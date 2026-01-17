"""HDFC Swiggy Credit Card details."""

CARD_DETAILS = {
    "name": "HDFC Swiggy Credit Card",
    "bank": "HDFC Bank",
    "partner": "Swiggy",
    
    "benefits": {
        "cashback": {
            "percentage": 10,
            "description": "10% cashback on all Swiggy orders",
            "max_monthly": 1500,  # Rs. 1500 max cashback per month
        },
        "free_delivery": {
            "description": "Free delivery on all Swiggy orders",
            "savings_per_order": 40,  # Average delivery fee
        },
        "signup_bonus": {
            "amount": 500,
            "description": "Rs. 500 welcome bonus on first transaction",
        },
    },
    
    "fees": {
        "annual_fee": 500,
        "waiver_threshold": 50000,  # Annual spend for fee waiver
        "joining_fee": 0,
    },
    
    "eligibility": {
        "min_income": 25000,  # Monthly income
        "min_age": 21,
        "max_age": 60,
    },
}


def format_card_benefits() -> str:
    """Format card benefits for prompt inclusion."""
    return """HDFC SWIGGY CREDIT CARD BENEFITS:
- 10% cashback on all Swiggy orders (up to Rs. 1,500/month)
- Free delivery on every Swiggy order (saves ~Rs. 40 per order)
- Rs. 500 signup bonus on first transaction
- Annual fee: Rs. 500 (waived if you spend Rs. 50,000 annually)
- No joining fee"""


def calculate_savings(
    weekly_orders: float,
    avg_order_amount: float,
) -> dict:
    """Calculate potential savings for a customer."""
    
    weekly_spend = weekly_orders * avg_order_amount
    monthly_spend = weekly_spend * 4.33
    annual_spend = weekly_spend * 52
    
    # Cashback (10%, max Rs. 1500/month)
    monthly_cashback = min(monthly_spend * 0.10, 1500)
    annual_cashback = monthly_cashback * 12
    
    # Delivery savings (Rs. 40 per order)
    monthly_delivery_savings = weekly_orders * 4.33 * 40
    annual_delivery_savings = monthly_delivery_savings * 12
    
    # Total savings
    total_annual_savings = annual_cashback + annual_delivery_savings
    
    # Fee consideration
    annual_fee = 500 if annual_spend < 50000 else 0
    signup_bonus = 500
    
    net_first_year = total_annual_savings - annual_fee + signup_bonus
    net_subsequent_years = total_annual_savings - annual_fee
    
    return {
        "weekly_spend": round(weekly_spend),
        "monthly_spend": round(monthly_spend),
        "annual_spend": round(annual_spend),
        "monthly_cashback": round(monthly_cashback),
        "annual_cashback": round(annual_cashback),
        "monthly_delivery_savings": round(monthly_delivery_savings),
        "annual_delivery_savings": round(annual_delivery_savings),
        "total_annual_savings": round(total_annual_savings),
        "annual_fee": annual_fee,
        "fee_waived": annual_spend >= 50000,
        "net_first_year": round(net_first_year),
        "net_subsequent_years": round(net_subsequent_years),
    }
