from typing import Dict, Optional

# Emotion ranges
MIN_EMOTION = -50.0
MAX_EMOTION = 50.0

def normalize_emotion(value: float) -> float:
    """Clamps emotion value between MIN_EMOTION and MAX_EMOTION."""
    return max(MIN_EMOTION, min(MAX_EMOTION, value))

def get_default_emotions() -> Dict[str, float]:
    """Returns a default dictionary of emotions."""
    return {
        "trust": 0.0,
        "resentment": 0.0,
        "admiration": 0.0,
        "fear": 0.0,
        "ambition": 0.0,
        "insecurity": 0.0,
    }

def update_emotions(
    current_emotions: Dict[str, float],
    action_type: str,
    is_target: bool = False
) -> Dict[str, float]:
    """
    Updates emotional state based on an interaction.
    
    Args:
        current_emotions: The current dictionary of emotions toward a specific agent (or general state).
        action_type: The type of action performed.
        is_target: Whether the agent owning these emotions was the target of the action.
        
    Returns:
        Updated dictionary of emotions.
    """
    # Create a copy to avoid mutating the input directly if needed, 
    # though usually we want to update the state. Let's return a new dict for safety.
    new_emotions = current_emotions.copy()
    
    # Delta values
    trust_delta = 0.0
    resentment_delta = 0.0
    admiration_delta = 0.0
    fear_delta = 0.0
    
    # Logic based on action type
    # Note: These rules apply to how I feel about the ACTOR.
    
    if action_type == "support_agent":
        if is_target:
            trust_delta += 5.0
            resentment_delta -= 2.0
            admiration_delta += 1.0
            
    elif action_type == "oppose_agent":
        if is_target:
            resentment_delta += 5.0
            trust_delta -= 5.0
            fear_delta += 1.0
            
    elif action_type == "sabotage":
        if is_target:
            resentment_delta += 15.0
            trust_delta -= 10.0
            fear_delta += 5.0
            
    elif action_type == "negotiate":
        if is_target:
            trust_delta += 2.0
            admiration_delta += 1.0
            
    elif action_type == "consume_resource":
        # Selfish action by other agent increases resentment slightly
        resentment_delta += 1.0
        
    elif action_type == "denounce_agent":
        if is_target:
            resentment_delta += 8.0
            trust_delta -= 5.0
            
    elif action_type == "form_alliance":
        if is_target:
            trust_delta += 10.0
            admiration_delta += 2.0
            
    elif action_type == "offer_concession":
        if is_target:
            trust_delta += 5.0
            resentment_delta -= 5.0
            
    elif action_type == "demand_concession":
        if is_target:
            resentment_delta += 5.0
            fear_delta += 2.0
            
    elif action_type == "accuse_agent":
        if is_target:
            resentment_delta += 6.0
            trust_delta -= 3.0
            
    elif action_type == "offer_protection":
        if is_target:
            trust_delta += 8.0
            admiration_delta += 3.0
            
    elif action_type == "spread_rumor":
        if is_target:
            resentment_delta += 4.0
            trust_delta -= 4.0
            
    # Apply deltas
    new_emotions["trust"] = normalize_emotion(new_emotions.get("trust", 0.0) + trust_delta)
    new_emotions["resentment"] = normalize_emotion(new_emotions.get("resentment", 0.0) + resentment_delta)
    new_emotions["admiration"] = normalize_emotion(new_emotions.get("admiration", 0.0) + admiration_delta)
    new_emotions["fear"] = normalize_emotion(new_emotions.get("fear", 0.0) + fear_delta)
    
    # Ambition and Insecurity are usually internal traits or updated by world state/success,
    # but could be affected here too. For now, we leave them as is unless specified.
    
    return new_emotions

def get_emotional_bias(emotions: Dict[str, float]) -> Dict[str, float]:
    """
    Calculates action bias multipliers based on emotional state.
    
    Args:
        emotions: Dictionary of emotions toward a target.
        
    Returns:
        Dictionary mapping action types to bias multipliers (additive or multiplicative).
        Spec says "multipliers".
    """
    biases = {}
    
    trust = emotions.get("trust", 0.0)
    resentment = emotions.get("resentment", 0.0)
    admiration = emotions.get("admiration", 0.0)
    fear = emotions.get("fear", 0.0)
    
    # Base multiplier is 0.0 (additive bonus) or 1.0 (multiplicative)?
    # Spec says "final_bias[action] = base_weight + relation_bonus + emotion_bias..."
    # So these should be additive bonuses to the base weight.
    
    # Positive actions
    # High trust/admiration -> boost support, alliance
    biases["support_agent"] = (trust + admiration) / 100.0
    biases["form_alliance"] = (trust + admiration) / 80.0
    biases["offer_protection"] = (trust + admiration) / 90.0
    biases["offer_concession"] = (trust - resentment) / 100.0
    biases["negotiate"] = (trust + admiration - fear) / 100.0
    
    # Negative actions
    # High resentment -> boost oppose, sabotage, denounce
    biases["oppose_agent"] = (resentment - trust) / 100.0
    biases["sabotage"] = (resentment - trust) / 80.0
    biases["denounce_agent"] = (resentment - trust) / 90.0
    biases["accuse_agent"] = (resentment - trust) / 90.0
    biases["demand_concession"] = (resentment + fear) / 100.0
    biases["spread_rumor"] = (resentment + insecurity_factor(emotions)) / 100.0
    
    return biases

def insecurity_factor(emotions: Dict[str, float]) -> float:
    return emotions.get("insecurity", 0.0)
