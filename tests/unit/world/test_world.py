import pytest
from src.world.engine import World
from src.config.settings import WorldConfig
from src.core.models import Action, ActionType

@pytest.fixture
def world():
    config = WorldConfig(
        initial_resource_level=50, 
        initial_stability=50,
        initial_food=50,
        initial_energy=50,
        initial_infrastructure=50,
        initial_morale=50
    )
    return World(config)

def test_initial_state(world):
    assert world.state.resource_level == 50
    assert world.state.food == 50
    assert world.state.crisis_level == 50 # 100 - 50 = 50
    assert world.state.overall_health == 50 # (50+50+50+50+50)//5 = 50

def test_derived_metrics(world):
    # Manually set values to test calculation
    world.state.resource_level = 10
    world.state.food = 10
    world.state.energy = 10
    world.state.infrastructure = 10
    world.state.morale = 10
    world.state.stability = 10
    
    world._calculate_derived_metrics()
    
    # Avg resources = 10
    # Crisis = 100 - 10 = 90
    assert world.state.crisis_level == 90
    
    # Overall health = (10+10+10+10+10)//5 = 10
    assert world.state.overall_health == 10

def test_improve_resource(world):
    action = Action(
        type=ActionType.IMPROVE_RESOURCE, 
        target="world", 
        resource="food", 
        amount=10, 
        reason="test"
    )
    success, msg = world.apply_action("Agent1", action)
    assert success
    assert world.state.food == 60
    assert "improved food" in msg

def test_consume_resource(world):
    action = Action(
        type=ActionType.CONSUME_RESOURCE, 
        target="world", 
        resource="energy", 
        amount=10, 
        reason="test"
    )
    success, msg = world.apply_action("Agent1", action)
    assert success
    assert world.state.energy == 40
    assert "consumed energy" in msg

def test_resource_clamping(world):
    world.state.food = 5
    action = Action(
        type=ActionType.CONSUME_RESOURCE, 
        target="world", 
        resource="food", 
        amount=10, 
        reason="test"
    )
    success, msg = world.apply_action("Agent1", action)
    assert success
    assert world.state.food == 0 # Clamped to 0

def test_send_message(world):
    action = Action(
        type=ActionType.SEND_MESSAGE,
        target="Agent2",
        message="Hello",
        reason="test"
    )
    success, msg = world.apply_action("Agent1", action)
    assert success
    assert len(world.state.message_queue) == 1
    assert world.state.message_queue[0].sender == "Agent1"
    assert world.state.message_queue[0].recipient == "Agent2"
    assert world.state.message_queue[0].text == "Hello"

def test_social_actions(world):
    # Negotiate
    action = Action(type=ActionType.NEGOTIATE, target="Agent2", reason="test")
    success, msg = world.apply_action("Agent1", action)
    assert success
    assert "negotiated" in msg
    
    # Sabotage
    action = Action(type=ActionType.SABOTAGE, target="Agent2", reason="test")
    success, msg = world.apply_action("Agent1", action)
    assert success
    assert world.state.stability == 40 # 50 - 10
