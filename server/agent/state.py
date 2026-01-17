"""LangGraph state definitions for the sales agent."""

from typing import Annotated, Literal, Optional
from uuid import UUID

from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field
from typing_extensions import TypedDict


class Message(TypedDict):
    """A single message in the conversation."""
    role: Literal["user", "assistant", "system"]
    content: str


class UserContext(BaseModel):
    """User context loaded from memory."""
    
    user_id: Optional[UUID] = None
    name: Optional[str] = None
    phone_last_four: Optional[str] = None
    location: Optional[str] = None
    work_status: Optional[str] = None
    
    # Profile data
    spending_patterns: dict = Field(default_factory=dict)
    food_habits: dict = Field(default_factory=dict)
    financial_goals: dict = Field(default_factory=dict)
    current_cards: dict = Field(default_factory=dict)
    preferences: dict = Field(default_factory=dict)
    pain_points: list = Field(default_factory=list)
    
    # Computed insights
    insights: dict = Field(default_factory=dict)
    
    # Session history
    previous_sessions: list = Field(default_factory=list)
    
    def to_context_string(self) -> str:
        """Convert to a string for LLM context."""
        parts = []
        
        if self.name:
            parts.append(f"Customer Name: {self.name}")
        if self.location:
            parts.append(f"Location: {self.location}")
        if self.work_status:
            parts.append(f"Work Status: {self.work_status}")
        
        if self.spending_patterns:
            parts.append(f"Spending Patterns: {self.spending_patterns}")
        if self.food_habits:
            parts.append(f"Food Habits: {self.food_habits}")
        if self.financial_goals:
            parts.append(f"Financial Goals: {self.financial_goals}")
        if self.current_cards:
            parts.append(f"Current Cards: {self.current_cards}")
        if self.pain_points:
            parts.append(f"Pain Points: {', '.join(self.pain_points)}")
        
        if self.insights:
            insights_str = "\n".join(
                f"  - {k}: {v}" for k, v in self.insights.items()
            )
            parts.append(f"Computed Insights:\n{insights_str}")
        
        if self.previous_sessions:
            sessions_str = "\n".join(
                f"  - {s.get('session_type', 'unknown')} on {s.get('started_at', 'unknown')}: {s.get('summary', 'No summary')}"
                for s in self.previous_sessions[:3]
            )
            parts.append(f"Previous Conversations:\n{sessions_str}")
        
        return "\n".join(parts) if parts else "No previous context available."


class ExtractedInfo(BaseModel):
    """Information extracted from current turn."""
    
    # Basic info
    name: Optional[str] = None
    location: Optional[str] = None
    work_status: Optional[str] = None
    
    # Spending
    swiggy_frequency: Optional[str] = None  # e.g., "3-4 times per week"
    swiggy_amount_per_order: Optional[float] = None  # e.g., 350
    monthly_food_spend: Optional[float] = None
    
    # Financial
    budget_conscious: Optional[bool] = None
    savings_focused: Optional[bool] = None
    financial_concerns: list[str] = Field(default_factory=list)
    
    # Cards
    existing_cards: list[str] = Field(default_factory=list)
    card_satisfaction: Optional[str] = None
    card_pain_points: list[str] = Field(default_factory=list)
    
    # Objections
    objections_raised: list[str] = Field(default_factory=list)
    
    # Any other relevant info
    other: dict = Field(default_factory=dict)


class AgentState(TypedDict):
    """Main state for the LangGraph sales agent."""
    
    # Conversation messages - uses add_messages reducer for proper handling
    messages: Annotated[list[Message], add_messages]
    
    # Identity
    phone_number: Optional[str]
    identity_verified: bool
    
    # User context
    user_id: Optional[str]  # UUID as string for serialization
    user_context: Optional[dict]  # UserContext as dict
    is_new_user: bool
    
    # Session
    session_id: Optional[str]  # UUID as string
    session_type: Literal["discovery", "pitch", "objection"]
    turn_count: int
    
    # Current turn
    current_input: str
    current_response: Optional[str]
    extracted_info: Optional[dict]  # ExtractedInfo as dict
    
    # Control flow
    should_end: bool
    error: Optional[str]


def create_initial_state(
    session_type: Literal["discovery", "pitch", "objection"] = "discovery"
) -> AgentState:
    """Create initial agent state for a new session."""
    return AgentState(
        messages=[],
        phone_number=None,
        identity_verified=False,
        user_id=None,
        user_context=None,
        is_new_user=True,
        session_id=None,
        session_type=session_type,
        turn_count=0,
        current_input="",
        current_response=None,
        extracted_info=None,
        should_end=False,
        error=None,
    )
