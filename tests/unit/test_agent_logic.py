import pytest
from unittest.mock import MagicMock
from src.agents.llm_agent import LLMAgent
from src.core.models import Persona, Action, ActionType, Message

@pytest.fixture
def mock_llm_client():
    return MagicMock()

@pytest.fixture
def agent(mock_llm_client):
    persona = Persona(
        name="TestAgent",
        description="Test",
        goals=["Test"],
        behavior_biases=[]
    )
    return LLMAgent(persona, mock_llm_client, history_depth=3)

def test_history_sliding_window(agent):
    agent.update_history("Turn 1")
    agent.update_history("Turn 2")
    agent.update_history("Turn 3")
    assert len(agent.history) == 3
    assert agent.history[0] == "Turn 1"
    
    agent.update_history("Turn 4")
    assert len(agent.history) == 3
    assert agent.history[0] == "Turn 2"
    assert agent.history[-1] == "Turn 4"

def test_relationship_updates(agent):
    # Support -> Trust +
    action = Action(type=ActionType.SUPPORT_AGENT, target="TestAgent", reason="test")
    agent.process_action(action, "OtherAgent")
    
    assert "OtherAgent" in agent.relationships
    assert agent.relationships["OtherAgent"]["trust"] == 10
    
    # Sabotage -> Resentment +
    action = Action(type=ActionType.SABOTAGE, target="TestAgent", reason="test")
    agent.process_action(action, "OtherAgent")
    
    assert agent.relationships["OtherAgent"]["resentment"] == 20

def test_receive_message(agent):
    msg = Message(sender="Sender", recipient="TestAgent", text="Hi", turn_sent=1)
    agent.receive_message(msg)
    assert len(agent.message_inbox) == 1
    assert agent.message_inbox[0].text == "Hi"

def test_prompt_building_clears_inbox(agent):
    msg = Message(sender="Sender", recipient="TestAgent", text="Hi", turn_sent=1)
    agent.receive_message(msg)
    
    # Mock world state
    mock_state = MagicMock()
    mock_state.turn = 1
    mock_state.resource_level = 50
    
    # Building prompt should clear inbox (in decide, actually)
    # But _build_prompt just reads it.
    # decide() calls _build_prompt then clears.
    
    agent.llm_client.generate_action.return_value = Action(type=ActionType.PASS, target="none", reason="pass")
    
    agent.decide(mock_state)
    
    assert len(agent.message_inbox) == 0
