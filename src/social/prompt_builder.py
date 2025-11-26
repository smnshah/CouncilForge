"""
Prompt Builder Module

Helper functions to construct social sections of the LLM prompt.
"""
from typing import Dict, List, Any
from .relationship_engine import Relationship
from .decision_engine import merge_biases_into_prompt
from .interaction_triggers import generate_prompt_section_for_interaction_triggers

def build_social_section(
    relationships: Dict[str, Relationship],
    biases: Dict[str, float],
    triggers: List[str],
    recent_actions: List[str],
    messages: List[Dict[str, Any]]
) -> str:
    """
    Constructs the social context section for the prompt.
    """
    sections = []
    
    # 1. Relationship Summary
    if relationships:
        rel_lines = ["Relationship Summary:"]
        for name, rel in relationships.items():
            rel_lines.append(f"- {name}: Score {rel.score} (Trust: {rel.trust}, Resentment: {rel.resentment})")
        sections.append("\n".join(rel_lines))
        
    # 2. Action Biases
    if biases:
        sections.append(merge_biases_into_prompt(biases))
        
    # 3. Interaction Triggers
    if triggers:
        sections.append(generate_prompt_section_for_interaction_triggers(triggers))
        
    # 4. Recent Actions (Diversity)
    if recent_actions:
        action_lines = ["Recent Agent Actions:"]
        for i, action in enumerate(reversed(recent_actions)):
            action_lines.append(f"- Turn -{i+1}: {action}")
        sections.append("\n".join(action_lines))
        
    # 5. Messages Received
    if messages:
        msg_lines = ["Messages Received:"]
        for msg in messages:
            # Assuming msg is a dict or object with sender, text, tone
            sender = msg.get("sender", "Unknown")
            text = msg.get("text", "")
            tone = msg.get("tone", "neutral")
            msg_lines.append(f"- From {sender}: \"{text}\"")
            msg_lines.append(f"  Tone: {tone}")
        sections.append("\n".join(msg_lines))
        
    # 6. Social Instructions
    instructions = [
        "Social Guidelines:",
        "1. You MUST consider interpersonal relationships when selecting an action.",
        "2. You MUST avoid repeating the same action without strong justification.",
        "3. You SHOULD target agents with recent interactions.",
        "4. You SHOULD use social actions when relevant based on relationships and triggers."
    ]
    sections.append("\n".join(instructions))
    
    return "\n\n".join(sections)
