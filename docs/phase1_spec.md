# CouncilForge - Project Specification

## 1. Problem Definition
We need a local, modular, and extensible multi-agent simulation engine where 3-5 AI agents interact in a turn-based environment. The system must be powered by a local LLM (llama3.1:8b via Ollama) and designed specifically for "AIS-driven development"—meaning the code must be clean, logically separated, safe for AI agents to read, understand, and extend, and easy for AI systems to iterate on.

## 2. System Purpose and Goals
**Primary Goal:** Create a minimal viable simulation engine (Phase 1) that successfully runs a multi-agent loop with local LLM reasoning.
**Design Philosophy:** Modular, readable, type-safe, future-proof, and AI-friendly.
**Target Environment:** Local execution, Python-based, Ollama backend, using llama3.1:8b for all agent reasoning.

## 3. Minimal Viable System (Phase 1)
The Phase 1 system will consist of:

*   **World State:** Small, deterministic, numeric/categorical state.
*   **Agents:** 3–5 agents, each with a persona and simple internal state.
*   **Simulation Loop:** A turn-based controller orchestrating sequential turns.
*   **LLM Integration:** Local LLM integration for choosing actions from a discrete action set.
*   **Logging:** Console for narrative, file for raw LLM responses.
*   **Configuration:** Config-driven initialization for everything.

**Exclusions for Phase 1:**
*   No Graphical User Interface (GUI).
*   No persistent long-term memory (focus is on clean architecture + stable loop).
*   No swarm logic or Monte Carlo Tree Search.
*   No reinforcement learning.

## 4. Component Breakdown

### A. Core Models (models/)
Pydantic models will define the data structure for:
*   **WorldState:** Minimal and deterministic.
    *   `resource_level` (int)
    *   `stability` (int)
    *   `turn` (int)
*   **AgentState:** Stores only simple internal info for Phase 1.
    *   `last_action` (str | None)
*   **Action:** Represents a structured choice made by an agent. Must match the discrete action set.
*   **Persona:** Lightweight descriptor loaded from YAML.
    *   `name` (str)
    *   `description` (str)
    *   `goals` (list[str])
    *   `behavior_biases` (list[str])

### B. LLM Client (llm/)
Wrapper around `httpx` to communicate with Ollama.
*   **Responsibilities:**
    *   Handle JSON schema validation.
    *   Implement retry logic: 3 attempts, fallback to "pass" action if invalid.
    *   Ensure Phase 1 simulation stability.

### C. Agent System (agents/)
*   **Interface:**
    *   `observe(world_state)`
    *   `decide_action(observation)`
    *   `internal_state`
*   **LLMAgent Implementation:**
    *   Uses `LLMClient`.
    *   Loads `Persona`.
    *   Receives world observation.
    *   Builds structured prompt.
    *   Requests an action.
    *   Parses & returns an `Action`.

### D. World Engine (world/)
*   **Responsibilities:**
    *   Hold authoritative world state.
    *   Validate actions.
    *   Apply changes deterministically.
    *   Update state every turn.
*   **Constraints:**
    *   Deterministic-only behavior in Phase 1. No randomness.
*   **Phase 1 Action Set:**
    *   `increase_resource`
    *   `decrease_resource`
    *   `support_agent`
    *   `oppose_agent`
    *   `pass`

### E. Simulation Controller (simulation/)
Handles the full simulation lifecycle:
1.  Load config + personas.
2.  Initialize world + agents.
3.  Loop through turns (Sequential):
    *   Broadcast world state.
    *   Collect actions sequentially.
    *   Validate & apply actions.
    *   Log narrative + debug info.
4.  Terminate on:
    *   `max_turns` reached.
    *   Optional terminal world condition.
    *   All agents choose "pass" for N consecutive turns.

### F. Configuration (config/)
YAML files defining:
*   Simulation settings (`max_turns`, `model_name`, `retries`).
*   Agent personas (`name`, `description`, `goals`, `biases`).
*   World initialization settings.

## 5. Data Flow
1.  **Initialization:** `SimulationController` loads configs. Instantiates `World` and `Agents`.
2.  **Turn Start:** `SimulationController` increments turn counter.
3.  **Observation:** Each agent receives a read-only snapshot of `WorldState`.
4.  **Reasoning:** Agent builds a structured prompt (Persona + Goals + World State + Allowed Actions + JSON Schema + Last 1-2 turns).
5.  **Decision:** Agent sends prompt to `LLMClient`.
6.  **Validation:** `LLMClient` retries up to 3 times on invalid JSON. Returns "pass" on failure.
7.  **Action:** Agent returns `Action` object.
8.  **World Update:** Controller checks validity: if not `world.is_valid_action(action)`: `action = Action(type="pass")`. World applies action deterministically.
9.  **Logging:** Changes logged to console (info) and file (debug).

## 6. Turn Loop Logic
```python
while turn < max_turns:
    for agent in agents:
        observation = world.get_view(agent)
        action = agent.decide(observation)
        
        if not world.is_valid_action(action):
            action = Action(type="pass")
            
        success, message = world.apply_action(agent, action)
        logger.log_turn(turn, agent, action, success, message)
```

## 7. LLM Interaction Approach
*   **Output Format:** Strict, JSON-only output schema.
    ```json
    {
      "action": "increase_resource",
      "target": "world",
      "reason": "short explanation here"
    }
    ```
*   **Prompt Template:**
    *   Persona description
    *   Goals
    *   World state
    *   Allowed actions
    *   Required JSON schema
    *   Last 1–2 turns max (strict limit for Phase 1)
*   **Model:** `llama3.1:8b`.

## 8. Memory Strategy (Phase 1)
*   **Short-term:** Include only the previous 1–2 turns in the prompt.
*   **Long-term:** None for Phase 1.

## 9. Logging Plan
*   **Console:** Info-level narrative.
*   **File:** Debug-level structured logs (LLM prompts + raw outputs).
*   **Format:** Easily machine-parsable (optional JSON logging for analytics later).

## 10. Testing Outline
*   **Unit Tests:** Action validation, world updates, config loading, persona parsing.
*   **Integration Tests:** Run a short (3 turn) simulation with a real LLM to verify end-to-end flow.

## 11. Roadmap
*   **Phase 1:** Minimal deterministic multi-agent simulation (MVP).
*   **Phase 2:** Deeper memory, richer world, structured JSON reasoning, trust maps.
*   **Phase 3:** Inter-agent communication (messaging), alliances, betrayals.
*   **Phase 4:** Swarm variants, Monte Carlo simulation, scenario planning.

## 12. Extensibility Strategy
*   Use ABCs/Protocols for all interfaces.
*   No cross-module dependencies.
*   Pydantic for all structured data.
*   Config-driven personas and world configs.
*   Dependency injection for `LLMClient` and `World`.
*   Directory structure scalable for future agents/worlds.

## 13. Dependencies
All installed via Poetry.
*   `httpx`: Async HTTP client.
*   `loguru`: Structured logging.
*   `pydantic`: Data validation and settings.
*   `pyyaml`: Configuration.
*   `pytest`: Testing.
