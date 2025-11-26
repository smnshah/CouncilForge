# CouncilForge Phase 3 Specification

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

Phase 1 and 2 are already complete.
Phase 3 gives the system the mind to use the social actions: urgency, emotion, motive, personality, conflict style, cooperation style, memory, and responsiveness.

After this phase, agents should no longer behave as isolated stat-mutators.
They should behave like characters reacting to each other, shaping alliances, rivalries, and making decisions that feel natural.

You must NOT rewrite or over-complicate the system.
You must extend it cleanly and safely.

============================================================
2. PHASE 3 REQUIREMENTS
Implement ALL of the following modules.
============================================================

------------------------------------------------------------
MODULE 1 — Relationship Dynamics System
------------------------------------------------------------
1.1 Relationship Data Structure Redesign

Update the relationship structure to:

```python
Relationship = {
    "trust": int,         # -100 to +100
    "resentment": int,    # -100 to +100
    "history": List[str], # optional short log of interactions
}
```

Every agent maintains this for every other agent.

1.2 Relational Delta Rules

When a social action occurs:

| Action | Trust Δ | Resentment Δ |
| :--- | :--- | :--- |
| support_agent | +10 | -5 |
| oppose_agent | -10 | +10 |
| negotiate | +5 | 0 |
| request_help (and accepted) | +10 | 0 |
| request_help (ignored/rejected) | -5 | +5 |
| trade (successful) | +7 | -3 |
| sabotage | -25 | +20 |
| send_message (neutral) | +1 | 0 |
| send_message (friendly) | +3 | -1 |
| send_message (hostile) | -3 | +3 |

Implementation requirement:
Add a `relationship_engine.py` with functions:

- `update_relationships(actor, target, action)`
- `apply_message_effects(actor, target, text)`
- `get_relationship_score(actor, target)` (trust - resentment)

1.3 Relationship Score Helper

Calculate:
```python
score = trust - resentment
range = -200 to +200
```

Expose scores to the agent prompt as:
`"relationship_score_with_X": <computed score>`

Agents use this score to determine whether to choose supportive, cooperative, or hostile actions.

------------------------------------------------------------
MODULE 2 — Social Action Selection Bias Layer
------------------------------------------------------------
2.1 New Step in Decision Pipeline

Before the LLM chooses an action, compute weighted probabilities reflecting agent traits and relationships.

Add a function:
`compute_action_biases(agent, world_state, relationships)`

It should generate a JSON object like:
```json
{
  "support_agent": 0.2,
  "oppose_agent": 0.1,
  "negotiate": 0.15,
  "request_help": 0.1,
  "trade": 0.15,
  "sabotage": 0.05,
  "send_message": 0.1,
  "other_world_actions": 0.15
}
```

2.2 Bias Inputs

Biases depend on:
- **Personality Traits**: Conflict style, Cooperation style, Risk preference
- **Biases**: loss aversion, optimism bias, etc.
- **Relationship Scores**:
    - score > 50 → more likely to support, message, trade
    - score < -50 → more likely to oppose, sabotage
    - -20 < score < 20 → more likely to negotiate
- **World Pressures**:
    - Crisis Level > 60 → more negotiation, more request_help
    - Stability < 40 → higher chance of political conflict (oppose, sabotage)
    - Morale < 40 → send_message or support_agent increases

2.3 Deliver Bias Summary into LLM Prompt

Inject this into the LLM prompt as a dedicated section:

```
Action Biases (Pre-Computed):
- support_agent: 0.2
- oppose_agent: 0.1
...
LLM MUST consider these biases when choosing actions.
```

------------------------------------------------------------
MODULE 3 — Interaction Incentive System
------------------------------------------------------------
Agents should feel a reason to interact, not only mutate world stats.

3.1 Interaction Triggers

Agents are more likely to interact when any of these conditions are true:
- Someone targeted them in the last 2 turns
- Their resource preference is threatened
- Their goals are not being met for multiple turns
- Their relationship score crosses thresholds
- Crisis level spikes
- They receive a message (new stimuli)

3.2 Historical Awareness

Add a new world field piped into the prompt:

```
recent_interactions_targeting_me: [
   "Turn 4: Lyra opposed Eldric",
   "Turn 3: Thorne sent_message Eldric: '...' "
]
```

Agents should react to this in their decision-making.

------------------------------------------------------------
MODULE 4 — Message Interpretation Engine
------------------------------------------------------------
When an agent receives a message, parse it to determine tone:

Add `message_parser.py` with:
`parse_message_tone(text) -> "friendly" | "neutral" | "hostile"`

Use simple heuristics:
- Keywords (thanks, appreciate, help) → friendly
- Accusations (why did you…), capital letters, negative sentiment → hostile

Apply relationship deltas accordingly.

Agents should also reference incoming messages in next prompt:
```
Messages Received:
- From Lyra: "We should collaborate more."
Tone: friendly
```

------------------------------------------------------------
MODULE 5 — Action Diversity Pressure
------------------------------------------------------------
Your agents kept repeating the same action. Fix this with:

5.1 Turn-Level Diversity

Track the last N (3–5) actions per agent.

Inject into prompt:
```
Recent Agent Actions:
- Turn 3: strengthened_infrastructure
- Turn 2: strengthened_infrastructure
- Turn 1: strengthened_infrastructure
```

LLM MUST NOT repeat the same action excessively unless strongly justified.

5.2 Hard Constraints

If the last 3 actions were identical, lower probability weight for that action to near-zero unless:
- the crisis demands it
- the agent's goals require it

5.3 Implement Helper

Add:
`apply_repetition_penalty(biases, agent_history)`

------------------------------------------------------------
MODULE 6 — Updated Prompt Contract for Agents
------------------------------------------------------------
Every agent prompt MUST now include:

New sections:
- Relationship summary with scores
- Action bias table
- Messages received + tone
- Interaction triggers
- Agent’s last 3 actions
- Social incentives + pressure notes
- "Do not repeat the same action repeatedly unless justified."

Updated Action Instructions:
Add:
4. You MUST consider interpersonal dynamics when choosing actions.
5. Social actions are encouraged when relationship scores or recent interactions are relevant.
6. Avoid repeatedly selecting world-only actions unless they directly align with your goals AND world conditions.

------------------------------------------------------------
MODULE 7 — Tests Required
------------------------------------------------------------
Make sure to create unit tests that cover the major components of this project. If a unit test does not exist, create it. If a unit test exists for a component that you change, make sure to update the tests. We should have tests corresponding to each component, such as "test_models". Update the integration tests as well to reflect any new behavior.

============================================================
CODING STANDARDS
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

