from enum import Enum
from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from src.social.relationship_engine import Relationship

class ActionType(str, Enum):
    # Resource Actions (5 - added generate_treasury)
    IMPROVE_FOOD = "improve_food"
    IMPROVE_ENERGY = "improve_energy"
    IMPROVE_INFRASTRUCTURE = "improve_infrastructure"
    BOOST_MORALE = "boost_morale"
    GENERATE_TREASURY = "generate_treasury"
    
    # Social Actions (3)
    SUPPORT_AGENT = "support_agent"
    OPPOSE_AGENT = "oppose_agent"
    SEND_MESSAGE = "send_message"
    
    # Other (1)
    PASS = "pass"

class Message(BaseModel):
    sender: str
    recipient: str
    content: str
    turn_sent: int

class Action(BaseModel):
    type: ActionType
    target: str = Field(..., description="Target of the action (e.g., 'world' or agent name)")
    message: Optional[str] = Field(None, description="Content for messaging actions", alias="content")
    reason: Optional[str] = Field(None, description="Explanation for the action", alias="reasoning")
    
    class Config:
        populate_by_name = True

class WorldState(BaseModel):
    # Core Resources
    treasury: int = Field(..., description="Nation's wealth/budget for development")
    food: int = Field(..., description="Food supply level")
    energy: int = Field(..., description="Energy level")
    infrastructure: int = Field(..., description="Infrastructure level")
    morale: int = Field(..., description="Public morale level")
    
    # Derived Metrics
    crisis_level: int = Field(0, description="Derived crisis indicator (0-100)")
    
    # Messaging System
    message_queue: List[Message] = Field(default_factory=list, description="Queue of messages to be delivered")
    
    # Cost Modifiers (Phase 1.6: Support/Oppose mechanics)
    cost_modifiers: Dict[str, float] = Field(
        default_factory=dict,
        description="Agent name -> cost multiplier (0.5 for support, 1.5 for oppose). One-time use."
    )
    
    turn: int = Field(..., description="Current turn number")

class AgentState(BaseModel):
    last_action: Optional[str] = Field(None, description="The last action taken by the agent")
    
    # Phase 3 Fields
    relationships: Dict[str, Relationship] = Field(default_factory=dict, description="Relationships with other agents")
    recent_actions: List[str] = Field(default_factory=list, description="History of recent actions for diversity check")
    messages_received: List[Message] = Field(default_factory=list, description="Messages received this turn")
    recent_interactions_targeting_me: List[str] = Field(default_factory=list, description="Log of recent interactions targeting this agent")
    
    # Phase 4 Fields
    emotions: Dict[str, Dict[str, float]] = Field(default_factory=dict, description="Emotions toward other agents")
    goals: Dict[str, Optional[str]] = Field(default_factory=dict, description="Interpersonal goals")

class Persona(BaseModel):
    name: str
    description: str
    voice_instructions: Optional[str] = None
    goals: List[str]
    behavior_biases: List[str] # Keeping for backward compatibility
    
    # Phase 2 Traits
    archetype: str = "Generic"
    core_values: List[str] = Field(default_factory=list)
    dominant_trait: str = "Neutral"
    secondary_trait: str = "None"
    decision_biases: List[str] = Field(default_factory=list)
    preferred_resources: List[str] = Field(default_factory=list)
    conflict_style: str = "diplomatic"
    cooperation_style: str = "neutral"
    risk_preference: str = "medium"
