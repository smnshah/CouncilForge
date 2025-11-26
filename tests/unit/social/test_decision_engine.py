import pytest
from unittest.mock import MagicMock
from src.social.decision_engine import compute_action_biases, apply_repetition_penalty, select_targets_based_on_relationships, get_top_actions, get_recommended_targets
from src.social.relationship_engine import Relationship

def test_compute_action_biases_defaults():
    agent_state = MagicMock()
    emotions = {"trust": 0.0, "resentment": 0.0, "admiration": 0.0, "fear": 0.0}
    goals = {}
    
    biases = compute_action_biases(agent_state, world_state, {}, emotions, goals)
    
    # World actions boosted by +1.0 -> 1.25
    assert biases["improve_resource"] == 1.25
    # Social actions stay 1.0
    assert biases["support_agent"] == 1.0

def test_compute_action_biases_goals():
    agent_state = MagicMock()
    world_state = MagicMock()
    world_state.crisis_level = 0
    
    emotions = {"trust": 0.0, "resentment": 0.0, "admiration": 0.0, "fear": 0.0}
    goals = {"ally_with": "AgentA"}
    
    biases = compute_action_biases(agent_state, world_state, {}, emotions, goals)
    
    # ally_with boosts form_alliance by 0.5 -> 1.5
    assert biases["form_alliance"] == 1.5

def test_apply_repetition_penalty():
    biases = {"action_a": 1.0, "action_b": 1.0}
    recent_actions = ["action_a"]
    
    new_biases = apply_repetition_penalty(biases, recent_actions)
    
    # Penalty -0.75 -> 0.25
    assert new_biases["action_a"] == 0.25
    assert new_biases["action_b"] == 1.0

def test_select_targets_based_on_relationships():
    rels = {
        "AgentA": Relationship(trust=10, resentment=0), # Score 10
        "AgentB": Relationship(trust=-50, resentment=0), # Score -50, Abs 50
        "AgentC": Relationship(trust=0, resentment=0) # Score 0
    }
    
    targets = select_targets_based_on_relationships(rels)
    
    # Should be sorted by absolute score: AgentB (50), AgentA (10), AgentC (0)
    assert targets == ["AgentB", "AgentA", "AgentC"]

def test_get_top_actions():
    biases = {"action_a": 1.5, "action_b": 0.5, "action_c": 2.0}
    top = get_top_actions(biases, top_n=2)
    assert len(top) == 2
    assert top[0] == "action_c"
    assert top[1] == "action_a"

def test_get_recommended_targets():
    agent_state = MagicMock()
    relationships = {
        "AgentA": Relationship(trust=20, resentment=0),
        "AgentB": Relationship(trust=0, resentment=15)
    }
    
    recs = get_recommended_targets(agent_state, relationships)
    
    assert "support" in recs
    assert "AgentA" in recs["support"]
    assert "oppose" in recs
    assert "AgentB" in recs["oppose"]
