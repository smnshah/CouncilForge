"""
Decision Engine Module

Calculates action biases and applies social pressure to agent decisions.
"""
from typing import Dict, List, Any, TYPE_CHECKING
from collections import Counter

if TYPE_CHECKING:
    from src.core.models import AgentState, WorldState
    from src.social.relationship_engine import Relationship

def compute_action_biases(
    agent_state: "AgentState",
    world_state: "WorldState",
    relationships: Dict[str, "Relationship"]
) -> Dict[str, float]:
    """
    Computes weighted probabilities for actions based on traits and relationships.
    """
    biases = {
        "support_agent": 0.1,
        "oppose_agent": 0.1,
        "negotiate": 0.1,
        "request_help": 0.1,
        "trade": 0.1,
        "sabotage": 0.05,
        "send_message": 0.1,
        "improve_resource": 0.1,
        "consume_resource": 0.1,
        "boost_morale": 0.05,
        "strengthen_infrastructure": 0.1
    }
    
    # 1. Personality Traits (Simplified for now)
    # In a real implementation, we'd parse the persona traits.
    # For now, we'll assume some defaults or look for keywords in persona description if available.
    
    # 2. Relationship Scores
    avg_relationship_score = 0
    if relationships:
        scores = [r.score for r in relationships.values()]
        avg_relationship_score = sum(scores) / len(scores)
        
    if avg_relationship_score > 20:
        biases["support_agent"] += 0.1
        biases["trade"] += 0.05
        biases["send_message"] += 0.05
    elif avg_relationship_score < -20:
        biases["oppose_agent"] += 0.1
        biases["sabotage"] += 0.05
    elif -20 <= avg_relationship_score <= 20:
        biases["negotiate"] += 0.1
        
    # 3. World Pressures
    # Assuming world_state has these fields as per Phase 2 spec
    if hasattr(world_state, "crisis_level") and world_state.crisis_level > 60:
        biases["negotiate"] += 0.1
        biases["request_help"] += 0.1
        
    if hasattr(world_state, "stability") and world_state.stability < 40:
        biases["oppose_agent"] += 0.05
        biases["sabotage"] += 0.05
        
    if hasattr(world_state, "morale") and world_state.morale < 40:
        biases["send_message"] += 0.1
        biases["support_agent"] += 0.05
        
    # Normalize (optional, but good for relative weights)
    total = sum(biases.values())
    if total > 0:
        for k in biases:
            biases[k] = round(biases[k] / total, 2)
            
    return biases

def apply_repetition_penalty(
    biases: Dict[str, float],
    recent_actions: List[str]
) -> Dict[str, float]:
    """
    Lowers probability for actions repeated too often.
    """
    if not recent_actions:
        return biases
        
    # Check for strict repetition of last 3 actions
    if len(recent_actions) >= 3:
        last_three = recent_actions[-3:]
        if all(a == last_three[0] for a in last_three):
            repeated_action = last_three[0]
            if repeated_action in biases:
                biases[repeated_action] *= 0.1 # Heavy penalty
                
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
