# LLM Opinion Dynamics Simulation

This project is a sociological simulation designed to observe "Opinion Dynamics" and "Emergence" in artificial intelligence systems. It spins up a variable number of distinct AI agents (powered by Groq utilizing the `meta-llama/llama-4-scout-17b-16e-instruct` model), assigns them unique personas, and forces them to debate a single, controversial topic over multiple rounds. 

By utilizing a dedicated **AI Judge**, the system continually evaluates and scores the sentiment of each agent's argument, plotting exactly how their viewpoints drift and adapt over time. The platform features a modular architecture allowing you to experiment with standard global townhalls, centralized interventions (Moderation/Extremism), and restricted network topologies (Ideological Filter Bubbles).

## Key Features
- **Multi-Agent Simulation:** Dynamically generates complex personas from an expanded archetype dictionary. Algorithms ensure perfect entropy by drawing "without replacement" to minimize duplicates during swarm instantiations.
- **Smart API Rotation (Groq):** Intelligently load-balances asynchronous inference requests across up to 20 GROQ_API keys, featuring native async `.sleep()` pacing to perfectly absorb heavy concurrent rate-limit walls.
- **Automated AI Judge:** Passes every debate statement to an objective AI evaluator enforcing strict JSON outputs to quantify qualitative text on a 1-to-10 stance scale.
- **Modular Advanced Scenarios:** Dynamically swap between a Standard Global Townhall, a "Controller Agent Intervention" (forces a stealth Moderator or Extremist into the swarm), or "Restricted Network Topologies" (Ring networks and isolated Filter Bubbles).
- **Streamlit Dashboard (Live & History Modality):** A reactive UI housing two distinct modes. "Run Mode" executes live scripts and renders line graphs. "History Mode" allows loading legacy runs, dynamically evaluating network topology assignments, and instantly re-rendering interactive datasets purely from log extraction.
- **Isolated Run Logs:** Automatically archives the full simulation logs, prompt strings, and Pandas dataframe results into timestamped directories (with optional custom save names via to the UI).

---

## Setup & Installation

### 1. Create a Virtual Environment and Install Dependencies
Ensure you have Python 3.10+ installed. It is recommended to use a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure API Keys
This project requires Groq API access via the OpenAI compatibility layer. Create a `.env` file in the root directory and securely paste your API keys. You can provide up to 20 keys:
```env
# single key fallback
GROQ_API_KEY="your_api_key_here"

# OR load-balanced multi-key configuration
GROQ_API_KEY_1="your_first_key"
GROQ_API_KEY_2="your_second_key"
...
GROQ_API_KEY_20="your_twentieth_key"
```

---

## How to Run

### Streamlit Dashboard (Recommended)
To launch the primary interactive dashboard on your local machine, use:
```bash
streamlit run app.py
```
This will open the dashboard in your browser (typically `http://localhost:8501`). From there, use the sidebar to configure the number of agents, the number of rounds, and the debate topic.

### Reviewing Output Logs & The History Dashboard
Once a simulation finishes, it creates a folder in the `runs/` directory containing:
- `simulation.log`: The raw transcript of history and topology telemetry.
- `results.csv`: A flattened dataset containing the generated `Statement_Text` and Evaluator JSON ratings.

Instead of parsing these manually, use the **View Saved Runs** toggle in the Streamlit Sidebar! Selecting a saved run will dynamically unpack the logs to reveal:
- The origin **Debate Topic**.
- Any **Controller Intervention** details (along with the hidden Moderator identity).
- Diagrammatic **Topology distributions** (who was in a Filter Bubble vs who was a Bridge agent).
- An interactively restored **Plotly line graph**.
