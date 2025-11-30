# Relationship Engine Analysis

**Status:** Active & Integrated (Bug Fixed)

## ❓ Do We Need It?
**Yes.** While a 120B LLM is smart, it has limitations that the Relationship Engine solves.

### 1. Long-Term Memory (The "Memento" Problem)
-   **LLM Context:** The LLM only sees the last few turns of history (to save tokens).
-   **Problem:** If Magnus betrayed Zara 20 turns ago, the LLM will forget it once that event scrolls out of the history window.
-   **Solution:** The Relationship Engine stores a persistent score (`Trust: -50`). Even if the *event* is forgotten, the *grudge* remains.

### 2. Consistency & Bias
-   **LLM Variability:** LLMs can be inconsistent. One turn they might be angry, the next turn they might forget why.
-   **Engine Bias:** By injecting `• Magnus: rival (-50)` into the prompt, we **force** the LLM to bias its reasoning against Magnus. It acts as a consistent "emotional state" anchor.

### 3. Game Mechanics (Future Proofing)
-   If we ever want to add hard rules (e.g., "Cannot form alliance if Trust < 0"), we need explicit numbers. The LLM's "feeling" cannot be used for code-based logic checks.

## 🛠️ The Fix
I discovered that while the engine was calculating scores, **they were not being shown to the LLM** due to a bug in `llm_agent.py`.
-   **Bug:** `relationships_section` was never populated.
-   **Fix:** Added logic to inject the scores into the prompt.

Now, when Zara sees `Magnus: rival (-15)`, she will treat him with suspicion *even if* he hasn't done anything bad in the last 2 turns.
