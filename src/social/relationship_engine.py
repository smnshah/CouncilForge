"""
Relationship Engine Module

Handles the logic for updating and querying agent relationships.
"""
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

class Relationship(BaseModel):
    """
    Represents the relationship between two agents.
    """
    trust: int = Field(default=0, ge=-100, le=100)
    resentment: int = Field(default=0, ge=-100, le=100)
    history: List[str] = Field(default_factory=list)

    @property
    def score(self) -> int:
        """Calculates the overall relationship score."""
        return self.trust - self.resentment

# Relational Delta Rules
RELATIONSHIP_DELTAS = {
    "support_agent": {"trust": 10, "resentment": -5},
    "oppose_agent": {"trust": -10, "resentment": 10},
    "negotiate": {"trust": 5, "resentment": 0},
    "request_help_accepted": {"trust": 10, "resentment": 0},
    "request_help_rejected": {"trust": -5, "resentment": 5},
    "trade_successful": {"trust": 7, "resentment": -3},
    "sabotage": {"trust": -25, "resentment": 20},
    "send_message_neutral": {"trust": 1, "resentment": 0},
    "send_message_friendly": {"trust": 3, "resentment": -1},
    "send_message_hostile": {"trust": -3, "resentment": 3},
    # Phase 4 Actions
    "form_alliance": {"trust": 15, "resentment": -5},
    "denounce_agent": {"trust": -15, "resentment": 15},
    "offer_concession": {"trust": 8, "resentment": -5},
    "demand_concession": {"trust": -5, "resentment": 8},
    "accuse_agent": {"trust": -10, "resentment": 10},
    "offer_protection": {"trust": 12, "resentment": -2},
    "spread_rumor": {"trust": -8, "resentment": 8},
    "propose_policy": {"trust": 2, "resentment": 0}, # Slight trust boost for engagement
}

def update_relationship(
    relationship: Relationship,
    action_type: str,
    description: Optional[str] = None
) -> Relationship:
    """
    Updates a relationship based on an action.
    
    Args:
        relationship: The current relationship object.
        action_type: The type of action performed (must match keys in RELATIONSHIP_DELTAS).
        description: Optional description to add to history.
        
    Returns:
        The updated relationship object.
    """
    if action_type not in RELATIONSHIP_DELTAS:
        return relationship

    deltas = RELATIONSHIP_DELTAS[action_type]
    
    # Update trust
    relationship.trust = max(-100, min(100, relationship.trust + deltas["trust"]))
    
    # Update resentment
    relationship.resentment = max(-100, min(100, relationship.resentment + deltas["resentment"]))
    
    if description:
        relationship.history.append(description)
        # Keep history short? Spec says "optional short log". 
        # Let's keep last 10 for now to avoid unbounded growth
        if len(relationship.history) > 10:
            relationship.history.pop(0)
            
    return relationship

def apply_message_effects(
    relationship: Relationship,
    tone: str,
    text: Optional[str] = None
) -> Relationship:
    """
    Applies the effects of a message on a relationship.
    
    Args:
        relationship: The relationship to update.
        tone: The tone of the message ("friendly", "hostile", "neutral").
        text: Optional text of the message for history.
        
    Returns:
        The updated relationship.
    """
    action_map = {
        "friendly": "send_message_friendly",
        "hostile": "send_message_hostile",
        "neutral": "send_message_neutral"
    }
    
    action_type = action_map.get(tone, "send_message_neutral")
    description = f"Received {tone} message: '{text}'" if text else f"Received {tone} message"
    
    return update_relationship(relationship, action_type, description)


def get_relationship_score(relationship: Relationship) -> int:
    """Returns the calculated score for a relationship."""
    return relationship.score
