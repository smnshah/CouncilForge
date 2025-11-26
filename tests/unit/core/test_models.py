import pytest
from src.core.models import WorldState, Action, ActionType, Persona, Message

def test_world_state_initialization():
    state = WorldState(
        resource_level=50,
        stability=50,
        food=50,
        energy=50,
        infrastructure=50,
        morale=50,
        turn=0
    )
    assert state.resource_level == 50
    assert state.food == 50
    assert state.message_queue == []
    assert state.crisis_level == 0  # Default 0
    assert state.overall_health == 0 # Default 0

def test_action_model():
    action = Action(
        type=ActionType.IMPROVE_RESOURCE,
        target="world",
        resource="food",
        amount=10,
        reason="Testing"
    )
    assert action.type == ActionType.IMPROVE_RESOURCE
    assert action.resource == "food"
    assert action.amount == 10

def test_message_model():
    msg = Message(
        sender="AgentA",
        recipient="AgentB",
        text="Hello",
        turn_sent=1
    )
    assert msg.sender == "AgentA"
    assert msg.text == "Hello"

def test_persona_model_defaults():
    persona = Persona(
        name="Test Agent",
        description="A test agent",
        goals=["Test"],
        behavior_biases=["None"]
    )
    assert persona.archetype == "Generic"
    assert persona.risk_preference == "medium"
    assert persona.core_values == []
