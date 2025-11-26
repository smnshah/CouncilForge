import pytest
from unittest.mock import MagicMock
from src.social.interaction_triggers import compute_interaction_triggers

def test_compute_interaction_triggers_targeted():
    agent_state = MagicMock()
    world_state = MagicMock()
    # Configure mocks to avoid comparison errors
    world_state.resource_level = 50
    world_state.food = 50
    world_state.crisis_level = 0
    agent_state.messages_received = []
    
    recent_interactions = ["AgentA opposed you"]
    
    triggers = compute_interaction_triggers(agent_state, world_state, recent_interactions)
    
    assert "You have been targeted in recent interactions." in triggers

def test_compute_interaction_triggers_crisis():
    agent_state = MagicMock()
    world_state = MagicMock()
    world_state.resource_level = 50
    world_state.food = 50
    world_state.crisis_level = 80
    agent_state.messages_received = []
    
    triggers = compute_interaction_triggers(agent_state, world_state, [])
    
    assert "The world is in crisis." in triggers

def test_compute_interaction_triggers_messages():
    agent_state = MagicMock()
    agent_state.messages_received = ["msg"]
    world_state = MagicMock()
    world_state.resource_level = 50
    world_state.food = 50
    world_state.crisis_level = 0
    
    triggers = compute_interaction_triggers(agent_state, world_state, [])
    
    assert "You have received new messages." in triggers
