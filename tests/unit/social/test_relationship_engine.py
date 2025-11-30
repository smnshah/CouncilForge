import pytest
from src.social.relationship_engine import Relationship, update_relationship, apply_message_effects

def test_relationship_initialization():
    """Test Relationship initializes with default values."""
    rel = Relationship()
    assert rel.trust == 0
    assert rel.resentment == 0
    assert rel.score == 0

def test_update_relationship_support():
    """Test support_agent updates relationships (Phase 1.5 values)."""
    rel = Relationship()
    rel = update_relationship(rel, "support_agent")
    assert rel.trust == 3  # Phase 1.5: smaller delta
    assert rel.resentment == -2
    assert rel.score == 5  # 3 - (-2)

def test_update_relationship_oppose():
    """Test oppose_agent updates relationships (Phase 1.5 values)."""
    rel = Relationship()
    rel = update_relationship(rel, "oppose_agent")
    assert rel.trust == -3
    assert rel.resentment == 3
    assert rel.score == -6  # -3 - 3

def test_update_relationship_clamping():
    """Test relationships clamp at -50 to +50 (Phase 1.5 range)."""
    rel = Relationship(trust=48, resentment=-48)
    rel = update_relationship(rel, "support_agent")  # +3 trust, -2 resentment
    assert rel.trust == 50  # Clamped at 50 (was going to 51)
    assert rel.resentment == -50  # Clamped at -50 (was going to -50)
    
    # Test other direction
    rel2 = Relationship(trust=-48, resentment=48)
    rel2 = update_relationship(rel2, "oppose_agent")  # -3 trust, +3 resentment
    assert rel2.trust == -50  # Clamped at -50
    assert rel2.resentment == 50  # Clamped at 50

def test_apply_message_effects_friendly():
    """Test friendly message effects."""
    rel = Relationship()
    rel = apply_message_effects(rel, "I support you friend")
    assert rel.trust == 5

def test_apply_message_effects_hostile():
    """Test hostile message effects."""
    rel = Relationship()
    rel = apply_message_effects(rel, "I hate you enemy")
    assert rel.trust == -5
    assert rel.resentment == 5

def test_apply_message_effects_neutral():
    """Test neutral message effects."""
    rel = Relationship()
    rel = apply_message_effects(rel, "neutral")
    assert rel.trust == 1
    assert rel.resentment == 0



def test_unknown_action_ignored():
    """Test unknown action types are ignored."""
    rel = Relationship()
    rel_before = Relationship(trust=rel.trust, resentment=rel.resentment)
    rel = update_relationship(rel, "unknown_action")
    # Should be unchanged
    assert rel.trust == rel_before.trust
    assert rel.resentment == rel_before.resentment
