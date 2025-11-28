# Phase 5: Simplification for 8B Model Compatibility

**Status**: Complete  
**Date**: November 2025  
**Target**: llama3.1:8b (local)

---

## 1. Problem Statement

After implementing Phases 1-4, the simulation failed with llama3.1:8b:
- 30% JSON parse errors (malformed output)
- Repetitive action spam
- No emergent social behavior
- Prompt complexity overwhelmed 8b model

**Root Cause**: Over-engineering. Phases 2-4 optimized for 70b+ models, not local 8b.

---

## 2. Design Philosophy

**"Radical Simplification"**
- Reduce prompt from 1200 → 700 tokens (50% reduction)
- Reduce actions from 22 → 8 (64% reduction)  
- Remove complex social systems, add simple mechanics
- Simple rules → Emergent complexity

---

## 3. Key Changes (Phase 1.5)

### Action Space Reduction
**Before (22 actions)**: form_alliance, break_alliance, accuse_agent, sabotage_agent, consume_resource, hoard_resource, improve_resource, distribute_resource, call_vote, declare_crisis, etc.

**After (8 actions)**:
```
Resource (4): improve_food, improve_energy, improve_infrastructure, boost_morale
Social (3): support_agent, oppose_agent, send_message  
Other (1): pass
```

### WorldState Simplification
**Removed**: resource_level, stability, overall_health, policy_cooldowns  
**Added**: treasury (national budget), cost_modifiers (support/oppose effects)  
**Kept**: food, energy, infrastructure, morale, crisis_level, turn

### Cost System (NEW)
All resource actions now cost other resources:
```python
improve_food: +8 food, costs 3 energy
improve_energy: +8 energy, costs 3 treasury
improve_infrastructure: +8 infrastructure, costs 4 treasury
boost_morale: +8 morale, costs 2 food
```
**Effect**: Prevents spam, creates strategic tradeoffs

### Relationship Simplification
**Before**: trust, resentment, admiration, fear + full history  
**After**: trust, resentment only (-50 to +50 range)

### Prompt Restructuring
**Before**: 10 sections, 1200 tokens, 1 JSON example  
**After**: 7 sections, 700 tokens, 4 JSON examples (including "cannot afford")

Key improvements:
- Last 2 turns of history (vs 6)
- Only significant relationships shown (score > 3)
- Clear cost descriptions
- Explicit 4-step reasoning instructions

### Removed Systems
- EmotionEngine (6 emotion types)
- InterpersonalGoals (dynamic goal generation)
- DecisionEngine (complex bias calculations)
- InteractionTriggers (event-based triggers)
- PromptBuilder (moved to inline formatting)

**Total**: 5 modules removed, -737 lines of code (-26%)

---

## 4. Strategic Re-addition (Phase 1.6)

After achieving stability (0% errors), added back strategic depth:

### Conflicting Goals
```yaml
Eldric: "Keep infrastructure above 60", "Limit food spending"
Lyra: "Keep food above 60", "Limit infrastructure spending"  
Thorne: "Keep treasury above 30", "Balance all resources"
```
**Effect**: Natural conflict without programming

### Cost Modifiers
```
support_agent: Target's next action costs 50% less
oppose_agent: Target's next action costs 50% more
Duration: 1 turn (one-time use)
```
**Effect**: Concrete strategic value for social actions

### Prompt Reordering
Social actions listed FIRST (primacy effect) with clear benefits:
```
1. support_agent - They pay 50% less next turn
2. oppose_agent - They pay 50% more next turn
3. send_message - Builds relationships
```

### Modifier Status Display
```
"*** YOU ARE SUPPORTED: Your next resource action costs 50% less! ***"
```
Shown in world state section when active.

---

## 5. Results

| Metric | Phase 4 | Phase 1.5 | Phase 1.6 |
|--------|---------|-----------|-----------|
| JSON Errors | 30% | 0% | 7% (recoverable) |
| Action Spam | High | None | None |
| Social Actions | 0% | 0% | **27%** ✅ |
| Emergent Behavior | None | None | Cooperation ✅ |
| Code Size | 2,875 LOC | 2,138 LOC | 2,148 LOC |

**Phase 1.6 Highlights**:
- Reciprocal cooperation (Eldric → Lyra → Eldric)
- Repeated support patterns (Thorne → Lyra 3 times)
- Strategic use of cost modifiers (visible savings)
- 100% test coverage (46/46 passing)

---

## 6. Architecture

```
SimulationController
├── World
│   ├── WorldState (6 metrics + cost_modifiers)
│   └── Cost-based action effects
├── Agents (3)
│   ├── Persona (name, archetype, traits, goals)
│   └── Relationships (trust/resentment only)
└── Social Systems
    ├── RelationshipEngine (simplified)
    └── MessageParser (tone detection)
```

**vs Phase 4**: 5 modules → 2 modules

---

## 7. Key Learnings

1. **Less is More**: Fewer, clearer actions → Better 8b decisions
2. **Concrete > Abstract**: "50% cost" > "builds relationship"
3. **Structure Enables Emergence**: Simple cost system → Complex cooperation
4. **Examples Matter**: 4 JSON examples → 0% parse errors

---

## 8. Next Steps

### Phase 1.7 (Quick Wins)
- **Voting System**: Actions > threshold cost need 2/3 approval
- **Crisis Events**: Random urgent events ("Famine Warning!")
- **Message Persuasion**: Messages affect next-turn behavior

### Phase 2.0 (Strategic Depth)
- **Multi-turn Investments**: Actions with delayed payoffs
- **Political Coalitions**: Form/break alliances
- **Scarcity Scenarios**: Zero-sum resource competition
- **Relationship Thresholds**: High trust unlocks actions

All designed to work within 8b token budget (~300 tokens remaining).

**Not Feasible for 8b**:
- Open-ended goal creation
- Multi-turn planning (5+ steps ahead)
- Complex freeform negotiations

These require 70b+ models due to creative reasoning demands.

---

## 9. Testing

**Coverage**: 100% (46/46 tests passing)
- Unit tests: Core models, world engine, relationships, agents
- Integration tests: Full simulation flow with cost modifiers
- Live tests: llama3.1:8b verification (5-turn simulation)

---

## 10. Migration from Phase 4

**Removed**: 5 social module files, 5 test files  
**Modified**: models.py, engine.py, llm_agent.py, relationship_engine.py, personas.yaml  
**Breaking Changes**: ActionType enum, WorldState structure, Relationship model

See git history for detailed migration path.
