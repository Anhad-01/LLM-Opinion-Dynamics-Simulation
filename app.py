import os
import asyncio
import random
import pandas as pd
import streamlit as st
import plotly.express as px
import logging
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

logging.basicConfig(
    filename='simulation_run.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

st.set_page_config(page_title="Opinion Dynamics Sim", layout="wide")

st.sidebar.title("Opinion Dynamics")
st.sidebar.markdown("Sociological simulation observing emergent agreement/disagreement using Gemini.")

NUM_AGENTS = st.sidebar.slider("Number of Agents", min_value=2, max_value=20, value=3)
NUM_ROUNDS = st.sidebar.slider("Number of Rounds", min_value=1, max_value=10, value=3)
TOPIC = st.sidebar.text_area("Debate Topic", value="Should a global, mandatory carbon tax be implemented?")

start_btn = st.sidebar.button("Start Simulation", type="primary")

API_KEYS = []
for i in range(1, 11):
    key = os.environ.get(f"GEMINI_API_KEY_{i}")
    if key:
        API_KEYS.append(key)

if not API_KEYS and os.environ.get("GEMINI_API_KEY"):
    API_KEYS.append(os.environ.get("GEMINI_API_KEY"))

request_counter = 0

def get_current_client():
    if not API_KEYS:
        return None
    key_index = (request_counter // 3) % len(API_KEYS)
    return genai.Client(api_key=API_KEYS[key_index])

BASE_PERSONAS = [
    "A pragmatic economist who prioritizes market stability and gradual changes",
    "A passionate environmental scientist who believes drastic action is needed immediately",
    "A conservative politician concerned about the economic impact on the working class and businesses",
    "A progressive activist focused on environmental justice and systemic change",
    "An indifferent citizen who doesn't follow politics but cares about daily living costs",
    "An industrial lobbyist who protects the interests of large manufacturing corporations",
    "A tech entrepreneur looking for technological rather than policy-driven solutions",
    "A local farmer who worries about the direct cost of fuel and supplies",
    "A youth climate striker who feels their future is being stolen",
    "A renewable energy investor hoping to capitalize on green policies",
    "A pessimistic philosopher who thinks humanity is doomed regardless of policy",
    "An international diplomat concerned about fairness between developed and developing nations"
]

def generate_personas(num_agents: int) -> list[dict]:
    personas = []
    if num_agents > len(BASE_PERSONAS):
        selected = random.choices(BASE_PERSONAS, k=num_agents)
    else:
        selected = random.sample(BASE_PERSONAS, k=num_agents)
        
    for i, archetype in enumerate(selected):
        stance_score = random.randint(1, 10)
        personas.append({
            "agent_id": f"Agent_{i+1}",
            "system_prompt": f"You are {archetype}. Consistently represent these views in debates. Keep your responses conversational and concise.",
            "initial_stance_score": stance_score
        })
    return personas

class JudgeEvaluation(BaseModel):
    sentiment_score: int = Field(description="Score from 1-10 evaluating the agent's stance (1=Strongly Against the topic, 10=Strongly For).")
    statement_summary: str = Field(description="A concise 1-sentence summary of the agent's core argument.")

async def judge_statement(round_num: int, agent_id: str, persona_name: str, statement: str) -> dict:
    global request_counter
    client = get_current_client()
    if not client:
        return {"Round": round_num, "Agent_ID": agent_id, "Persona": persona_name, "Stance_Score": 0, "Statement_Summary": "Error: API Keys missing"}
        
    system_instruction = "You are an objective AI judge evaluating debate statements. Return the data exactly as requested in the JSON schema."
    user_prompt = f"Topic: '{TOPIC}'\n\Evaluate the stance score and summarize this statement:\n{statement}"
    
    request_counter += 1
    try:
        response = await client.aio.models.generate_content(
            model="gemini-2.5-flash",
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.0,
                response_mime_type="application/json",
                response_schema=JudgeEvaluation,
            )
        )
        import json
        data = json.loads(response.text)
        return {
            "Round": round_num,
            "Agent_ID": agent_id,
            "Persona": persona_name,
            "Stance_Score": data.get("sentiment_score", 0),
            "Statement_Summary": data.get("statement_summary", "")
        }
    except Exception as e:
        return {"Round": round_num, "Agent_ID": agent_id, "Persona": persona_name, "Stance_Score": 0, "Statement_Summary": "Error parsing evaluation"}

async def agent_turn(persona: dict, context: str, is_first_round: bool) -> str:
    global request_counter
    if is_first_round:
        user_prompt = f"The topic is: '{TOPIC}'. Please state your initial opinion clearly. Write at least 2 full sentences, but strictly keep it under 60 words."
    else:
        user_prompt = f"Here is the debate history so far:\n{context}\n\nBased on this context, respond to others, argue your point, or adapt your views on the topic: '{TOPIC}'. Write at least 2 full sentences, but strictly keep it under 60 words."
        
    client = get_current_client()
    if not client:
        return "Error: Gemini API keys not found."
    
    request_counter += 1
    try:
        response = await client.aio.models.generate_content(
            model="gemini-2.5-flash",
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=persona["system_prompt"],
                temperature=0.7,
            )
        )
        return response.text
    except Exception as e:
        return f"API Error: {str(e)}"

