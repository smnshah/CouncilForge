"""
Message Parser Module

Analyzes the tone of messages between agents.
"""
import re

def parse_message_tone(text: str) -> str:
    """
    Determines the tone of a message based on simple heuristics.
    
    Args:
        text: The message content.
        
    Returns:
        "friendly", "hostile", or "neutral"
    """
    text_lower = text.lower()
    
    # Hostile indicators
    hostile_keywords = [
        "betray", "enemy", "attack", "destroy", "fool", "liar", "hate", 
        "stupid", "useless", "weak", "threat", "demand", "or else",
        "crush", "disaster", "hoard", "greed", "suffering", "oppress"
    ]
    
    # Check for all caps (shouting) - heuristic: > 50% caps and length > 5
    caps_count = sum(1 for c in text if c.isupper())
    if len(text) > 5 and caps_count / len(text) > 0.5:
        return "hostile"
        
    for word in hostile_keywords:
        if word in text_lower:
            return "hostile"
            
    # Friendly indicators
    friendly_keywords = [
        "friend", "help", "support", "thanks", "thank you", "appreciate", 
        "good", "great", "ally", "together", "cooperate", "peace", "love",
        "please", "kind"
    ]
    
    for word in friendly_keywords:
        if word in text_lower:
            return "friendly"
            
    return "neutral"
