import pytest
from src.social.interpersonal_goals import update_goals, get_default_goals

def test_update_goals_ally():
    goals = get_default_goals()
    emotions = {"trust": 20.0, "resentment": 0.0, "admiration": 0.0}
    
    updated = update_goals(goals, emotions, "AgentA", world_stability=100, ambition=0.0)
    
    assert updated["ally_with"] == "AgentA"

def test_update_goals_undermine():
    goals = get_default_goals()
    emotions = {"trust": 0.0, "resentment": 20.0, "admiration": 0.0}
    
    updated = update_goals(goals, emotions, "AgentB", world_stability=100, ambition=0.0)
    
    assert updated["undermine"] == "AgentB"

def test_update_goals_seek_approval():
    goals = get_default_goals()
    emotions = {"trust": 0.0, "resentment": 0.0, "admiration": 15.0}
    
    updated = update_goals(goals, emotions, "AgentC", world_stability=100, ambition=0.0)
    
    assert updated["seek_approval_from"] == "AgentC"

def test_update_goals_gain_influence():
    goals = get_default_goals()
    emotions = {"trust": 0.0, "resentment": 0.0, "admiration": 0.0}
    
    # Ambition > 10 and Stability < 50
    updated = update_goals(goals, emotions, "AgentD", world_stability=40, ambition=15.0)
    
    assert updated["gain_influence_over"] == "AgentD"

def test_update_goals_gain_influence_fail():
    goals = get_default_goals()
    emotions = {"trust": 0.0, "resentment": 0.0, "admiration": 0.0}
    
    # Stability too high
    updated = update_goals(goals, emotions, "AgentD", world_stability=60, ambition=15.0)
    assert updated["gain_influence_over"] is None
    
    # Ambition too low
    updated = update_goals(goals, emotions, "AgentD", world_stability=40, ambition=5.0)
    assert updated["gain_influence_over"] is None

def test_update_goals_hysteresis():
    # Test dropping ally only when trust <= 10
    goals = get_default_goals()
    goals["ally_with"] = "AgentA"
    
    # Trust drops to 12 (still > 10, but < 15) -> Should keep ally
    emotions = {"trust": 12.0, "resentment": 0.0, "admiration": 0.0}
    updated = update_goals(goals, emotions, "AgentA", world_stability=100, ambition=0.0)
    assert updated["ally_with"] == "AgentA"
    
    # Trust drops to 10 -> Should drop ally
    emotions = {"trust": 10.0, "resentment": 0.0, "admiration": 0.0}
    updated = update_goals(goals, emotions, "AgentA", world_stability=100, ambition=0.0)
    assert updated["ally_with"] is None
