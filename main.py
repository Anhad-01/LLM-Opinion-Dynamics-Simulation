import os
import asyncio
import random
from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai.errors import APIError

load_dotenv()

NUM_AGENTS = 10
NUM_ROUNDS = 5
TOPIC = "Should a global, mandatory carbon tax be implemented?"

try:
    client = genai.Client()
except Exception as e:
    print(f"Warning: Could not initialize global Gemini Client. {e}")
    client = None

async def get_gemini_response(system_instruction: str, user_prompt: str, model: str = "gemini-2.5-flash") -> str:
    if not client:
        return "Error: Gemini client is not initialized. Please set the GEMINI_API_KEY environment variable."
        
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
    "An international diplomat concerned about fairness between developed and developing nations"
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

async def test_personas():
    print("Testing Persona Generation...\n")
    personas = generate_personas(NUM_AGENTS)
    for p in personas:
        print(f"[{p['agent_id']}] Stance: {p['initial_stance_score']}/10")
        print(f"System Prompt: {p['system_prompt']}\n")
    print(f"Successfully generated {len(personas)} personas.")

if __name__ == "__main__":
    if not os.environ.get("GEMINI_API_KEY"):
        print("WARNING: GEMINI_API_KEY environment variable not found.")
    asyncio.run(test_personas())
