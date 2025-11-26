import pytest
from src.social.relationship_engine import Relationship, update_relationship, apply_message_effects, get_relationship_score

def test_relationship_initialization():
    rel = Relationship()
    assert rel.trust == 0
    assert rel.resentment == 0
    assert rel.score == 0
    assert rel.history == []

def test_update_relationship_support():
    rel = Relationship()
    rel = update_relationship(rel, "support_agent", "Supported agent")
    assert rel.trust == 10
    assert rel.resentment == -5
    assert rel.score == 15
    assert "Supported agent" in rel.history

def test_update_relationship_sabotage():
    rel = Relationship()
    rel = update_relationship(rel, "sabotage", "Sabotaged agent")
    assert rel.trust == -25
    assert rel.resentment == 20
    assert rel.score == -45

def test_update_relationship_clamping():
    rel = Relationship(trust=95, resentment=-95)
    rel = update_relationship(rel, "support_agent") # +10 trust, -5 resentment
    assert rel.trust == 100 # Clamped at 100
    assert rel.resentment == -100 # Clamped at -100

def test_apply_message_effects_friendly():
    rel = Relationship()
    rel = apply_message_effects(rel, "friendly", "Hello friend")
    assert rel.trust == 3
    assert rel.resentment == -1
    assert "Received friendly message: 'Hello friend'" in rel.history

def test_apply_message_effects_hostile():
    rel = Relationship()
    rel = apply_message_effects(rel, "hostile", "I hate you")
    assert rel.trust == -3
    assert rel.resentment == 3
