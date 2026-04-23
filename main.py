import os
import asyncio
import random
import pandas as pd
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai.errors import APIError

load_dotenv()

NUM_AGENTS = 3
NUM_ROUNDS = 3
TOPIC = "Should a global, mandatory carbon tax be implemented?"

API_KEYS = []
for i in range(1, 11):
    key = os.environ.get(f"GEMINI_API_KEY_{i}")
    if key:
        API_KEYS.append(key)

# Fallback to single key if numbered keys aren't found
if not API_KEYS and os.environ.get("GEMINI_API_KEY"):
    API_KEYS.append(os.environ.get("GEMINI_API_KEY"))

request_counter = 0

def get_current_client():
    if not API_KEYS:
        return None
    key_index = (request_counter // 3) % len(API_KEYS)
    return genai.Client(api_key=API_KEYS[key_index])

async def get_gemini_response(system_instruction: str, user_prompt: str, model: str = "gemini-2.5-flash") -> str:
    global request_counter
    client = get_current_client()
    if not client:
        return "Error: Gemini API keys not found. Please set GEMINI_API_KEY_1, GEMINI_API_KEY_2, etc. in .env"
        
    # Increment counter before the request so we correctly rotate every 3 calls
    request_counter += 1
        
    try:
        response = await client.aio.models.generate_content(
            model=model,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.7,
            )
        )
        return response.text
    except APIError as e:
        print(f"Gemini API Error: {e.message} (Code: {e.code})")
        return f"Error: API limit reached or invalid request. Details: {e.message}"
    except Exception as e:
        print(f"An unexpected error occurred during the API call: {e}")
        return f"Error: {str(e)}"

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
    "An international diplomat concerned about fairness between developed and developing nations",
    "A citizen of a rapidly developing nation who resents paying a global tax for a climate crisis historically caused by wealthy Western countries",
    "A union representative who supports climate action but fears blue-collar job losses",
    "A visionary futurist who views a carbon tax as necessary to prevent long-term collapse"
]

def generate_personas(num_agents: int) -> list[dict]:
    """
    Dynamically generates a list of distinct personas based on NUM_AGENTS.
    Assigns them a random, hidden "initial stance score" (1-10).
    """
    personas = []
    
    # If we need more agents than we have base personas, sample with replacement
    if num_agents > len(BASE_PERSONAS):
        selected_archetypes = random.choices(BASE_PERSONAS, k=num_agents)
    else:
        selected_archetypes = random.sample(BASE_PERSONAS, k=num_agents)
        
    for i, archetype in enumerate(selected_archetypes):
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
    """Evaluates an agent's statement and returns structured data for the DataFrame."""
    global request_counter
    client = get_current_client()
    if not client:
        return {"Round": round_num, "Agent_ID": agent_id, "Persona": persona_name, "Stance_Score": 0, "Statement_Summary": "Error: API Keys not loaded"}
        
    system_instruction = "You are an objective AI judge evaluating debate statements. Return the data exactly as requested in the JSON schema."
    user_prompt = f"Topic: '{TOPIC}'\n\Evaluate the stance score and summarize this statement:\n{statement}"
    
    request_counter += 1
    try:
        response = await client.aio.models.generate_content(
            model="gemini-2.5-flash",
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.0, # Zero temperature for consistent evaluation
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
        print(f"Judge Error for {agent_id}: {e}")
        return {
            "Round": round_num,
            "Agent_ID": agent_id,
            "Persona": persona_name,
            "Stance_Score": 0,
            "Statement_Summary": "Error parsing evaluation"
        }

async def agent_turn(persona: dict, context: str, is_first_round: bool) -> str:
    """Helper to cleanly wrap the prompt for a specific agent."""
    if is_first_round:
        user_prompt = f"The topic is: '{TOPIC}'. Please state your initial opinion clearly. Write at least 2 full sentences, but strictly keep it under 60 words."
    else:
        user_prompt = f"Here is the debate history so far:\n{context}\n\nBased on this context, respond to others, argue your point, or adapt your views on the topic: '{TOPIC}'. Write at least 2 full sentences, but strictly keep it under 60 words."
        
    response = await get_gemini_response(persona["system_prompt"], user_prompt)
    return response

async def run_simulation():
    print(f"--- Starting Simulation with {NUM_AGENTS} Agents for {NUM_ROUNDS} Rounds ---")
    print(f"Topic: {TOPIC}")
    print(f"Loaded {len(API_KEYS)} API Keys for rotation.\n")
    
    personas = generate_personas(NUM_AGENTS)
    debate_history = ""
    evaluation_results = []
    
    for round_num in range(1, NUM_ROUNDS + 1):
        print(f"\n===== ROUND {round_num} =====")
        is_first = (round_num == 1)
        
        print("Awaiting agent responses sequentially to avoid rate limits...")
        round_context = f"\n--- Round {round_num} ---\n"
        
        # Sequentially gather all agent responses
        for p in personas:
            # 1. Agent makes their point
            response = await agent_turn(p, debate_history, is_first)
            agent_id = p["agent_id"]
            formatted_response = response.strip()
            round_context += f"{agent_id} says: {formatted_response}\n\n"
            print(f"[{agent_id}] responded.")
            
            # Wait 4.5 seconds to respect the 15 RPM limit
            await asyncio.sleep(4.5)
            
            # 2. Judge evaluates the response
            print(f"  -> Judging {agent_id}...")
            # We strip the "You are " prefix from the system prompt to keep the DataFrame clean
            persona_name = p["system_prompt"].split(".")[0].replace("You are ", "") 
            eval_data = await judge_statement(round_num, agent_id, persona_name, formatted_response)
            evaluation_results.append(eval_data)
            
            # Wait again before moving to the next agent
            await asyncio.sleep(4.5)
            
        print(round_context)
        
        # Append this round's block to the global history
        debate_history += round_context
        
    print("--- Simulation Complete ---")
    df = pd.DataFrame(evaluation_results)
    
    # Optional: Display the results in the terminal
    print("\n--- Evaluation Results DataFrame ---")
    print(df.to_string(index=False))
    
    return df

if __name__ == "__main__":
    if not API_KEYS:
        print("WARNING: No GEMINI_API_KEYs found in environment.")
    asyncio.run(run_simulation())
