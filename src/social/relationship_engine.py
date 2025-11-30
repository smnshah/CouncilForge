"""
Relationship Engine Module

Handles the logic for updating and querying agent relationships.
"""
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
import logging
from src.social.message_parser import parse_message_tone

logger = logging.getLogger(__name__)

class Relationship(BaseModel):
    """
    Represents the relationship between two agents.
    Simplified for Phase 1.5 - trust and resentment only.
    """
    trust: int = Field(default=0, ge=-50, le=50)
    resentment: int = Field(default=0, ge=-50, le=50)

    @property
    def score(self) -> int:
        """Calculates the overall relationship score."""
        return self.trust - self.resentment

# Relational Delta Rules (Phase 1.5 - Simple)
RELATIONSHIP_DELTAS = {
    # Social Actions
    "support_agent": {"trust": 3, "resentment": -2},
    "oppose_agent": {"trust": -3, "resentment": 3},
    "send_message_neutral": {"trust": 1, "resentment": 0},
    "send_message_friendly": {"trust": 5, "resentment": -2},
    "send_message_hostile": {"trust": -5, "resentment": 5},
}

def update_relationship(
    relationship: Relationship,
    action_type: str,
    description: Optional[str] = None  # Kept for compatibility but unused
) -> Relationship:
    """
    Updates a relationship based on an action.
    
    Args:
        relationship: The current relationship object.
        action_type: The type of action performed (must match keys in RELATIONSHIP_DELTAS).
        description: Optional description (unused in Phase 1.5).
        
    Returns:
        The updated relationship object.
    """
    if action_type not in RELATIONSHIP_DELTAS:
        return relationship

    deltas = RELATIONSHIP_DELTAS[action_type]
    
    # Update trust (clamped to -50 to +50)
    relationship.trust = max(-50, min(50, relationship.trust + deltas["trust"]))
    
    # Update resentment (clamped to -50 to +50)
    relationship.resentment = max(-50, min(50, relationship.resentment + deltas["resentment"]))
            
    return relationship

def apply_message_effects(
    relationship: Relationship,
    content: Optional[str] = None
) -> Relationship:
    """
    Applies the effects of a message on a relationship based on its tone.
    
    Args:
        relationship: The current relationship object between two agents.
        content: The content of the message to parse for tone.
        
    Returns:
        The updated relationship object.
    """
    if content is None:
        # If no content, apply a neutral contact effect
        return update_relationship(relationship, "send_message_neutral")

    # Parse tone from content
    tone = parse_message_tone(content)
    
    # Determine the action type based on tone
    action_type = "send_message_neutral"
    if tone == "friendly":
        action_type = "send_message_friendly"
        logger.info(f"Relationship effect: Friendly Message detected from message content.")
    elif tone == "hostile":
        action_type = "send_message_hostile"
        logger.info(f"Relationship effect: Hostile Message detected from message content.")
    else:
        logger.info(f"Relationship effect: Neutral Message detected from message content.")
        
    # Update relationship using the determined action type
    return update_relationship(relationship, action_type)


