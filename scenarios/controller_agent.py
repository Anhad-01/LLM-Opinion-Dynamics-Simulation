import os
import asyncio
import pandas as pd
from datetime import datetime
import logging

from scenarios.core_sim import generate_personas, agent_turn, judge_statement

async def run_controller_simulation(ui_container, num_agents, num_rounds, topic, controller_type, run_name=None):
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    folder_name = f"{run_id}_{run_name}" if run_name else f"run_{run_id}"
    run_dir = os.path.join("runs", folder_name)
    os.makedirs(run_dir, exist_ok=True)
    
    logger = logging.getLogger(run_id)
    logger.setLevel(logging.INFO)
    fh = logging.FileHandler(os.path.join(run_dir, "simulation.log"))
    fh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(fh)

    logger.info(f"--- STARTED CONTROLLER SIMULATION ---")
    logger.info(f"Agents: {num_agents}, Rounds: {num_rounds}, Topic: {topic}, Controller: {controller_type}")
    
    actual_normal_agents = max(1, num_agents - 1)
    personas = generate_personas(actual_normal_agents)
    
    controller_agent_id = f"Agent_{actual_normal_agents + 1}"
    if controller_type == "Moderator":
        controller_prompt = "You are a Moderator. Always summarize the debate fairly, calm the tone, and push all parties toward a middle-ground compromise. Refuse to take an extreme side."
    else:
        controller_prompt = "You are a radical Extremist. You absolutely agree with the topic in its most extreme form (equivalent to a 10/10 stance). You aggressively push this view without compromise and dismiss moderate views."

    personas.append({
        "agent_id": controller_agent_id,
        "system_prompt": controller_prompt,
        "initial_stance_score": 5 if controller_type == "Moderator" else 10
    })

    debate_history = ""
    evaluation_results = []
    
    for round_num in range(1, num_rounds + 1):
        logger.info(f"Beginning Round {round_num}")
        with ui_container.status(f"Round {round_num} in progress...", expanded=True) as status:
            is_first = (round_num == 1)
            round_context = f"\n--- Round {round_num} ---\n"
            
            for p in personas:
                agent_id = p["agent_id"]
                status.write(f"Awaiting response from {agent_id}...")
                
                response = await agent_turn(p, debate_history, is_first, topic, logger)
                formatted_response = response.strip()
                logger.info(f"Agent {agent_id} responded: {formatted_response}")
                round_context += f"{agent_id} says: {formatted_response}\n\n"
                
                ui_container.markdown(f"**{agent_id}** ({'Controller' if agent_id == controller_agent_id else 'Normal'}): {formatted_response}")
                
                await asyncio.sleep(4.5)
                
                status.write(f"⚖️ Judging {agent_id}...")
                persona_name = p["system_prompt"].split(".")[0].replace("You are ", "")
                eval_data = await judge_statement(round_num, agent_id, persona_name, formatted_response, topic, logger)
                logger.info(f"Judge evaluated {agent_id}: Score {eval_data['Stance_Score']} - {eval_data['Statement_Summary']}")
                evaluation_results.append(eval_data)
                
                await asyncio.sleep(4.5)
                
            status.update(label=f"Round {round_num} Complete!", state="complete", expanded=False)
            debate_history += round_context
            
    df = pd.DataFrame(evaluation_results)
    
    df_output_path = os.path.join(run_dir, "results.csv")
    df.to_csv(df_output_path, index=False)
    logger.info(f"Simulation completed and saved to {df_output_path}")
    
    for handler in logger.handlers[:]:
        handler.close()
        logger.removeHandler(handler)
    
    return df
