import pytest
from src.world.engine import World
from src.core.models import WorldState, Action, ActionType
from src.config.settings import WorldConfig

def make_world_config(**kwargs):
    """Helper to create WorldConfig for testing."""
    defaults = {
        'initial_treasury': 50,
        'initial_food': 50,
        'initial_energy': 50,
        'initial_infrastructure': 50,
        'initial_morale': 50
    }
    defaults.update(kwargs)
    return WorldConfig(**defaults)

def test_support_agent_applies_cost_reduction():
    """Test that support_agent sets 50% cost reduction."""
    world = World(make_world_config())
    
    # Agent1 supports Agent2
    action = Action(type=ActionType.SUPPORT_AGENT, target="Agent2", reason="helping")
    success, msg = world.apply_action("Agent1", action, ["Agent1", "Agent2"])
    
    assert success
    assert world.state.cost_modifiers["Agent2"] == 0.5
    assert "50% less" in msg
    assert world.state.morale == 55  # +5 from support

def test_oppose_agent_applies_cost_increase():
    """Test that oppose_agent sets 50% cost increase."""
    world = World(make_world_config())
    
    # Agent1 opposes Agent2
    action = Action(type=ActionType.OPPOSE_AGENT, target="Agent2", reason="blocking")
    success, msg = world.apply_action("Agent1", action, ["Agent1", "Agent2"])
    
    assert success
    assert world.state.cost_modifiers["Agent2"] == 1.5
    assert "50% more" in msg
    assert world.state.morale == 47  # -3 from oppose

def test_supported_action_costs_less():
    """Test that a supported agent pays 50% less on resource actions."""
    world = World(make_world_config())
    
    # Agent1 supports Agent2
    support_action = Action(type=ActionType.SUPPORT_AGENT, target="Agent2", reason="helping")
    world.apply_action("Agent1", support_action, ["Agent1", "Agent2"])
    
    # Agent2 uses improve_infrastructure (normally costs 4 treasury)
    action = Action(type=ActionType.IMPROVE_INFRASTRUCTURE, target="world", reason="building")
    success, msg = world.apply_action("Agent2", action, ["Agent1", "Agent2"])
    
    assert success
    assert world.state.treasury == 48  # 50 - 2 (50% of 4)
    assert world.state.infrastructure == 58  # 50 + 8
    assert "SUPPORTED" in msg
    assert "paid 50% less" in msg

def test_opposed_action_costs_more():
    """Test that an opposed agent pays 50% more on resource actions."""
    world = World(make_world_config())
    
    # Agent1 opposes Agent2
    oppose_action = Action(type=ActionType.OPPOSE_AGENT, target="Agent2", reason="blocking")
    world.apply_action("Agent1", oppose_action, ["Agent1", "Agent2"])
    
    # Agent2 uses improve_infrastructure (normally costs 4 treasury)
    action = Action(type=ActionType.IMPROVE_INFRASTRUCTURE, target="world", reason="building")
    success, msg = world.apply_action("Agent2", action, ["Agent1", "Agent2"])
    
    assert success
    assert world.state.treasury == 44  # 50 - 6 (150% of 4)
    assert world.state.infrastructure == 58  # 50 + 8
    assert "OPPOSED" in msg
    assert "paid 50% more" in msg

def test_modifier_clears_after_use():
    """Test that cost modifiers are one-time use and clear after application."""
    world = World(make_world_config())
    
    # Agent1 supports Agent2
    support_action = Action(type=ActionType.SUPPORT_AGENT, target="Agent2", reason="helping")
    world.apply_action("Agent1", support_action, ["Agent1", "Agent2"])
    
    assert "Agent2" in world.state.cost_modifiers
    
    # Agent2 uses an action
    action = Action(type=ActionType.IMPROVE_FOOD, target="world", reason="feeding")
    world.apply_action("Agent2", action, ["Agent1", "Agent2"])
    
    # Modifier should be cleared
    assert "Agent2" not in world.state.cost_modifiers
    
    # Next action should have normal cost
    action2 = Action(type=ActionType.IMPROVE_FOOD, target="world", reason="feeding again")
    world.apply_action("Agent2", action2, ["Agent1", "Agent2"])
    
    # Should cost normal 3 energy
    # int(3 * 0.5) = 1 for first action
    # 3 for second action
    # Total: 50 - 1 - 3 = 46
    assert world.state.energy == 46  # 50 - 1 (first, supported) - 3 (second, normal)

def test_opposed_agent_cannot_afford():
    """Test that opposition can prevent an action if agent can't afford higher cost."""
    world = World(make_world_config(initial_treasury=5))
    
    # Agent1 opposes Agent2
    oppose_action = Action(type=ActionType.OPPOSE_AGENT, target="Agent2", reason="blocking")
    world.apply_action("Agent1", oppose_action, ["Agent1", "Agent2"])
    
    # Agent2 tries improve_infrastructure (costs 4, but 50% more = 6)
    # Treasury is only 5, so should fail
    action = Action(type=ActionType.IMPROVE_INFRASTRUCTURE, target="world", reason="building")
    success, msg = world.apply_action("Agent2", action, ["Agent1", "Agent2"])
    
    assert not success
    assert "Insufficient treasury" in msg
    assert world.state.infrastructure == 50  # Unchanged
