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

def get_bins(nodes, lz):
    # Binning logic for GAC (Nodes) and EPC (LZ)
    # Nodes: 0-1000 in bins of 50
    node_bin = min(int(nodes / 50), 19)
    # LZ: 0.0 - 1.0 in bins of 0.05
    lz_bin = min(int(lz / 0.05), 19)
    return (node_bin, lz_bin)

def run_mapelites_baseline(seed, generations=10000):
    random.seed(seed)
    np.random.seed(seed)
    
    log_interval = 1000
    pop_size = 20
    width = 50
    height = 50
    
    print(f"Starting MAP-Elites Baseline [Seed {seed}, {generations} gens]")
    
    f_map = np.full((height, width), 0.055, dtype=np.float32)
    k_map = np.full((height, width), 0.062, dtype=np.float32)
    u_map = np.full((height, width), 1.0, dtype=np.float32)
    v_map = np.full((height, width), 0.4, dtype=np.float32)
    
    substrate = V5Substrate(width, height, f_map, k_map, u_map, v_map)
    substrate.V = np.random.uniform(0.0, 0.5, (height, width)).astype(np.float32)
    substrate.U = np.random.uniform(0.5, 1.0, (height, width)).astype(np.float32)
    
    population = [AgentV4(random.randint(0, width-1), random.randint(0, height-1)) for _ in range(pop_size)]
    archive = {} # maps (node_bin, lz_bin) -> best_agent
    
    os.makedirs('results/baselines', exist_ok=True)
    log_path = f'results/baselines/mapelites_seed_{seed}.csv'
    
    with open(log_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['gen', 'nodes', 'edges', 'lz', 'archive_size'])
        writer.writerow([0, 12.0, 2.0, 0.0, 0])
        
    for gen in range(1, generations + 1):
        for _ in range(20):
            substrate.step()
            for agent in population:
                agent.step(substrate)
                agent.energy += substrate.V[int(agent.y) % substrate.height, int(agent.x) % substrate.width] * 0.5
                
        # Evaluate and insert into archive
        for agent in population:
            nodes = len(agent.genome.nodes)
            actions = get_agent_action_string(agent, substrate, steps=20)
            lz = compute_lz_complexity_ratio(actions)
            bin_idx = get_bins(nodes, lz)
            
            if bin_idx not in archive or agent.energy > archive[bin_idx].energy:
                archive[bin_idx] = agent
                
        # Generate new population from archive
        new_pop = []
        archive_agents = list(archive.values())
        
        while len(new_pop) < pop_size:
            parent = random.choice(archive_agents)
            child = parent.reproduce()
            child.energy = 1.0
            child.x = (parent.x + random.choice([-1, 0, 1])) % substrate.width
            child.y = (parent.y + random.choice([-1, 0, 1])) % substrate.height
            new_pop.append(child)
            
        population = new_pop
        
        if gen % log_interval == 0:
            nodes = [len(a.genome.nodes) for a in archive.values()]
            edges = [len(a.genome.connections) for a in archive.values()]
            
            avg_nodes = np.mean(nodes) if nodes else 0
            avg_edges = np.mean(edges) if edges else 0
            
            # Estimate average LZ of archive by reverse mapping bin or just calculating
            lzs = []
            for a in archive.values():
                act = get_agent_action_string(a, substrate, steps=20)
                lzs.append(compute_lz_complexity_ratio(act))
            avg_lz = np.mean(lzs) if lzs else 0
            
            with open(log_path, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([gen, avg_nodes, avg_edges, avg_lz, len(archive)])
                
            print(f"MAP-Elites [Seed {seed}] Gen {gen:05d} | Nodes: {avg_nodes:.2f} | LZ: {avg_lz:.3f} | Archive: {len(archive)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--seed', type=int, required=True)
    parser.add_argument('--generations', type=int, default=10000)
    args = parser.parse_args()
    run_mapelites_baseline(args.seed, args.generations)
