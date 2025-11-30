# Phase 6: High-Fidelity Simulation & Social Intelligence

**Objective:** Transition CouncilForge from a mechanical prototype to a high-fidelity social simulation with distinct agent personalities, emotional intelligence, and robust reasoning capabilities.

## 1. 🧠 LLM Provider Upgrade
To support complex strategic reasoning, we moved beyond the limitations of local 8B models.

-   **New Provider:** Groq API.
-   **Production Model:** `openai/gpt-oss-120b` (120B Parameters).
-   **Architecture:**
    -   Implemented `LLMClient` with dual-mode support (`dev` vs `prod`).
    -   **Dev Mode:** Uses local `ollama` (`llama3.1:8b`) for free, offline testing.
    -   **Prod Mode:** Uses `Groq` for high-performance production runs.
    -   **Robustness:** Added retry logic and increased `max_tokens` to 1500 to handle verbose reasoning.

## 2. 🎭 Persona Refinement
We replaced generic agents with distinct, real-world inspired archetypes to drive conflict and diverse strategies.

### The Council
| Agent | Archetype | Voice/Style | Goals |
| :--- | :--- | :--- | :--- |
| **Magnus** | The Tycoon (Trump-inspired) | Hyperbolic, nickname-heavy, transactional. | **Treasury > 50**, Infrastructure. |
| **Zara** | The Organizer (Mamdani-inspired) | Passionate, collective ("We"), academic. | **Food > 50**, Morale, Coalition building. |
| **Victoria** | The Strategist (Pelosi-inspired) | Formal, institutional, calculated. | **Stability**, Budget balance. |

**Implementation:**
-   Added `voice_instructions` field to `Persona` model.
-   Updated LLM prompt to strictly enforce these voices.

## 3. ❤️ Social & Emotional Intelligence
Agents now react not just to *actions* but to the *tone* of communication.

### Tone Analysis Engine
-   **Mechanism:** Integrated `parse_message_tone` into the relationship update loop.
-   **Logic:**
    -   **Friendly:** (+5 Trust, -2 Resentment). Triggered by support, alliance offers.
    -   **Hostile:** (-5 Trust, +5 Resentment). Triggered by insults, accusations ("hoard", "crush").
    -   **Neutral:** (+1 Trust). Routine communication.

### Relationship Engine Integration (Fixed)
-   **Bug Found:** Relationship scores were calculated but **not shown** to the LLM in the prompt.
-   **Fix:** Updated `llm_agent.py` to inject a `=== RELATIONSHIPS ===` section into the prompt.
-   **Refactor:** Removed redundant `get_relationship_score` function; agents now use `Relationship.score` property directly.
-   **Impact:** Agents are now aware of their allies and rivals, enabling long-term memory and consistent bias.

## 4. 🛡️ Robustness & Hallucination Fixes
Addressed issues where the LLM would invent invalid targets or malformed output.

-   **Target Sanitization:**
    -   Prompt updated to use generic `TARGET AGENT` placeholders.
    -   Controller sanitizes output to strip brackets (`[]`) and underscores (`_`) (e.g., `[Victoria]` -> `Victoria`).
-   **JSON Validation:**
    -   Strict `json_object` mode enforced.
    -   Prompt explicitly forbids markdown code blocks to prevent parsing errors.
    -   Increased `max_tokens` to 1500 to prevent truncation.

## 5. 📚 Documentation
-   **README.md:** Rewritten with comprehensive project summary, setup, and usage instructions.
-   **Analysis:** Added `docs/relationship_engine_analysis.md` explaining the necessity of the relationship engine.

## 6. ✅ Verification
-   **Test Suite:** Updated all unit and integration tests to reflect new models and mechanics.
-   **Status:** 45/45 Tests Passing.
