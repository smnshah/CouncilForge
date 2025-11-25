import pytest
from pydantic import ValidationError
from src.core.models import Action, ActionType, WorldState, AgentState, Persona

def test_world_state_initialization():
    state = WorldState(resource_level=50, stability=50, turn=0)
    assert state.resource_level == 50
    assert state.stability == 50
    assert state.turn == 0

def test_action_valid():
    action = Action(type=ActionType.INCREASE_RESOURCE, target="world", reason="test")
    assert action.type == ActionType.INCREASE_RESOURCE
    assert action.target == "world"
    assert action.reason == "test"

def test_action_invalid_type():
    with pytest.raises(ValidationError):
        Action(type="invalid_type", target="world", reason="test")

def test_action_missing_field():
    with pytest.raises(ValidationError):
        Action(type=ActionType.PASS, target="none") # Missing reason

def test_persona_initialization():
    persona = Persona(
        name="Test Agent",
        description="A test agent",
        goals=["Goal 1"],
        behavior_biases=["Bias 1"]
    )
    assert persona.name == "Test Agent"
    assert len(persona.goals) == 1
