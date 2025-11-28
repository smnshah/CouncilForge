import pytest
from unittest.mock import MagicMock
from src.agents.llm_agent import LLMAgent
from src.core.models import Persona, Action, ActionType, Message, WorldState

@pytest.fixture
def mock_llm_client():
    return MagicMock()

@pytest.fixture
def agent(mock_llm_client):
    persona = Persona(
        name="TestAgent",
        description="Test",
        goals=["Test"],
        behavior_biases=[],
        archetype="Realist"
    )
    return LLMAgent(persona, mock_llm_client, history_depth=3)

def test_history_sliding_window(agent):
    """Test history maintains sliding window of correct depth."""
    agent.update_history("Turn 1")
    agent.update_history("Turn 2")
    agent.update_history("Turn 3")
    assert len(agent.history) == 3
    assert agent.history[0] == "Turn 1"
    
    agent.update_history("Turn 4")
    assert len(agent.history) == 3  # Still 3
    assert agent.history[0] == "Turn 2"  # Oldest dropped
    assert agent.history[-1] == "Turn 4"

def test_relationship_updates(agent):
    """Test process_action updates relationships correctly (Phase 1.5 values)."""
    # Support -> Trust +3
    action = Action(type=ActionType.SUPPORT_AGENT, target="TestAgent", reason="test")
    agent.process_action(action, "OtherAgent")
    
    assert "OtherAgent" in agent.relationships
    assert agent.relationships["OtherAgent"].trust == 3  # Phase 1.5 value
    assert agent.relationships["OtherAgent"].resentment == -2  # Phase 1.5 value
    
    # Oppose -> Resentment +3
    action2 = Action(type=ActionType.OPPOSE_AGENT, target="TestAgent", reason="test")
    agent.process_action(action2, "OtherAgent")
    
    assert agent.relationships["OtherAgent"].trust == 0  # 3 + (-3)
    assert agent.relationships["OtherAgent"].resentment == 1  # -2 + 3

def test_receive_message(agent):
    """Test receive_message updates relationships based on tone."""
    msg = Message(sender="Sender", recipient="TestAgent", text="Hi", tone="friendly", turn_sent=1)
    agent.receive_message(msg)
    
    assert "Sender" in agent.relationships
    assert agent.relationships["Sender"].trust == 3  # Friendly message
    assert agent.relationships["Sender"].resentment == -1

def test_prompt_building_includes_relationships(agent):
    """Test prompt includes significant relationships."""
    # Add a significant relationship
    action = Action(type=ActionType.SUPPORT_AGENT, target="TestAgent", reason="test")
    for _ in range(5):  # Build up trust
        agent.process_action(action, "FriendlyAgent")
    
    # Mock world state
    mock_state = WorldState(
        treasury=50,
        food=50,
        energy=50,
        infrastructure=50,
        morale=50,
        turn=1
    )
    
    prompt = agent._build_prompt(mock_state, ["FriendlyAgent"])
    
    # Should include relationship section
    assert "FriendlyAgent" in prompt
    assert "trust" in prompt.lower()

def test_decide_calls_llm(agent, mock_llm_client):
    """Test decide method calls LLM client and returns action."""
    # Mock LLM response
    mock_llm_client.generate_action.return_value = Action(
        type=ActionType.PASS,
        target="world",
        reason="test"
    )
    
    mock_state = WorldState(
        treasury=50,
        food=50,
        energy=50,
        infrastructure=50,
        morale=50,
        turn=1
    )
    
    action = agent.decide(mock_state, ["Agent2"])
    
    assert action.type == ActionType.PASS
    assert mock_llm_client.generate_action.called

def test_agent_ignores_self_actions(agent):
    """Test agent doesn't update relationships for its own actions."""
    action = Action(type=ActionType.SUPPORT_AGENT, target="Someone", reason="test")
    agent.process_action(action, "TestAgent")  # Same as agent's name
    
    # Should not track relationship with self
    assert "TestAgent" not in agent.relationships
