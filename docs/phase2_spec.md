# CouncilForge Phase 2 Specification

============================================================
1. PROJECT CONTEXT
============================================================

CouncilForge is a local LLM-based multi-agent simulation engine using:
- Python
- Poetry
- Pydantic
- httpx
- loguru
- YAML
- Ollama (local LLM runtime)

Phase 1 is already complete. Phase 2 expands the simulation world, adds memory, new action types, inter-agent messaging, improved personas, and a more robust prompt structure.

You must NOT rewrite or over-complicate the system.
You must extend it cleanly and safely.

============================================================
2. PHASE 2 REQUIREMENTS
Implement ALL of the following modules.
============================================================

------------------------------------------------------------
A. WORLD EXPANSION
------------------------------------------------------------
Update WorldState Pydantic model:

Add these new fields:
- food: int
- energy: int
- infrastructure: int
- morale: int
- crisis_level: int        # derived each turn
- overall_health: int      # derived each turn
- message_queue: List[Message]

Derived metrics (compute each turn, not manually set):
- crisis_level = max(0, 100 - (resource_level + food + energy + infrastructure + morale) // 5)
- overall_health = (resource_level + stability + food + energy + morale) // 5

Requirements:
- Clamp all values to >= 0
- Computation must occur in the world engine after each action
- Keep implementation small and clear

------------------------------------------------------------
B. ACTION SYSTEM EXPANSION
------------------------------------------------------------
Update Action model:
- type: str
- target: str                # "world" or an agent name
- resource: Optional[str]    # for resource actions
- amount: Optional[int]      # small ints (default 5)
- message: Optional[str]     # for messaging
- reason: str

New allowed actions:

Resource actions:
- improve_resource
- consume_resource
- boost_morale
- strengthen_infrastructure

Social actions:
- negotiate
- request_help
- trade
- sabotage

Messaging:
- send_message

Validation rules:
- Invalid actions → convert to "pass"
- Log invalid attempts
- World engine must handle each new action cleanly and with minimal side effects

------------------------------------------------------------
C. MEMORY SYSTEM UPGRADE
------------------------------------------------------------
1. Sliding Window Memory
- Increase recent history from 2 → 6 turns.
- Summaries must be short and standardized.

2. Relationship Table
Each agent maintains:
relationships = {
    "AgentName": {
        "trust": int,
        "resentment": int
    }
}

Update rules:
- Support → trust +
- Negotiate → trust + small
- Trade → trust + medium (if successful)
- Sabotage → resentment + large
- Oppose → resentment + small

Expose these values in the prompt template.

------------------------------------------------------------
D. PERSONA SYSTEM UPGRADE
------------------------------------------------------------
Update persona YAML + Pydantic model to include:
- archetype: str
- core_values: list
- dominant_trait: str
- secondary_trait: str
- decision_biases: list
- preferred_resources: list
- conflict_style: "aggressive" | "diplomatic" | "passive"
- cooperation_style: "helpful" | "neutral" | "selfish"
- risk_preference: "low" | "medium" | "high"

Personas must be fully included in the prompt context.
No complex logic required—LLM will interpret traits naturally.

------------------------------------------------------------
E. INTER-AGENT MESSAGING
------------------------------------------------------------
Add Message model:
```python
class Message(BaseModel):
    sender: str
    recipient: str
    text: str
    turn_sent: int
```

Message system requirements:
- World maintains message_queue
- Agents generate messages via send_message action
- Messages delivered at the start of next turn
- Agents see messages in their prompt input
- Clear logging

Keep this extremely simple.

------------------------------------------------------------
F. PROMPT TEMPLATE UPGRADE
------------------------------------------------------------
Rewrite the LLM prompt template to include structured sections:
- Persona block
- Current world summary (including new world fields)
- Agent memory
    - last 6 turns
    - relationship table
- Messages received
- Allowed actions
- STRICT JSON schema
- STRICT instructions to output ONLY valid JSON
- Example JSON output

Requirements:
- Full schema MUST be included in every prompt
- The agent must re-prompt on invalid JSON
- The code must attempt JSON auto-repair before fallback

============================================================
3. CODING STANDARDS
Follow these EXACT engineering rules.
============================================================

You MUST write code like a senior-level software engineer:
- Small, focused functions
- Pydantic for all data models
- 100% type annotated
- Clear variable names
- Clean separation of concerns
- No clever abstractions
- No unnecessary inheritance
- Docstrings for every class and method
- Inline comments explaining non-obvious logic
- World engine must remain deterministic

============================================================
4. TESTING REQUIREMENTS
You MUST write tests.
============================================================

Implement the following in tests/:

Unit Tests:
- World engine updates
- Action validation
- Action effects (resource changes, morale, infrastructure)
- Relationship updates
- Memory expansion logic
- Message queue logic
- Persona model loading

Integration Tests:
- A 3-agent, 5-turn simulation using mocked LLM responses
- Messages passing between agents
- Multi-resource world evolution
- JSON parsing + fallback logic

Tests must be simple, deterministic, and readable.
Use pytest best practices.

============================================================
5. IMPLEMENTATION ORDER
Follow this sequence exactly.
============================================================
1. Update all data models
    - WorldState → Action → Persona → Message
2. Update world engine
    - Handle new actions
    - Compute derived metrics
    - Clamp resource values
    - Deliver messages
3. Implement memory system upgrade
    - 6-turn sliding window
    - Relationship table
4. Implement messaging system
5. Update prompt template
6. Update simulation controller
7. Update persona YAMLs
8. Implement all unit + integration tests
9. Run full simulation to verify stability
