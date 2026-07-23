import sys
import os
import csv
import random
import numpy as np
import argparse

def lev_dist(s1, s2):
    # Ultra-fast Hamming-style distance for 20-char strings
    if len(s1) != len(s2):
        min_len = min(len(s1), len(s2))
        return abs(len(s1) - len(s2)) + sum(1 for a, b in zip(s1[:min_len], s2[:min_len]) if a != b)
    return sum(1 for a, b in zip(s1, s2) if a != b)


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

def calculate_novelty(behavior, archive, k=15):
    if not archive:
        return 0.0
    distances = [lev_dist(behavior, arch_b) for arch_b in archive]
    distances.sort()
    k_nearest = distances[:min(k, len(distances))]
    return sum(k_nearest) / len(k_nearest)

def run_novelty_baseline(seed, generations=10000):
    random.seed(seed)
    np.random.seed(seed)
    
    log_interval = 1000
    pop_size = 20
    width = 50
    height = 50
    
    print(f"Starting Novelty Baseline [Seed {seed}, {generations} gens]")
    
    f_map = np.full((height, width), 0.055, dtype=np.float32)
    k_map = np.full((height, width), 0.062, dtype=np.float32)
    u_map = np.full((height, width), 1.0, dtype=np.float32)
    v_map = np.full((height, width), 0.4, dtype=np.float32)
    
    substrate = V5Substrate(width, height, f_map, k_map, u_map, v_map)
    substrate.V = np.random.uniform(0.0, 0.5, (height, width)).astype(np.float32)
    substrate.U = np.random.uniform(0.5, 1.0, (height, width)).astype(np.float32)
    
    population = [AgentV4(random.randint(0, width-1), random.randint(0, height-1)) for _ in range(pop_size)]
    archive = []
    
    os.makedirs('results/baselines', exist_ok=True)
    log_path = f'results/baselines/novelty_seed_{seed}.csv'
    
    with open(log_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['gen', 'nodes', 'edges', 'lz'])
        writer.writerow([0, 12.0, 2.0, 0.0])
        
    for gen in range(1, generations + 1):
        behaviors = []
        for _ in range(20):
            substrate.step()
            for agent in population:
                agent.step(substrate)
                
        # Calculate behaviors for novelty
        for agent in population:
            agent.behavior = get_agent_action_string(agent, substrate, steps=20)
            agent.novelty = calculate_novelty(agent.behavior, archive)
            
        # Add to archive probabilistically
        for agent in population:
            if random.random() < 0.05:
                archive.append(agent.behavior)
                if len(archive) > 1000:
                    archive.pop(0)
                    
        # Selection based purely on NOVELTY
        population.sort(key=lambda a: a.novelty, reverse=True)
        survivors = population[:pop_size//2]
        
        for a in survivors:
            a.energy = 1.0
            a.x = (a.x + random.choice([-1, 0, 1])) % substrate.width
            a.y = (a.y + random.choice([-1, 0, 1])) % substrate.height
            
        new_pop = list(survivors)
        while len(new_pop) < pop_size:
            parent = random.choice(survivors)
            child = parent.reproduce()
            new_pop.append(child)
            
        population = new_pop
        
        if gen % log_interval == 0:
            nodes = [len(a.genome.nodes) for a in population]
            edges = [len(a.genome.connections) for a in population]
            lzs = []
            for a in population:
                if hasattr(a, 'behavior'):
                    lzs.append(compute_lz_complexity_ratio(a.behavior))
                else:
                    beh = get_agent_action_string(a, substrate, steps=20)
                    lzs.append(compute_lz_complexity_ratio(beh))
            
            avg_nodes = np.mean(nodes)
            avg_edges = np.mean(edges)
            avg_lz = np.mean(lzs)
            
            with open(log_path, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([gen, avg_nodes, avg_edges, avg_lz])
                
            print(f"Novelty [Seed {seed}] Gen {gen:05d} | Nodes: {avg_nodes:.2f} | LZ: {avg_lz:.3f} | Archive: {len(archive)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--seed', type=int, required=True)
    parser.add_argument('--generations', type=int, default=10000)
    args = parser.parse_args()
    run_novelty_baseline(args.seed, args.generations)