async def run_simulation(ui_container):
    logging.info(f"--- STARTED NEW SIMULATION ---")
    logging.info(f"Agents: {NUM_AGENTS}, Rounds: {NUM_ROUNDS}, Topic: {TOPIC}")
    
    personas = generate_personas(NUM_AGENTS)
    debate_history = ""
    evaluation_results = []
    
    for round_num in range(1, NUM_ROUNDS + 1):
        logging.info(f"Beginning Round {round_num}")
        with ui_container.status(f"Round {round_num} in progress...", expanded=True) as status:
            is_first = (round_num == 1)
            round_context = f"\n--- Round {round_num} ---\n"
            
            for p in personas:
                agent_id = p["agent_id"]
                status.write(f"Awaiting response from {agent_id}...")
                
                response = await agent_turn(p, debate_history, is_first)
                formatted_response = response.strip()
                logging.info(f"Agent {agent_id} responded: {formatted_response}")
                round_context += f"{agent_id} says: {formatted_response}\n\n"
                
                ui_container.markdown(f"**{agent_id}**: {formatted_response}")
                
                await asyncio.sleep(4.5)
                
                status.write(f"⚖️ Judging {agent_id}...")
                persona_name = p["system_prompt"].split(".")[0].replace("You are ", "")
                eval_data = await judge_statement(round_num, agent_id, persona_name, formatted_response)
                logging.info(f"Judge evaluated {agent_id}: Score {eval_data['Stance_Score']} - {eval_data['Statement_Summary']}")
                evaluation_results.append(eval_data)
                
                await asyncio.sleep(4.5)
                
            status.update(label=f"Round {round_num} Complete!", state="complete", expanded=False)
            debate_history += round_context
            
    df = pd.DataFrame(evaluation_results)
    
    df_output_path = "all_simulations_results.csv"
    if os.path.exists(df_output_path):
        df.to_csv(df_output_path, mode='a', header=False, index=False)
    else:
        df.to_csv(df_output_path, index=False)
    logging.info("Simulation completed and saved to all_simulations_results.csv")
    
    return df

st.title("Opinion Dynamics & Emergence Dashboard")
st.markdown("Watch AI agents develop, debate, and shift their stances over a controversial topic!")

if not API_KEYS:
    st.error("No GEMINI_API_KEYs found in environment. Please set them in your .env file.")
elif start_btn:
    st.subheader("Live Debate Feed")
    live_feed = st.container()
    
    df = asyncio.run(run_simulation(live_feed))
    
    st.divider()
    st.subheader("Simulation Results")
    
    if not df.empty:
        st.dataframe(df, use_container_width=True)
        
        fig = px.line(
            df, 
            x="Round", 
            y="Stance_Score", 
            color="Agent_ID", 
            hover_data=["Persona", "Statement_Summary"],
            markers=True,
            title="Opinion Drift Over Time (1=Strongly Against, 10=Strongly For)",
            range_y=[0, 11]
        )
        fig.update_xaxes(dtick=1)
        fig.update_layout(xaxis_title="Debate Round", yaxis_title="Stance Score")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No data was collected during the simulation.")
