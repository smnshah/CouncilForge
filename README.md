# CouncilForge 🏛️

**An Emergent AI Political Simulation**

CouncilForge is a multi-agent simulation where distinct AI personas compete, collaborate, and scheme to manage a city's resources. Powered by Large Language Models (LLMs), agents possess unique goals, voices, and dynamic relationships that evolve based on their interactions.

## 🌟 Key Features

### 🎭 Distinct Personas
The council is composed of three archetypal agents, each with a unique voice and agenda:
- **Magnus the Tycoon:** A populist business mogul focused on **Treasury** and **Infrastructure**. Speaks in hyperbole and nicknames.
- **Zara the Organizer:** A grassroots activist fighting for **Food** and **Morale**. Speaks with passion and collective language.
- **Victoria the Strategist:** An establishment politician prioritizing **Stability** and **Budget**. Speaks with formal, calculated polish.

### 🤝 Dynamic Social Engine
Relationships are not static. They evolve in real-time based on:
- **Actions:** Supporting or opposing an agent changes Trust and Resentment.
- **Tone Analysis:** The system analyzes the *emotional tone* of messages. Friendly messages build trust; hostile accusations fuel resentment.
- **Memory:** Agents remember past betrayals and alliances.

### 🧠 Dual-Mode Intelligence
- **Dev Mode:** Runs locally using **Ollama** (`llama3.1:8b`) for free, offline development.
- **Prod Mode:** Connects to **Groq API** (`openai/gpt-oss-120b`) for high-fidelity reasoning and strategic depth.

## 🛠️ Setup

### Prerequisites
- Python 3.10+
- [Poetry](https://python-poetry.org/) (Dependency Management)
- [Ollama](https://ollama.com/) (For local Dev mode)
- [Groq API Key](https://console.groq.com/) (For Prod mode)

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/yourusername/CouncilForge.git
    cd CouncilForge
    ```

2.  **Install dependencies:**
    ```bash
    poetry install
    ```

3.  **Set up Environment:**
    Create a `.env` file in the root directory:
    ```bash
    cp .env.example .env
    ```
    Add your Groq API key to `.env`:
    ```ini
    GROQ_API_KEY=your_api_key_here
    ```

4.  **Prepare Local Model (Dev Mode):**
    ```bash
    ollama pull llama3.1:8b
    ```

## 🚀 Usage

### Run the Simulation
```bash
poetry run python main.py
```

### Configuration
Edit `config/settings.yaml` to switch modes or adjust parameters:

```yaml
simulation:
  max_turns: 10
  mode: "prod"  # "dev" or "prod"
  
  prod_model: "openai/gpt-oss-120b"
  dev_model: "llama3.1:8b"
```

## 🧪 Testing
Run the full test suite to verify mechanics:
```bash
poetry run pytest
```

## 🏗️ Architecture
The simulation runs on a turn-based loop:
1.  **Observe:** Agents view the current world state (Resources, History).
2.  **Decide:** Agents use the LLM to reason and choose an action (Strategic, Economic, or Social).
3.  **Act:** The system applies the action and calculates costs/effects.
4.  **React:** Relationships update, and the world entropy decays resources.
