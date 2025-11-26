# Phase 4 Specification — Social Priority System + Emotion Engine + Behavior Dynamics Overhaul

## 1. High-Level Goals

Phase 4 aims to transform agents from resource managers into socially-driven political actors. The central shift is that **social behavior must dominate decision-making**.

### Key Capabilities
1.  **Social Dominance**: Social actions become the default; resource actions are fallbacks.
2.  **Emotional States**: Agents track Anger, Trust, Fear, Admiration, Ambition, and Insecurity.
3.  **Interpersonal Goals**: Agents form explicit conditional goals (e.g., "Ally with X", "Undermine Y").
4.  **Strong Bias Weighting**: Decision making uses hard numeric multipliers, not just soft prompt hints.
5.  **Expanded Social Actions**: 8 new distinct social actions (e.g., `form_alliance`, `denounce_agent`).
6.  **Prompt Restructuring**: Social content moves to the top; world content is compressed and lowered.
7.  **Deterministic Reasoning**: Prompts include structured sections for emotion influence, bias weights, and penalties.

## 2. Module Breakdown

### 2.1 Emotion Engine (`src/social/emotion_engine.py`)

**Responsibilities:**
-   Store per-agent emotion state:
    ```python
    emotions = {
        "trust": float,      # [-50, 50]
        "resentment": float, # [-50, 50]
        "admiration": float, # [-50, 50]
        "fear": float,       # [-50, 50]
        "ambition": float,   # [-50, 50]
        "insecurity": float, # [-50, 50]
    }
    ```
-   **Update Rules**:
    -   `support` → +trust, -resentment
    -   `oppose` → +resentment, -trust
    -   `sabotage` → Large +resentment
    -   `negotiate` → +trust or +admiration
    -   `consume_resource` (selfish) → Increase others' resentment
-   **Normalization**: Ensure emotions stay within [-50, +50].

**API**:
-   `update_emotions(actor, target, action_type)`
-   `get_emotional_bias(emotions) -> Dict[str, float]` (Returns multipliers for actions)

### 2.2 Interpersonal Goals (`src/social/interpersonal_goals.py`)

**Responsibilities:**
-   Store explicit goals per agent:
    ```python
    goals = {
       "ally_with": Optional[str],
       "undermine": Optional[str],
       "gain_influence_over": Optional[str],
       "seek_approval_from": Optional[str]
    }
    ```
-   **Formation Rules**:
    -   **Ally**: When `trust > 15`.
    -   **Undermine**: When `resentment > 15`.
    -   **Seek Approval**: When `admiration > 10`.
    -   **Gain Influence**: When `ambition > 10` AND `world_stability < 50`.

**API**:
-   `update_goals(agent_state, emotions)`

### 2.3 Expanded Social Action Ontology (`src/core/models.py`)

**New Actions**:
1.  `form_alliance`
2.  `denounce_agent`
3.  `offer_concession`
4.  `demand_concession`
5.  `accuse_agent`
6.  `offer_protection`
7.  `spread_rumor`
8.  `propose_policy`

**Updates**:
-   Update `ActionType` enum.
-   Ensure schema supports these (standard `target`, `message`, `reason` fields).

### 2.4 Decision Bias Overhaul (`src/social/decision_engine.py`)

**Logic**:
Replace soft biases with numeric multipliers.
-   **Base Weights**:
    -   `social_action_base` = 1.0
    -   `world_action_base` = 0.25
-   **Bonuses**:
    -   `relation_bonus` = `(trust - resentment) / 50`
    -   `emotion_bias` = Derived from `emotion_engine`.
    -   `goal_bonus` = +0.5 if action aligns with current goal.
    -   `repetition_penalty` = -0.75 if repeating last action.

**Formula**:
`final_bias[action] = base_weight + relation_bonus + emotion_bias + goal_bonus + repetition_penalty`

**Output**:
-   Sorted list of actions by score to be presented in the prompt.

### 2.5 Prompt Template Overhaul (`src/agents/llm_agent.py`)

**New Section Order**:
1.  **Persona**
2.  **Emotional State** (New)
3.  **Relationship Summary**
4.  **Interpersonal Goals** (New)
5.  **Action Bias Weight Table** (Numeric, New)
6.  **Recent History Summary** (Shortened)
7.  **Allowed Social Actions**
8.  **Allowed Resource Actions**
9.  **Compressed World Summary** (Moved down)
10. **Output Schema + Rules**

**Formatting Requirements**:
-   **Bias Table**:
    ```text
    Action Bias Table:
    - support_agent: 1.35
    - oppose_agent: 0.85
    ...
    ```
-   **Repetition Penalty**:
    ```text
    Repetition Penalty Applied:
    Last Action: "strengthen_infrastructure"
    Penalty: -0.75
    ```
-   **Emotions**:
    ```text
    Your Emotional State:
    - Trust toward Lyra: 15
    ...
    ```
-   **Goals**:
    ```text
    Your Current Goals:
    - ally_with: "Lyra"
    ...
    ```

**Instructions**:
-   "You MUST choose an action with the highest final bias score unless you provide a compelling reason."
-   "Social actions are preferred over world actions unless crisis metrics demand otherwise."

### 2.6 World Table Compression (`src/agents/llm_agent.py`)

-   Reduce world state display to: `Food`, `Energy`, `Infrastructure`, `Stability`, `Crisis`.
-   Remove verbose descriptions if possible to save context and focus attention.

### 2.7 Controller & Engine Updates (`src/simulation/controller.py`)

-   **Loop Updates**:
    -   Call `update_emotions` after actions.
    -   Call `update_goals` after emotion updates.
    -   Ensure `repetition_tracking` is accurate.
    -   Log all social state changes for debugging.

## 3. Behavior Guarantees

Agents will:
-   Form alliances and denounce rivals.
-   Escalate conflicts and protect allies.
-   Drift apart emotionally.
-   Avoid repetitive actions.
-   **Choose social behavior 70%+ of the time.**

## 4. Test Requirements

-   **Emotion Engine**: Test updates, bias generation, normalization.
-   **Interpersonal Goals**: Test threshold triggering.
-   **Decision Bias**: Test numeric weighting, sorting, repetition penalty.
-   **Allowed Actions**: Test schema validation.
-   **Integration**: Verify full flow in `test_simulation_flow.py`.

## 5. Implementation Order

1.  **Emotion Engine** (`src/social/emotion_engine.py`)
2.  **Interpersonal Goals** (`src/social/interpersonal_goals.py`)
3.  **Expanded Actions** (`src/core/models.py`)
4.  **Decision Engine Overhaul** (`src/social/decision_engine.py`)
5.  **Prompt Restructuring** (`src/agents/llm_agent.py`)
6.  **Controller Integration** (`src/simulation/controller.py`)
7.  **Tests** (Unit & Integration)
8.  **Verification** (5-turn dry run)
