from typing import Dict, Optional, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.models import AgentState, WorldState

def get_default_goals() -> Dict[str, Optional[str]]:
    """Returns a default dictionary of interpersonal goals."""
    return {
        "ally_with": None,
        "undermine": None,
        "gain_influence_over": None,
        "seek_approval_from": None
    }

def update_goals(
    current_goals: Dict[str, Optional[str]],
    emotions: Dict[str, float],
    target_name: str,
    world_stability: int,
    ambition: float
) -> Dict[str, Optional[str]]:
    """
    Updates interpersonal goals based on emotions and world state.
    
    Args:
        current_goals: Current goals dictionary.
        emotions: Emotions toward the target agent.
        target_name: Name of the target agent.
        world_stability: Current stability of the world.
        ambition: The agent's own ambition level.
        
    Returns:
        Updated goals dictionary.
    """
    new_goals = current_goals.copy()
    
    trust = emotions.get("trust", 0.0)
    resentment = emotions.get("resentment", 0.0)
    admiration = emotions.get("admiration", 0.0)
    
    # Ally Rule: Trust > 15
    if trust > 15.0:
        # Only set if not already allied with someone else? 
        # Spec says "ally_with: Optional[str]", implying one ally.
        # If we already have an ally, do we switch? Or keep the stronger one?
        # For simplicity, let's switch if trust is higher? Or just overwrite.
        # Let's overwrite for now as per spec "Form alliances when trust > 15".
        new_goals["ally_with"] = target_name
    elif new_goals["ally_with"] == target_name and trust <= 10.0:
        # Drop ally if trust falls too low (hysteresis)
        new_goals["ally_with"] = None
        
    # Undermine Rule: Resentment > 15
    if resentment > 15.0:
        new_goals["undermine"] = target_name
    elif new_goals["undermine"] == target_name and resentment <= 10.0:
        new_goals["undermine"] = None
        
    # Seek Approval Rule: Admiration > 10
    if admiration > 10.0:
        new_goals["seek_approval_from"] = target_name
    elif new_goals["seek_approval_from"] == target_name and admiration <= 5.0:
        new_goals["seek_approval_from"] = None
        
    # Gain Influence Rule: Ambition > 10 AND Stability < 50
    # This goal is usually about a target, but the condition is about self and world.
    # "Gain influence over" -> who? Probably the target if we are ambitious?
    # Or maybe we pick a weak target?
    # Spec says: "Gain influence when ambition > 10 and stability < 50."
    # It implies gaining influence over *someone*. Let's assume the current target 
    # if they are a rival or just anyone?
    # Let's assume we set this goal towards the target if conditions met.
    if ambition > 10.0 and world_stability < 50:
        new_goals["gain_influence_over"] = target_name
    elif new_goals["gain_influence_over"] == target_name:
        # Clear if conditions no longer met
        if ambition <= 10.0 or world_stability >= 50:
            new_goals["gain_influence_over"] = None
            
    return new_goals
