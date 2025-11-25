from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

class ActionType(str, Enum):
    INCREASE_RESOURCE = "increase_resource"
    DECREASE_RESOURCE = "decrease_resource"
    SUPPORT_AGENT = "support_agent"
    OPPOSE_AGENT = "oppose_agent"
    PASS = "pass"

class Action(BaseModel):
    type: ActionType
    target: str = Field(..., description="Target of the action (e.g., 'world' or agent name)")
    reason: str = Field(..., description="Short explanation for the action")

class WorldState(BaseModel):
    resource_level: int = Field(..., description="Current resource level of the world")
    stability: int = Field(..., description="Current stability level of the world")
    turn: int = Field(..., description="Current turn number")

class AgentState(BaseModel):
    last_action: Optional[str] = Field(None, description="The last action taken by the agent")

class Persona(BaseModel):
    name: str
    description: str
    goals: List[str]
    behavior_biases: List[str]
