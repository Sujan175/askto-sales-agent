"""Sales agent prompts for different session types."""

from .card_details import CARD_DETAILS, format_card_benefits
from .discovery_prompt import get_discovery_prompt
from .pitch_prompt import get_pitch_prompt
from .objection_prompt import get_objection_prompt

__all__ = [
    "CARD_DETAILS",
    "format_card_benefits",
    "get_discovery_prompt",
    "get_pitch_prompt", 
    "get_objection_prompt",
]
