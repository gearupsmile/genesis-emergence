import sys
import os
import csv
import random
import numpy as np
import argparse

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if root_dir not in sys.path:
    sys.path.append(root_dir)

from genesis_engine_v3.engine.structurally_evolvable_agent import AgentV4
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

def run_random_baseline(seed, generations=10000):
    random.seed(seed)
    np.random.seed(seed)
    
    log_interval = 1000
    pop_size = 20
    width = 50
    height = 50
    
    print(f"Starting Random Baseline [Seed {seed}, {generations} gens]")
    
    # Static substrate
    f_map = np.full((height, width), 0.055, dtype=np.float32)
    k_map = np.full((height, width), 0.062, dtype=np.float32)
    u_map = np.full((height, width), 1.0, dtype=np.float32)
    v_map = np.full((height, width), 0.4, dtype=np.float32)
    
    substrate = V5Substrate(width, height, f_map, k_map, u_map, v_map)
    substrate.V = np.random.uniform(0.0, 0.5, (height, width)).astype(np.float32)
    substrate.U = np.random.uniform(0.5, 1.0, (height, width)).astype(np.float32)
    
    population = [AgentV4(random.randint(0, width-1), random.randint(0, height-1)) for _ in range(pop_size)]
    
    os.makedirs('results/baselines', exist_ok=True)
    log_path = f'results/baselines/random_seed_{seed}.csv'
    
    with open(log_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['gen', 'nodes', 'edges', 'lz'])
        writer.writerow([0, 12.0, 2.0, 0.0])
        
    for gen in range(1, generations + 1):
        for _ in range(20):
            substrate.step()
            for agent in population:
                agent.step(substrate)
                # Gain energy, but it's ignored in random selection
                agent.energy += substrate.V[int(agent.y) % substrate.height, int(agent.x) % substrate.width] * 0.5
                
        # Pure Random Selection (Neutral Drift)
        random.shuffle(population)
        survivors = population[:pop_size//2]
        
        for a in survivors:
            a.energy = 1.0 # Reset
            a.x = (a.x + random.choice([-1, 0, 1])) % substrate.width
            a.y = (a.y + random.choice([-1, 0, 1])) % substrate.height
            
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
                
            print(f"Random [Seed {seed}] Gen {gen:05d} | Nodes: {avg_nodes:.2f} | LZ: {avg_lz:.3f}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--seed', type=int, required=True)
    parser.add_argument('--generations', type=int, default=10000)
    args = parser.parse_args()
    run_random_baseline(args.seed, args.generations)
