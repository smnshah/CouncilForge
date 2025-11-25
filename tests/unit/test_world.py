import pytest
from src.world.engine import World
from src.config.settings import WorldConfig
from src.core.models import Action, ActionType

@pytest.fixture
def world():
    config = WorldConfig(initial_resource_level=50, initial_stability=50)
    return World(config)

def test_initial_state(world):
    assert world.state.resource_level == 50
    assert world.state.stability == 50
    assert world.state.turn == 0

def test_increase_resource(world):
    action = Action(type=ActionType.INCREASE_RESOURCE, target="world", reason="test")
    success, msg = world.apply_action("Agent1", action)
    assert success
    assert world.state.resource_level == 60

def test_decrease_resource(world):
    action = Action(type=ActionType.DECREASE_RESOURCE, target="world", reason="test")
    success, msg = world.apply_action("Agent1", action)
    assert success
    assert world.state.resource_level == 40

def test_decrease_resource_limit(world):
    world.state.resource_level = 5
    action = Action(type=ActionType.DECREASE_RESOURCE, target="world", reason="test")
    # Should fail validation or clamp? 
    # Engine.is_valid_action checks if resource <= 0 for decrease.
    # If resource is 5, it is valid.
    success, msg = world.apply_action("Agent1", action)
    assert success
    assert world.state.resource_level == 0 # max(0, 5-10)

def test_decrease_resource_invalid(world):
    world.state.resource_level = 0
    action = Action(type=ActionType.DECREASE_RESOURCE, target="world", reason="test")
    success, msg = world.apply_action("Agent1", action)
    assert not success
    assert "invalid" in msg

def test_support_agent(world):
    action = Action(type=ActionType.SUPPORT_AGENT, target="Agent2", reason="test")
    success, msg = world.apply_action("Agent1", action)
    assert success
    assert world.state.stability == 55

def test_oppose_agent(world):
    action = Action(type=ActionType.OPPOSE_AGENT, target="Agent2", reason="test")
    success, msg = world.apply_action("Agent1", action)
    assert success
    assert world.state.stability == 45

def test_pass_action(world):
    action = Action(type=ActionType.PASS, target="none", reason="test")
    success, msg = world.apply_action("Agent1", action)
    assert success
    assert world.state.resource_level == 50 # Unchanged
    assert world.state.stability == 50 # Unchanged

def test_increment_turn(world):
    world.increment_turn()
    assert world.state.turn == 1
