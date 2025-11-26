import pytest
from src.social.emotion_engine import (
    update_emotions, 
    get_emotional_bias, 
    normalize_emotion, 
    get_default_emotions,
    MIN_EMOTION,
    MAX_EMOTION
)

def test_normalize_emotion():
    assert normalize_emotion(60.0) == MAX_EMOTION
    assert normalize_emotion(-60.0) == MIN_EMOTION
    assert normalize_emotion(10.0) == 10.0

def test_update_emotions_support():
    emotions = get_default_emotions()
    updated = update_emotions(emotions, "support_agent", is_target=True)
    
    assert updated["trust"] == 5.0
    assert updated["resentment"] == -2.0
    assert updated["admiration"] == 1.0

def test_update_emotions_oppose():
    emotions = get_default_emotions()
    updated = update_emotions(emotions, "oppose_agent", is_target=True)
    
    assert updated["resentment"] == 5.0
    assert updated["trust"] == -5.0
    assert updated["fear"] == 1.0

def test_update_emotions_sabotage():
    emotions = get_default_emotions()
    updated = update_emotions(emotions, "sabotage", is_target=True)
    
    assert updated["resentment"] == 15.0
    assert updated["trust"] == -10.0
    assert updated["fear"] == 5.0

def test_update_emotions_not_target():
    # If not target, usually no direct emotional change unless specified (like consume_resource)
    emotions = get_default_emotions()
    updated = update_emotions(emotions, "support_agent", is_target=False)
    
    assert updated["trust"] == 0.0 # No change

def test_update_emotions_consume_resource():
    emotions = get_default_emotions()
    updated = update_emotions(emotions, "consume_resource", is_target=False)
    
    assert updated["resentment"] == 1.0

def test_get_emotional_bias():
    emotions = get_default_emotions()
    emotions["trust"] = 20.0
    emotions["resentment"] = -10.0
    
    biases = get_emotional_bias(emotions)
    
    # Trust should boost support
    assert biases["support_agent"] > 0
    # Resentment is low, so oppose should be negative (suppressed)
    assert biases["oppose_agent"] < 0

def test_get_emotional_bias_hostile():
    emotions = get_default_emotions()
    emotions["trust"] = -20.0
    emotions["resentment"] = 30.0
    
    biases = get_emotional_bias(emotions)
    
    # High resentment -> boost oppose
    assert biases["oppose_agent"] > 0
    # Low trust -> suppress support
    assert biases["support_agent"] < 0
