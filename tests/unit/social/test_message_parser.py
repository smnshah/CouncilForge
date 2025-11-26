import pytest
from src.social.message_parser import parse_message_tone

def test_parse_message_tone_friendly():
    assert parse_message_tone("Thanks for your help!") == "friendly"
    assert parse_message_tone("We should cooperate.") == "friendly"
    assert parse_message_tone("I appreciate it.") == "friendly"

def test_parse_message_tone_hostile():
    assert parse_message_tone("You are my enemy!") == "hostile"
    assert parse_message_tone("I will destroy you.") == "hostile"
    assert parse_message_tone("WHY DID YOU DO THAT") == "hostile" # Caps

def test_parse_message_tone_neutral():
    assert parse_message_tone("I am consuming resources.") == "neutral"
    assert parse_message_tone("The resource level is 50.") == "neutral"
