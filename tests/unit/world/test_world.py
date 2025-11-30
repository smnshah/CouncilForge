import pytest
from src.world.engine import World
from src.config.settings import WorldConfig
from src.core.models import Action, ActionType

@pytest.fixture
def world_config():
    return WorldConfig(
        initial_treasury=25,  # Phase 1.7: Scarcity
        initial_food=35,
        initial_energy=35,
        initial_infrastructure=40,
        initial_morale=45
    )

@pytest.fixture
def world(world_config):
    """Create a test world with Phase 1.7 scarcity config."""
    return World(world_config)

def test_initial_state(world):
    """Test world initializes with correct state."""
    assert world.state.treasury == 25
    assert world.state.food == 35
    assert world.state.energy == 35
    assert world.state.infrastructure == 40
    assert world.state.morale == 45
    # Avg = (25+35+35+40+45)/5 = 36, crisis = 100 - 36 = 64
    assert world.state.crisis_level == 64

def test_derived_metrics(world):
    """Test crisis level calculation."""
    # Manually set values to test calculation
    world.state.treasury = 10
    world.state.food = 10
    world.state.energy = 10
    world.state.infrastructure = 10
    world.state.morale = 10
    
    world._calculate_derived_metrics()
    
    # Avg resources = 10, crisis = 100 - 10 = 90
    assert world.state.crisis_level == 90

def test_improve_food_with_cost(world):
    """Test improve_food action costs 3 energy."""
    initial_energy = world.state.energy
    initial_food = world.state.food
    
    action = Action(
        type=ActionType.IMPROVE_FOOD,
        target="world",
        reason="test"
    )
    success, msg = world.apply_action("Agent1", action, ["Agent1", "Agent2"])
    
    assert success
    assert world.state.food == initial_food + 8  # Gain 8
    assert world.state.energy == initial_energy - 3  # Cost 3
    assert "improved food" in msg.lower()

def test_improve_energy_with_cost(world):
    """Test improve_energy action costs 3 treasury."""
    initial_treasury = world.state.treasury
    initial_energy = world.state.energy
    
    action = Action(
        type=ActionType.IMPROVE_ENERGY,
        target="world",
        reason="test"
    )
    success, msg = world.apply_action("Agent1", action, ["Agent1", "Agent2"])
    
    assert success
    assert world.state.energy == initial_energy + 8  # Gain 8
    assert world.state.treasury == initial_treasury - 3  # Cost 3
    assert "improved energy" in msg.lower()

def test_improve_infrastructure_with_cost(world):
    """Test improve_infrastructure action costs 4 treasury."""
    initial_treasury = world.state.treasury
    initial_infra = world.state.infrastructure
    
    action = Action(
        type=ActionType.IMPROVE_INFRASTRUCTURE,
        target="world",
        reason="test"
    )
    success, msg = world.apply_action("Agent1", action, ["Agent1", "Agent2"])
    
    assert success
    assert world.state.infrastructure == initial_infra + 8  # Gain 8
    assert world.state.treasury == initial_treasury - 4  # Cost 4

def test_boost_morale_with_cost(world):
    """Test boost_morale action costs 2 food."""
    initial_food = world.state.food
    initial_morale = world.state.morale
    
    action = Action(
        type=ActionType.BOOST_MORALE,
        target="world",
        reason="test"
    )
    success, msg = world.apply_action("Agent1", action, ["Agent1", "Agent2"])
    
    assert success
    assert world.state.morale == initial_morale + 8  # Gain 8
    assert world.state.food == initial_food - 2  # Cost 2

def test_cannot_afford_action(world):
    """Test action fails when cannot afford cost."""
    world.state.energy = 2  # Not enough for improve_food (costs 3)
    
    action = Action(
        type=ActionType.IMPROVE_FOOD,
        target="world",
        reason="test"
    )
    success, msg = world.apply_action("Agent1", action, ["Agent1", "Agent2"])
    
    assert not success
    assert "cannot afford" in msg.lower() or "insufficient" in msg.lower()
    assert world.state.food == 35  # Unchanged (Phase 1.7 initial)

def test_resource_clamping(world):
    """Test resources clamp at 0."""
    world.state.food = 5
    world.state.treasury = 100
    
    # Consume more food than available via morale boost
    for _ in range(5):  # Each costs 2 food
        action = Action(
            type=ActionType.BOOST_MORALE,
            target="world",
            reason="test"
        )
        world.apply_action("Agent1", action, ["Agent1", "Agent2"])
    
    # Should be clamped at 0
    assert world.state.food >= 0

def test_send_message(world):
    """Test send_message action."""
    action = Action(
        type=ActionType.SEND_MESSAGE,
        target="Agent2",
        message="Hello",
        reason="test"
    )
    success, msg = world.apply_action("Agent1", action, ["Agent1", "Agent2"])
    
    assert success
    assert len(world.state.message_queue) == 1
    assert world.state.message_queue[0].sender == "Agent1"
    assert world.state.message_queue[0].recipient == "Agent2"
    assert world.state.message_queue[0].content == "Hello"

def test_support_agent(world):
    """Test support_agent social action."""
    initial_morale = world.state.morale
    
    action = Action(
        type=ActionType.SUPPORT_AGENT,
        target="Agent2",
        reason="test"
    )
    success, msg = world.apply_action("Agent1", action, ["Agent1", "Agent2"])
    
    assert success
    assert world.state.morale == initial_morale + 5  # +5 morale
    assert "supported" in msg.lower()

def test_oppose_agent(world):
    """Test oppose_agent social action."""
    initial_morale = world.state.morale
    
    action = Action(
        type=ActionType.OPPOSE_AGENT,
        target="Agent2",
        reason="test"
    )
    success, msg = world.apply_action("Agent1", action, ["Agent1", "Agent2"])
    
    assert success
    assert world.state.morale == initial_morale - 3  # -3 morale
    assert "opposed" in msg.lower()

def test_pass_action(world):
    """Test pass action does nothing."""
    initial_state = world.state.model_copy()
    
    action = Action(
        type=ActionType.PASS,
        target="world",
        reason="test"
    )
    success, msg = world.apply_action("Agent1", action, ["Agent1", "Agent2"])
    
    assert success
    assert "passed" in msg.lower()
    # State unchanged (except derived metrics may recalculate)
    assert world.state.treasury == initial_state.treasury
    assert world.state.food == initial_state.food

def test_world_entropy(world):
    """Test resources decay by 2 each turn."""
    initial_treasury = world.state.treasury
    initial_food = world.state.food
    initial_energy = world.state.energy
    initial_infra = world.state.infrastructure
    
    world.increment_turn()
    
    assert world.state.turn == 1
    assert world.state.treasury == initial_treasury - 2
    assert world.state.food == initial_food - 2
    assert world.state.energy == initial_energy - 2
    assert world.state.infrastructure == initial_infra - 2
    # Morale doesn't decay (not in entropy list)

def test_invalid_target(world):
    """Test invalid action target."""
    action = Action(
        type=ActionType.SUPPORT_AGENT,
        target="NonExistentAgent",
        reason="test"
    )
    success, msg = world.apply_action("Agent1", action, ["Agent1", "Agent2"])
    
    assert not success
    assert "not a valid agent" in msg.lower()
