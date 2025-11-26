from enum import Enum
from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from src.social.relationship_engine import Relationship

class ActionType(str, Enum):
    # Resource Actions
    INCREASE_RESOURCE = "increase_resource" # Legacy support? Spec says "improve_resource"
    DECREASE_RESOURCE = "decrease_resource" # Legacy support? Spec says "consume_resource"
    IMPROVE_RESOURCE = "improve_resource"
    CONSUME_RESOURCE = "consume_resource"
    BOOST_MORALE = "boost_morale"
    STRENGTHEN_INFRASTRUCTURE = "strengthen_infrastructure"
    
    # Social Actions
    SUPPORT_AGENT = "support_agent"
    OPPOSE_AGENT = "oppose_agent"
    NEGOTIATE = "negotiate"
    REQUEST_HELP = "request_help"
    TRADE = "trade"
    SABOTAGE = "sabotage"
    
    # Messaging
    SEND_MESSAGE = "send_message"
    
    # Other
    PASS = "pass"

class Message(BaseModel):
    sender: str
    recipient: str
    text: str
    tone: str = "neutral"
    turn_sent: int

class Action(BaseModel):
    type: ActionType
    target: str = Field(..., description="Target of the action (e.g., 'world' or agent name)")
    resource: Optional[str] = Field(None, description="Resource type for resource actions")
    amount: Optional[int] = Field(5, description="Amount for resource actions")
    message: Optional[str] = Field(None, description="Content for messaging actions")
    reason: str = Field(..., description="Short explanation for the action")

class WorldState(BaseModel):
    resource_level: int = Field(..., description="Current resource level of the world")
    stability: int = Field(..., description="Current stability level of the world")
    
    # New Phase 2 Fields
    food: int = Field(0, description="Food level")
    energy: int = Field(0, description="Energy level")
    infrastructure: int = Field(0, description="Infrastructure level")
    morale: int = Field(0, description="Morale level")
    
    # Derived metrics
    crisis_level: int = Field(0, description="Derived crisis level")
    overall_health: int = Field(0, description="Derived overall health")
    
    message_queue: List[Message] = Field(default_factory=list, description="Queue of messages to be delivered")
    
    turn: int = Field(..., description="Current turn number")

class AgentState(BaseModel):
    last_action: Optional[str] = Field(None, description="The last action taken by the agent")
    
    # Phase 3 Fields
    relationships: Dict[str, Relationship] = Field(default_factory=dict, description="Relationships with other agents")
    recent_actions: List[str] = Field(default_factory=list, description="History of recent actions for diversity check")
    messages_received: List[Message] = Field(default_factory=list, description="Messages received this turn")
    recent_interactions_targeting_me: List[str] = Field(default_factory=list, description="Log of recent interactions targeting this agent")

class Persona(BaseModel):
    name: str
    description: str
    goals: List[str]
    behavior_biases: List[str] # Keeping for backward compatibility if needed, but spec says "decision_biases"
    
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
