import os
import asyncio
import pandas as pd
import streamlit as st
import plotly.express as px

# Imports from modular scenario engine
from scenarios.standard_sim import run_standard_simulation
from scenarios.controller_agent import run_controller_simulation
from scenarios.network_topology import run_topology_simulation
from scenarios.core_sim import API_KEYS

st.set_page_config(page_title="Opinion Dynamics Sim", layout="wide")

st.sidebar.title("Opinion Dynamics")
st.sidebar.markdown("Sociological simulation observing emergent agreement/disagreement using Gemini.")

app_mode = st.sidebar.radio("App Mode", ["Run New Simulation", "View Saved Runs"])

st.sidebar.divider()

if app_mode == "Run New Simulation":
    NUM_AGENTS = st.sidebar.slider("Number of Agents", min_value=2, max_value=20, value=3)
    NUM_ROUNDS = st.sidebar.slider("Number of Rounds", min_value=1, max_value=10, value=3)
    TOPIC = st.sidebar.text_area("Debate Topic", value="Should a global, mandatory carbon tax be implemented?")

    st.sidebar.divider()
    st.sidebar.subheader("Simulation Configuration")

    scenario_choice = st.sidebar.selectbox("Simulation Scenario", [
        "Standard Global Townhall",
        "Controller Agent Intervention",
        "Restricted Network Topology"
    ])

    controller_type = None
    topology_type = None

    if scenario_choice == "Controller Agent Intervention":
        controller_type = st.sidebar.selectbox("Controller Type", ["Moderator", "Extremist"])
    elif scenario_choice == "Restricted Network Topology":
        topology_type = st.sidebar.selectbox("Topology Type", ["Ring", "Filter Bubble"])

    st.sidebar.divider()
    custom_run_name = st.sidebar.text_input("💾 Save Run As (Optional)", placeholder="e.g. 15_agents_ring")
    start_btn = st.sidebar.button("Start Simulation", type="primary")

    st.title("🗣️ Opinion Dynamics & Emergence Dashboard")
    st.markdown("Watch AI agents develop, debate, and shift their stances over a controversial topic!")

    if not API_KEYS:
        st.error("No GROQ_API_KEYs found in environment. Please set them in your .env file.")
    elif start_btn:
        st.subheader("Live Debate Feed")
        live_feed = st.container()
        
        # Route execution dynamically
        if scenario_choice == "Standard Global Townhall":
            df = asyncio.run(run_standard_simulation(live_feed, NUM_AGENTS, NUM_ROUNDS, TOPIC, custom_run_name))
        elif scenario_choice == "Controller Agent Intervention":
            df = asyncio.run(run_controller_simulation(live_feed, NUM_AGENTS, NUM_ROUNDS, TOPIC, controller_type, custom_run_name))
        elif scenario_choice == "Restricted Network Topology":
            df = asyncio.run(run_topology_simulation(live_feed, NUM_AGENTS, NUM_ROUNDS, TOPIC, topology_type, custom_run_name))
        
        st.divider()
        st.subheader("📊 Simulation Results")
        
        if not df.empty:
            st.dataframe(df, use_container_width=True)
            
            # Plotly chart
            fig = px.line(
                df, 
                x="Round", 
                y="Stance_Score", 
                color="Agent_ID", 
                hover_data=["Persona", "Statement_Summary", "Statement_Text"],
                markers=True,
                title="Opinion Drift Over Time (1=Strongly Against, 10=Strongly For)",
                range_y=[0, 11]
            )
            fig.update_xaxes(dtick=1)
            fig.update_layout(xaxis_title="Debate Round", yaxis_title="Stance Score")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No data was collected during the simulation.")

else:
    # View Saved Runs Mode
    st.title("📂 Saved Runs History")
    
    if not os.path.exists("runs"):
        st.info("No runs directory found. Please run a simulation first.")
    else:
        all_runs = []
        for run_dir in os.listdir("runs"):
            if os.path.isdir(os.path.join("runs", run_dir)):
                if "results.csv" in os.listdir(os.path.join("runs", run_dir)):
                    all_runs.append(run_dir)
        
        if not all_runs:
            st.info("No saved results found inside the runs directory.")
        else:
            all_runs.sort(reverse=True) # Sort descending to show newest first
            selected_run = st.selectbox("Select a Saved Simulation to View", all_runs)
            
            if selected_run:
                csv_path = os.path.join("runs", selected_run, "results.csv")
                df = pd.read_csv(csv_path)
                
                st.subheader(f"Results for: {selected_run}")
                st.dataframe(df, use_container_width=True)
                
                # Plotly chart
                fig = px.line(
                    df, 
                    x="Round", 
                    y="Stance_Score", 
                    color="Agent_ID", 
                    hover_data=["Persona", "Statement_Summary", "Statement_Text"] if "Statement_Text" in df.columns else ["Persona", "Statement_Summary"],
                    markers=True,
                    title="Opinion Drift Over Time (1=Strongly Against, 10=Strongly For)",
                    range_y=[0, 11]
                )
                fig.update_xaxes(dtick=1)
                fig.update_layout(xaxis_title="Debate Round", yaxis_title="Stance Score")
                st.plotly_chart(fig, use_container_width=True)
