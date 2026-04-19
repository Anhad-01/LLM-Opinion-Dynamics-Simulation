# LLM Opinion Dynamics Simulation

This project is a sociological simulation designed to observe "Opinion Dynamics" and "Emergence" in artificial intelligence systems. It spins up a variable number of distinct AI agents (powered by Google's Gemini 2.5 Flash model), assigns them unique personas, and forces them to debate a single, controversial topic over multiple rounds. 

By utilizing a dedicated **AI Judge**, the system continually evaluates and scores the sentiment of each agent's argument, plotting exactly how their viewpoints drift and adapt over time. The platform features a modular architecture allowing you to experiment with standard global townhalls, centralized interventions (Moderation/Extremism), and restricted network topologies (Ideological Filter Bubbles).

## Key Features
- **Multi-Agent Simulation:** Dynamically generates complex personas (e.g., pragmatic economists, climate strikers, industrial lobbyists) with hidden internal baseline biases.
- **Smart API Rotation:** Intelligently load-balances inference requests across up to 10 GEMINI API keys (specifically respecting the strict free-tier rate limits of 15 Requests Per Minute via programmatic spacing).
- **Automated AI Judge:** Passes every debate statement to an objective AI evaluator enforcing a strict Pydantic JSON schema to quantify qualitative text on a 1-to-10 stance scale.
- **Modular Advanced Scenarios:** Dynamically swap between a Standard Global Townhall, a "Controller Agent Intervention" (forces a Moderator or Extremist into the swarm), or "Restricted Network Topologies" (Ring networks and isolated Filter Bubbles).
- **Streamlit Dashboard:** A reactive UI containing a live debate transcript matrix and Plotly-powered interactive line graphs.
- **Isolated Run Logs:** Automatically archives the full simulation logs and Pandas dataframe results into totally isolated, timestamped directories (e.g., `runs/run_2026.../`).
- **Anvil Integration Ready:** Includes a `anvil_frontend.py` snippet containing programmatic Python UI logic for deploying the simulation to the Anvil web platform. 

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
This project requires Google Gemini API access. Create a `.env` file in the root directory and securely paste your API keys. You can provide up to 10 keys:
```env
# single key fallback
GEMINI_API_KEY="your_api_key_here"

# OR load-balanced multi-key configuration
GEMINI_API_KEY_1="your_first_key"
GEMINI_API_KEY_2="your_second_key"
GEMINI_API_KEY_3="your_third_key"
```

---

## How to Run

### Streamlit Dashboard (Recommended)
To launch the primary interactive dashboard on your local machine, use:
```bash
streamlit run app.py
```
This will open the dashboard in your browser (typically `http://localhost:8501`). From there, use the sidebar to configure the number of agents, the number of rounds, and the debate topic.

### Reviewing Output Logs
Once a simulation finishes, open the `runs/` directory. Each run generates its own unique timestamped folder containing:
- `simulation.log`: The raw transcript of exactly who said what and what the judge evaluated.
- `results.csv`: A flattened, exportable dataset of that run's Opinion Matrix.
