import sys
import os
import csv
import random
import numpy as np

# Ensure root directory is on the path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if root_dir not in sys.path:
    sys.path.append(root_dir)

from genesis_engine_v3.engine.structurally_evolvable_agent import AgentV4
# Since V4 baseline doesn't use the CPPNEnvironment matrices, we can use V5Substrate 
# with static flat scalars mapped to the size, duplicating the classic Gray-Scott
from v5.src.cppn_environment import V5Substrate
from v5.src.metrics import compute_lz_complexity_ratio

def get_agent_action_string(agent, substrate, steps=20):
    clone = AgentV4(agent.x, agent.y, agent.genome.copy())
    clone.energy = 1.0
    action_str = ""
    for _ in range(steps):
        action = clone.step(substrate)
        action_str += action
    return action_str

def run_v4_baseline(seed):
    random.seed(seed)
    np.random.seed(seed)
    
    generations = 10000
    log_interval = 1000
    pop_size = 20
    width = 50
    height = 50
    
    print(f"Starting V4 Baseline [Seed {seed}, {generations} gens]")
    
    # Initialize static substrate (Classic Gray-Scott V4 without co-evolution)
    f_map = np.full((height, width), 0.055, dtype=np.float32)
    k_map = np.full((height, width), 0.062, dtype=np.float32)
    u_map = np.full((height, width), 1.0, dtype=np.float32)
    v_map = np.full((height, width), 0.4, dtype=np.float32)
    
    # Do exactly what V5 uses for fair testing except non-heterogeneous scalar map
    substrate = V5Substrate(width, height, f_map, k_map, u_map, v_map)
    # We ALSO must seed V randomly like we fixed for V5 so physics is identical minus co-evolution
    substrate.V = np.random.uniform(0.0, 0.5, (height, width)).astype(np.float32)
    substrate.U = np.random.uniform(0.5, 1.0, (height, width)).astype(np.float32)
    
    # Initialize pop
    population = [AgentV4(random.randint(0, width-1), random.randint(0, height-1)) for _ in range(pop_size)]
    
    os.makedirs('v4/results', exist_ok=True)
    os.makedirs('v4/experiments', exist_ok=True)
    log_path = f'v4/results/baseline_seed_{seed}.csv'
    
    with open(log_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['gen', 'nodes', 'edges', 'lz'])
        writer.writerow([0, 12.0, 2.0, 0.0])
        
    for gen in range(1, generations + 1):
        # Simulation step 20 times to match V5 exactly
        for _ in range(20):
            substrate.step()
            for agent in population:
                agent.step(substrate)
                # Gain energy from V just like V5 for an identical physics baseline
                agent.energy += substrate.V[int(agent.y) % substrate.height, int(agent.x) % substrate.width] * 0.5
                
        # Selection
        population.sort(key=lambda a: a.energy, reverse=True)
        survivors = population[:pop_size//2]
        
        for a in survivors:
            a.energy = min(1.0, max(0.0, a.energy + 0.2))
            a.x = (a.x + random.choice([-1, 0, 1])) % substrate.width
            a.y = (a.y + random.choice([-1, 0, 1])) % substrate.height
            
        # Reproduction
        new_pop = list(survivors)
        while len(new_pop) < pop_size:
            parent = random.choice(survivors)
            child = parent.reproduce()
            new_pop.append(child)
            
        population = new_pop
        
        if gen % log_interval == 0:
            nodes, edges, lzs = [], [], []
            for agent in population:
                nodes.append(len(agent.genome.nodes))
                edges.append(len(agent.genome.connections))
                actions = get_agent_action_string(agent, substrate, steps=20)
                lzs.append(compute_lz_complexity_ratio(actions))
                
            avg_nodes = np.mean(nodes)
            avg_edges = np.mean(edges)
            avg_lz = np.mean(lzs)
            
            with open(log_path, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([gen, avg_nodes, avg_edges, avg_lz])
                
            print(f"V4 [Seed {seed}] Gen {gen:05d} | Nodes: {avg_nodes:.2f} | LZ: {avg_lz:.3f}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        seeds = [int(sys.argv[1])]
    else:
        seeds = [42, 123, 456]
        
    for s in seeds:
        run_v4_baseline(s)
