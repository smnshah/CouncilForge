import pytest
from src.core.models import WorldState, Action, ActionType, Persona, Message

def test_world_state_initialization():
    """Test WorldState initializes with treasury and core resources."""
    state = WorldState(
        treasury=50,
        food=50,
        energy=50,
        infrastructure=50,
        morale=50,
        turn=0
    )
    assert state.treasury == 50
    assert state.food == 50
    assert state.energy == 50
    assert state.infrastructure == 50
    assert state.morale == 50
    assert state.message_queue == []
    assert state.crisis_level == 0  # Default 0

def test_action_model():
    """Test Action model with Phase 1.5 actions."""
    # Resource action
    action = Action(
        type=ActionType.IMPROVE_FOOD,
        target="world",
        reason="Testing"
    )
    assert action.type == ActionType.IMPROVE_FOOD
    assert action.target == "world"
    
    # Social action
    action2 = Action(
        type=ActionType.SUPPORT_AGENT,
        target="Agent2",
        reason="Testing support"
    )
    assert action2.type == ActionType.SUPPORT_AGENT
    assert action2.target == "Agent2"

def test_message_model():
    """Test Message model."""
    msg = Message(
        sender="AgentA",
        recipient="AgentB",
        content="Hello",
        turn_sent=1
    )
    assert msg.sender == "AgentA"
    assert msg.content == "Hello"


def test_persona_model_defaults():
    """Test Persona model with default values."""
    persona = Persona(
        name="Test Agent",
        description="A test agent",
        goals=["Test"],
        behavior_biases=["None"]
    )
    assert persona.archetype == "Generic"
    assert persona.risk_preference == "medium"
    assert persona.core_values == []

def test_action_types():
    """Test all 8 Phase 1.5 action types exist."""
    # Resource actions (4)
    assert ActionType.IMPROVE_FOOD == "improve_food"
    assert ActionType.IMPROVE_ENERGY == "improve_energy"
    assert ActionType.IMPROVE_INFRASTRUCTURE == "improve_infrastructure"
    assert ActionType.BOOST_MORALE == "boost_morale"
    
    # Social actions (3)
    assert ActionType.SUPPORT_AGENT == "support_agent"
    assert ActionType.OPPOSE_AGENT == "oppose_agent"
    assert ActionType.SEND_MESSAGE == "send_message"
    
    # Other (1)
    assert ActionType.PASS == "pass"
