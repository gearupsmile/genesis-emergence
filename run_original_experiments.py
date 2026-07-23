import sys
import os
import random
import numpy as np
import pickle

# Ensure root directory is on path
root_dir = os.path.abspath(os.path.dirname(__file__))
if root_dir not in sys.path:
    sys.path.append(root_dir)

from genesis_engine_v3.engine.structurally_evolvable_agent import AgentV4
from v5.src.cppn_environment import V5Substrate

def run_v4_baseline_experiment(seed=42, target_nodes=52.0):
    random.seed(seed)
    np.random.seed(seed)
    
    pop_size = 20
    width = 50
    height = 50
    
    print(f"--- Running V4 Baseline [Seed {seed}, target nodes {target_nodes}] ---")
    
    f_map = np.full((height, width), 0.055, dtype=np.float32)
    k_map = np.full((height, width), 0.062, dtype=np.float32)
    u_map = np.full((height, width), 1.0, dtype=np.float32)
    v_map = np.full((height, width), 0.4, dtype=np.float32)
    
    substrate = V5Substrate(width, height, f_map, k_map, u_map, v_map)
    substrate.V = np.random.uniform(0.0, 0.5, (height, width)).astype(np.float32)
    substrate.U = np.random.uniform(0.5, 1.0, (height, width)).astype(np.float32)
    
    population = [AgentV4(random.randint(0, width-1), random.randint(0, height-1)) for _ in range(pop_size)]
    
    gen = 0
    while True:
        gen += 1
        for _ in range(20):
            substrate.step()
            for agent in population:
                agent.step(substrate)
                agent.energy += substrate.V[int(agent.y) % substrate.height, int(agent.x) % substrate.width] * 0.5
                
        population.sort(key=lambda a: a.energy, reverse=True)
        survivors = population[:pop_size//2]
        
        for a in survivors:
            a.energy = min(1.0, max(0.0, a.energy + 0.2))
            a.x = (a.x + random.choice([-1, 0, 1])) % substrate.width
            a.y = (a.y + random.choice([-1, 0, 1])) % substrate.height
            
        new_pop = list(survivors)
        while len(new_pop) < pop_size:
            parent = random.choice(survivors)
            child = parent.reproduce()
            new_pop.append(child)
            
        population = new_pop
        
        avg_nodes = np.mean([len(agent.genome.nodes) for agent in population])
        if gen % 100 == 0:
            print(f"V4 Gen {gen} | Avg Nodes: {avg_nodes:.2f}")
            
        if avg_nodes >= target_nodes or gen >= 5000:
            print(f"V4 Finished at Gen {gen} with Avg Nodes: {avg_nodes:.2f}")
            break
            
    os.makedirs("v5_validation/checkpoints", exist_ok=True)
    with open("v5_validation/checkpoints/fixed_agents.pkl", "wb") as f:
        pickle.dump(population, f)
    print("Saved V4 agents to v5_validation/checkpoints/fixed_agents.pkl")

if __name__ == "__main__":
    run_v4_baseline_experiment(seed=42)
    print("Experiments completed successfully!")
