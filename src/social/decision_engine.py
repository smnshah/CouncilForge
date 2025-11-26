from typing import Dict, List, Any, TYPE_CHECKING, Optional
from collections import Counter
from src.social.emotion_engine import get_emotional_bias

if TYPE_CHECKING:
    from src.core.models import AgentState, WorldState
    from src.social.relationship_engine import Relationship

def get_persona_biases(persona_archetype: str) -> Dict[str, float]:
    """Returns bias modifiers based on archetype."""
    modifiers = {}
    if persona_archetype == "Guardian":
        modifiers["strengthen_infrastructure"] = 0.5
        modifiers["support_agent"] = 0.3
        modifiers["form_alliance"] = 0.3
        modifiers["propose_policy"] = -0.2
    elif persona_archetype == "Visionary":
        modifiers["propose_policy"] = 0.5
        modifiers["negotiate"] = 0.3
        modifiers["improve_resource"] = 0.3
    elif persona_archetype == "Realist":
        modifiers["consume_resource"] = 0.2
        modifiers["trade"] = 0.4
        modifiers["oppose_agent"] = 0.2
    elif persona_archetype == "Idealist":
        modifiers["boost_morale"] = 0.5
        modifiers["support_agent"] = 0.4
        modifiers["offer_concession"] = 0.3
    elif persona_archetype == "Agitator":
        modifiers["oppose_agent"] = 0.5
        modifiers["denounce_agent"] = 0.5
        modifiers["spread_rumor"] = 0.5
        modifiers["sabotage"] = 0.3
    return modifiers

def compute_action_biases(
    agent_state: "AgentState",
    world_state: "WorldState",
    relationships: Dict[str, "Relationship"],
    emotions: Dict[str, float],
    goals: Dict[str, Optional[str]]
) -> Dict[str, float]:
    """
    Computes weighted probabilities for actions based on traits, relationships, emotions, and goals.
    """
    biases = {}
    
    # Base Weights
    SOCIAL_ACTION_BASE = 1.0
    WORLD_ACTION_BASE = 0.25
    
    social_actions = [
        "support_agent", "oppose_agent", "negotiate", "request_help", "trade", "sabotage",
        "form_alliance", "denounce_agent", "offer_concession", "demand_concession",
        "accuse_agent", "offer_protection", "spread_rumor", "propose_policy", "send_message"
    ]
    
    world_actions = [
        "improve_resource", "consume_resource", "boost_morale", "strengthen_infrastructure"
    ]
    
    # Initialize with base weights
    for action in social_actions:
        biases[action] = SOCIAL_ACTION_BASE
        
    for action in world_actions:
        biases[action] = WORLD_ACTION_BASE
        
    # Crisis Override: If crisis is high, boost world actions
    if world_state.crisis_level > 60:
        for action in world_actions:
            biases[action] += 1.0
            
    # Persona Biases
    persona_biases = get_persona_biases(agent_state.persona.archetype)
    for action, mod in persona_biases.items():
        if action in biases:
            biases[action] += mod
            
    # Emotional Bias
    emotional_biases = get_emotional_bias(emotions)
    for action, bias in emotional_biases.items():
        if action in biases:
            biases[action] += bias
            
    # Goal Bonus (+0.5)
    if goals.get("ally_with"):
        biases["form_alliance"] += 0.5
        biases["support_agent"] += 0.5
        biases["offer_protection"] += 0.5
        
    if goals.get("undermine"):
        biases["denounce_agent"] += 0.5
        biases["sabotage"] += 0.5
        biases["spread_rumor"] += 0.5
        biases["oppose_agent"] += 0.5
        
    if goals.get("seek_approval_from"):
        biases["offer_concession"] += 0.5
        biases["support_agent"] += 0.5
        
    if goals.get("gain_influence_over"):
        biases["demand_concession"] += 0.5
        biases["accuse_agent"] += 0.5
        
    return biases

def apply_repetition_penalty(biases: Dict[str, float], recent_actions: List[str]) -> Dict[str, float]:
    """
    Applies a penalty to actions that have been performed recently.
    """
    if not recent_actions:
        return biases
        
    # Penalty: -0.75 if repeating last action
    last_action = recent_actions[-1]
    
    if last_action in biases:
        biases[last_action] -= 0.75
        
    # Additional penalty for PROPOSE_POLICY if recently used (handled by world engine validation too, but soft bias helps)
    if last_action == "propose_policy":
        biases["propose_policy"] -= 2.0 # Strong penalty to prevent spam
        
    return biases

def merge_biases_into_prompt(biases: Dict[str, float]) -> str:
    """
    Formats the biases for the LLM prompt.
    """
    lines = ["Action Biases (Pre-Computed):"]
    # Sort by weight descending
    sorted_biases = sorted(biases.items(), key=lambda x: x[1], reverse=True)
    
    for action, weight in sorted_biases:
        if weight > 0.01: # Filter out near-zero
            lines.append(f"- {action}: {weight:.2f}")
            
    lines.append("LLM MUST consider these biases when choosing actions.")
    return "\n".join(lines)

def select_targets_based_on_relationships(relationships: Dict[str, "Relationship"]) -> List[str]:
    """
    Returns a list of agent names sorted by relationship intensity (absolute score).
    """
    if not relationships:
        return []
        
    # Sort by absolute score (most loved or most hated first)
    sorted_rels = sorted(
        relationships.items(), 
        key=lambda x: abs(x[1].score), 
        reverse=True
    )
    return [name for name, _ in sorted_rels]

def get_top_actions(biases: Dict[str, float], top_n: int = 5) -> List[str]:
    """
    Returns the top N actions based on bias scores.
    """
    sorted_biases = sorted(biases.items(), key=lambda x: x[1], reverse=True)
    return [action for action, weight in sorted_biases[:top_n] if weight > 0]

def get_recommended_targets(
    agent_state: "AgentState",
    relationships: Dict[str, "Relationship"]
) -> Dict[str, str]:
    """
    Pre-computes the best target for each action type.
    Returns a dictionary mapping action category to a description string.
    """
    recommendations = {}
    
    # Sort relationships
    sorted_trust = sorted(relationships.items(), key=lambda x: x[1].trust, reverse=True)
    sorted_resentment = sorted(relationships.items(), key=lambda x: x[1].resentment, reverse=True)
    
    # Cooperative Target (Highest Trust)
    if sorted_trust:
        target, rel = sorted_trust[0]
        if rel.trust > 0:
            recommendations["support"] = f"{target} (Trust: {rel.trust})"
            
    # Hostile Target (Highest Resentment)
    if sorted_resentment:
        target, rel = sorted_resentment[0]
        if rel.resentment > 0:
            recommendations["oppose"] = f"{target} (Resentment: {rel.resentment})"
            
    return recommendations
