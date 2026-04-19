import os
import asyncio
import pandas as pd
from datetime import datetime
import logging

from scenarios.core_sim import generate_personas, agent_turn, judge_statement

def get_allowed_neighbors(target_index, topology_type, total_agents):
    if topology_type == "Ring":
        # Each agent hears only adjacent indices
        return [(target_index - 1) % total_agents, (target_index + 1) % total_agents]
    else: 
        # Filter Bubble
        bridge_index = 0
        if target_index == bridge_index:
            return list(range(total_agents))
        mid = total_agents // 2
        if target_index <= mid: # Group A
            return list(range(1, mid + 1))
        else: # Group B
            return list(range(mid + 1, total_agents))

async def run_topology_simulation(ui_container, num_agents, num_rounds, topic, topology_type):
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = os.path.join("runs", f"run_{run_id}")
    os.makedirs(run_dir, exist_ok=True)
    
    logger = logging.getLogger(run_id)
    logger.setLevel(logging.INFO)
    fh = logging.FileHandler(os.path.join(run_dir, "simulation.log"))
    fh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(fh)

    logger.info(f"--- STARTED TOPOLOGY SIMULATION ---")
    logger.info(f"Agents: {num_agents}, Rounds: {num_rounds}, Topic: {topic}, Topology: {topology_type}")
    
    personas = generate_personas(num_agents)
    
    if topology_type == "Filter Bubble":
        personas[0]["system_prompt"] += " You are the Bridge Agent. You have the unique ability to hear views from both isolated ideological groups."

    history_events = []
    evaluation_results = []
    
    for round_num in range(1, num_rounds + 1):
        logger.info(f"Beginning Round {round_num}")
        with ui_container.status(f"Round {round_num} in progress...", expanded=True) as status:
            is_first = (round_num == 1)
            
            for i, p in enumerate(personas):
                agent_id = p["agent_id"]
                
                context = ""
                if not is_first:
                    allowed = get_allowed_neighbors(i, topology_type, num_agents)
                    allowed_ids = [personas[idx]["agent_id"] for idx in allowed]
                    
                    for r in range(1, round_num):
                        context += f"\n--- Round {r} ---\n"
                        for ev in history_events:
                            if ev["round"] == r and ev["agent_id"] in allowed_ids:
                                context += f"{ev['agent_id']} says: {ev['text']}\n\n"

                status.write(f"Awaiting response from {agent_id}...")
                
                response = await agent_turn(p, context, is_first, topic, logger)
                formatted_response = response.strip()
                logger.info(f"Agent {agent_id} responded: {formatted_response}")
                
                history_events.append({
                    "round": round_num,
                    "agent_id": agent_id,
                    "text": formatted_response
                })
                
                group_label = ""
                if topology_type == "Filter Bubble":
                    if i == 0:
                        group_label = " (Bridge)"
                    elif i <= num_agents // 2:
                        group_label = " (Group A)"
                    else:
                        group_label = " (Group B)"

                ui_container.markdown(f"**{agent_id}**{group_label}: {formatted_response}")
                
                await asyncio.sleep(4.5)
                
                status.write(f"⚖️ Judging {agent_id}...")
                persona_name = p["system_prompt"].split(".")[0].replace("You are ", "")
                eval_data = await judge_statement(round_num, agent_id, persona_name, formatted_response, topic, logger)
                logger.info(f"Judge evaluated {agent_id}: Score {eval_data['Stance_Score']} - {eval_data['Statement_Summary']}")
                evaluation_results.append(eval_data)
                
                await asyncio.sleep(4.5)
                
            status.update(label=f"Round {round_num} Complete!", state="complete", expanded=False)
            
    df = pd.DataFrame(evaluation_results)
    
    df_output_path = os.path.join(run_dir, "results.csv")
    df.to_csv(df_output_path, index=False)
    logger.info(f"Simulation completed and saved to {df_output_path}")
    
    for handler in logger.handlers[:]:
        handler.close()
        logger.removeHandler(handler)
    
    return df
