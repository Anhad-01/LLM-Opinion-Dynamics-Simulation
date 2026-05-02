# LLM Opinion Dynamics Simulation

This project is a sociological simulation for observing **opinion dynamics**, **polarization**, and **emergent group behavior** in artificial intelligence systems. It spins up a configurable set of LLM agents, assigns each agent a distinct persona, and has them debate a controversial topic across multiple rounds.

A dedicated **AI Judge** evaluates every statement on a 1-to-10 stance scale, making qualitative debate behavior measurable. The project can then compare how opinions drift under standard discussion, controller-agent interventions, and restricted communication topologies such as rings and filter bubbles.

## Key Features

- **Multi-Agent Simulation:** Generates diverse personas and runs structured, multi-round debates between LLM agents.
- **Smart API Rotation (Groq):** Supports one Groq key or load-balanced rotation across up to 20 `GROQ_API_KEY_*` values for heavier concurrent runs.
- **Automated AI Judge:** Converts each natural-language debate statement into strict JSON ratings, including a numeric `Stance_Score`.
- **Modular Advanced Scenarios:** Swap between a standard global townhall, moderator/extremist controller agents, ring topology, and filter-bubble topology.
- **Streamlit Dashboard:** Run live simulations, inspect saved runs, restore plots, and review topology/controller metadata from archived outputs.
- **Mathematical Post-Run Analysis:** Recent analysis artifacts calculate round-level averages, variance, and standard deviation to quantify consensus, drift, volatility, and polarization.
- **Isolated Run Logs:** Archives simulation logs, prompt strings, and dataframe results into timestamped folders under `runs/`.

---

## Setup & Installation

### 1. Create a Virtual Environment and Install Dependencies

Ensure you have Python 3.10+ installed. It is recommended to use a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

On Windows PowerShell, activation is typically:

```powershell
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Configure API Keys

This project requires Groq API access via the OpenAI compatibility layer. Create a `.env` file in the root directory and add your API key or keys:

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

To launch the primary interactive dashboard:

```bash
streamlit run app.py
```

This opens the dashboard in your browser, typically at `http://localhost:8501`. Use the sidebar to configure the debate topic, number of agents, number of rounds, and scenario type.

### Reviewing Saved Runs

When a simulation finishes, it creates a folder in `runs/` containing:

- `simulation.log`: Raw debate transcript, scenario metadata, and topology telemetry.
- `results.csv`: Flattened statement-level data containing each agent response, persona, summary, and judge rating.

In the Streamlit UI, use **View Saved Runs** to load a previous run and restore its topic, controller details, topology distribution, and Plotly opinion-drift graph.

---

## Mathematical Analysis

The latest analysis work adds reproducible post-run metrics and visual artifacts for comparing scenario behavior. The source notebook is:

- `result_analysis.ipynb`

The notebook expects cleaned scenario CSVs in:

- `simulation_csvs/`

It exports per-scenario metric tables and plots into:

- `simulation_results/<scenario_name>/`

### Metrics Computed

For every debate round, the analysis groups all agents by `Round` and computes:

```text
System_Average = mean(Stance_Score)
System_Variance = variance(Stance_Score)
Standard_Deviation = sqrt(System_Variance)
```

These values provide a mathematical lens on the simulation:

- **System Average:** The overall center of opinion in a round. Movement over time indicates global opinion drift.
- **System Variance:** How widely agent opinions are spread. Higher variance means stronger disagreement.
- **Standard Deviation:** A more readable volatility/polarization score. Higher standard deviation means the system is more polarized.
- **Opinion Drift Plot:** Tracks each agent's stance score across rounds.
- **Volatility Plot:** Tracks standard deviation across rounds to show whether the system stabilizes or fragments.

### Scenario Artifacts

The repository currently includes generated analysis for five scenarios:

- `standard_townhall`
- `moderating_controller`
- `extremist_controller`
- `ring_topology`
- `filter_bubble_topology`

Each scenario folder contains:

- `<scenario>_statistics.csv`: Round-by-round `System_Average`, `System_Variance`, and `Standard_Deviation`.
- `<scenario>_drift.png`: Agent-level opinion drift over the debate.
- `<scenario>_volatility.png`: System-level volatility and polarization over the debate.

### Interpretation Summary

- **Standard Townhall:** A fully connected debate produces persistent gridlock. Extremes remain anchored, while moderate agents cluster near the middle without pulling the full system toward consensus.
- **Moderating Controller:** A moderator behaves like a damping signal. It reduces semantic instability for some agents and helps moderate personas converge around compromise language.
- **Extremist Controller:** A radical controller behaves like an amplifier. Instead of creating consensus, it provokes backlash and increases polarization.
- **Ring Topology:** Restricted neighbor-to-neighbor communication creates local clusters. Opinion movement is delayed because information cannot broadcast globally.
- **Filter Bubble Topology:** Isolated subgroups intensify echo-chamber behavior, while the bridge agent tends to settle into neutral synthesis because it receives conflicting signals from both sides.

A fuller written interpretation is available in `results_analysis.md`.

---

## Project Structure

```text
.
|-- app.py                         # Streamlit dashboard
|-- main.py                        # Simulation entry point / orchestration
|-- scenarios/                     # Scenario implementations
|-- runs/                          # Timestamped live simulation outputs
|-- simulation_csvs/               # Cleaned CSVs used for post-run analysis
|-- simulation_results/            # Generated statistics and plots
|-- result_analysis.ipynb          # Mathematical analysis notebook
|-- results_analysis.md            # Written interpretation of scenario outcomes
|-- requirements.txt
`-- README.md
```
