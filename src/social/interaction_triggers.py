"""
Interaction Triggers Module

Identifies conditions that should trigger social interactions.
"""
from typing import List, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.models import AgentState, WorldState

def compute_interaction_triggers(
    agent_state: "AgentState",
    world_state: "WorldState",
    recent_interactions: List[str]
) -> List[str]:
    """
    Identifies active triggers for interaction.
    """
    triggers = []
    
    # 1. Being Targeted
    if recent_interactions:
        triggers.append("You have been targeted in recent interactions.")
        
    # 2. Resource Deficits (assuming AgentState has goals or needs)
    # This requires looking at the agent's specific situation.
    # For now, we'll check world resources as a proxy for general scarcity
    if hasattr(world_state, "resource_level") and world_state.resource_level < 30:
        triggers.append("Global resources are critically low.")
        
    if hasattr(world_state, "food") and world_state.food < 30:
        triggers.append("Food supplies are dwindling.")
        
    # 3. Crisis
    if hasattr(world_state, "crisis_level") and world_state.crisis_level > 60:
        triggers.append("The world is in crisis.")
        
    # 4. Relationship Thresholds (checked in decision engine mostly, but can add narrative here)
    # We could check for extreme relationships here if we had access to them easily
    
    # 5. New Messages
    if hasattr(agent_state, "messages_received") and agent_state.messages_received:
        triggers.append("You have received new messages.")
        
    return triggers

def generate_prompt_section_for_interaction_triggers(triggers: List[str]) -> str:
    """
    Formats triggers for the LLM prompt.
    """
    if not triggers:
        return ""
        
    lines = ["Interaction Triggers:"]
    for trigger in triggers:
        lines.append(f"- {trigger}")
        
    return "\n".join(lines)
