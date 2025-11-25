# CouncilForge

A local multi-agent council simulation powered by a single local LLM model (llama3.1:8b via Ollama).

## Setup

1.  Install [Ollama](https://ollama.com/) and pull the model:
    ```bash
    ollama pull llama3.1:8b
    ```
2.  Install dependencies:
    ```bash
    poetry install
    ```
3.  Run the simulation:
    ```bash
    poetry run python main.py
    ```
