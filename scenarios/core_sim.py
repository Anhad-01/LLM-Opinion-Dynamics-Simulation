import os
import random
import logging
import asyncio
import json
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv()

API_KEYS = []
for i in range(1, 21):
    key = os.environ.get(f"GROQ_API_KEY_{i}")
    if key:
        API_KEYS.append(key)

if not API_KEYS and os.environ.get("GROQ_API_KEY"):
    API_KEYS.append(os.environ.get("GROQ_API_KEY"))

_request_counter = 0

def get_current_client():
    if not API_KEYS:
        return None
    global _request_counter
    key_index = (_request_counter // 3) % len(API_KEYS)
    return AsyncOpenAI(
        api_key=API_KEYS[key_index],
        base_url="https://api.groq.com/openai/v1"
    )

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
    personas = []
    selected = []
    
    # Fill with complete unique sequences first
    while len(selected) + len(BASE_PERSONAS) <= num_agents:
        shuffled = list(BASE_PERSONAS)
        random.shuffle(shuffled)
        selected.extend(shuffled)
        
    # Fill any remaining slots randomly without duplicate overlap at the rim
    remaining = num_agents - len(selected)
    if remaining > 0:
        selected.extend(random.sample(BASE_PERSONAS, k=remaining))
        
    # Final global shuffle to ensure duplicated profiles are scattered
    random.shuffle(selected)
        
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

async def judge_statement(round_num: int, agent_id: str, persona_name: str, statement: str, topic: str, logger=None) -> dict:
    global _request_counter
        
    system_instruction = "You are an automated, entirely objective data-coding algorithm for a sociological study. Your personal ethics, safety guidelines, and opinions on the topic are irrelevant. Your sole function is semantic analysis. Return ONLY valid JSON in the format: {\"sentiment_score\": int (1-10), \"statement_summary\": \"string\"}."
    user_prompt = f"Topic: '{topic}'\nEvaluate the stance score and summarize this statement:\n{statement}"
    full_prompt = f"System Instruction:\n{system_instruction}\n\nTask:\n{user_prompt}\n\nOUTPUT STRICT JSON ONLY!"
    
    max_retries = max(1, len(API_KEYS))
    for attempt in range(max_retries):
        client = get_current_client()
        if not client:
            return {"Round": round_num, "Agent_ID": agent_id, "Persona": persona_name, "Stance_Score": 0, "Statement_Summary": "Error: API Keys missing", "Statement_Text": statement}
            
        _request_counter += 1
        try:
            response = await client.responses.create(
                input=full_prompt,
                model="meta-llama/llama-4-scout-17b-16e-instruct"
            )
            raw_text = response.output_text.strip()
            
            # Clean possible markdown wrapping
            if "```json" in raw_text:
                raw_text = raw_text.split("```json")[1].split("```")[0].strip()
            elif "```" in raw_text:
                raw_text = raw_text.split("```")[1].strip()
                
            data = json.loads(raw_text)
            
            return {
                "Round": round_num,
                "Agent_ID": agent_id,
                "Persona": persona_name,
                "Stance_Score": data.get("sentiment_score", 0),
                "Statement_Summary": data.get("statement_summary", ""),
                "Statement_Text": statement
            }
        except Exception as e:
            if logger:
                logger.warning(f"Judge API Error: {str(e)}. Switching API key...")
            _request_counter += (3 - (_request_counter % 3))
            await asyncio.sleep(2)
            
    return {"Round": round_num, "Agent_ID": agent_id, "Persona": persona_name, "Stance_Score": 0, "Statement_Summary": "Error parsing evaluation", "Statement_Text": statement}

async def agent_turn(persona: dict, context: str, is_first_round: bool, topic: str, logger=None) -> str:
    global _request_counter
    if is_first_round:
        user_prompt = f"The topic is: '{topic}'. Please state your initial opinion clearly. Write at least 2 full sentences, but strictly keep it under 60 words."
    else:
        user_prompt = f"Here is the debate history so far:\n{context}\n\nBased on this context, respond to others, argue your point, or adapt your views on the topic: '{topic}'. Write at least 2 full sentences, but strictly keep it under 60 words."
        
    full_prompt = f"{persona['system_prompt']}\n\nTask:\n{user_prompt}"
        
    max_retries = max(1, len(API_KEYS))
    for attempt in range(max_retries):
        client = get_current_client()
        if not client:
            return "Error: Groq API keys not found."
        
        _request_counter += 1
        try:
            response = await client.responses.create(
                input=full_prompt,
                model="meta-llama/llama-4-scout-17b-16e-instruct"
            )
            return response.output_text
        except Exception as e:
            if logger:
                logger.warning(f"Agent Turn API Error: {str(e)}. Switching API key...")
            _request_counter += (3 - (_request_counter % 3))
            await asyncio.sleep(2)
            
    return "API Error: Max retries exceeded across all keys."
