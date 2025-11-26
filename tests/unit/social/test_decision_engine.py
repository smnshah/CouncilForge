import pytest
from unittest.mock import MagicMock
from src.social.decision_engine import compute_action_biases, apply_repetition_penalty, select_targets_based_on_relationships
from src.social.relationship_engine import Relationship

def test_compute_action_biases_defaults():
    agent_state = MagicMock()
    world_state = MagicMock()
    # Mock world state attributes to avoid errors
    world_state.crisis_level = 0
    world_state.stability = 100
    world_state.morale = 100
    
    biases = compute_action_biases(agent_state, world_state, {})
    
    # Check if all keys exist and sum to approx 1
    assert "support_agent" in biases
    assert sum(biases.values()) == pytest.approx(1.0)

def test_compute_action_biases_high_crisis():
    agent_state = MagicMock()
    world_state = MagicMock()
    world_state.crisis_level = 80 # > 60
    world_state.stability = 100
    world_state.morale = 100
    
    biases = compute_action_biases(agent_state, world_state, {})
    
    # Negotiate and request_help should be boosted
    # We can't check exact values easily without reproducing logic, but we can check relative rank or existence
    assert biases["negotiate"] > 0.1 # Default is 0.1, boosted by 0.1
    assert biases["request_help"] > 0.1

def test_apply_repetition_penalty():
    biases = {"action_a": 0.5, "action_b": 0.5}
    recent_actions = ["action_a", "action_a", "action_a"]
    
    new_biases = apply_repetition_penalty(biases, recent_actions)
    
    assert new_biases["action_a"] < 0.1 # Should be heavily penalized
    assert new_biases["action_b"] == 0.5

def test_select_targets_based_on_relationships():
    rels = {
        "AgentA": Relationship(trust=10, resentment=0), # Score 10
        "AgentB": Relationship(trust=-50, resentment=0), # Score -50, Abs 50
        "AgentC": Relationship(trust=0, resentment=0) # Score 0
    }
    
    targets = select_targets_based_on_relationships(rels)
    
    # Should be sorted by absolute score: AgentB (50), AgentA (10), AgentC (0)
    assert targets == ["AgentB", "AgentA", "AgentC"]
