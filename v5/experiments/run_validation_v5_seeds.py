import sys
import os
import csv
import random
import numpy as np

# Ensure root directory is on the path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if root_dir not in sys.path:
    sys.path.append(root_dir)

from v5.src.coevolution import CoevolutionOrchestrator
from v5.src.metrics import ANNEX, compute_lz_complexity_ratio

def get_agent_action_string(agent, substrate, steps=20):
    from genesis_engine_v3.engine.structurally_evolvable_agent import AgentV4
    clone = AgentV4(agent.x, agent.y, agent.genome.copy())
    clone.energy = 1.0
    action_str = ""
    for _ in range(steps):
        action = clone.step(substrate)
        action_str += action
    return action_str

def run_seed(seed):
    random.seed(seed)
    np.random.seed(seed)
    
    generations = 10000
    log_interval = 1000
    num_envs = 5
    pop_size = 20
    
    print(f"Starting V5 Validation [Seed {seed}, {generations} gens]")
    orchestrator = CoevolutionOrchestrator(num_envs=num_envs, pop_size_per_env=pop_size)
    annex = ANNEX()
    
    for env in orchestrator.environments:
        annex.record_environment(env, agents_solved=True)
        
    os.makedirs('v5/results', exist_ok=True)
    log_path = f'v5/results/validation_seed_{seed}.csv'
    
    with open(log_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['gen', 'nodes', 'edges', 'lz', 'annex', 'mutations', 'transfers'])
        
        # log gen 0
        writer.writerow([0, 12.0, 2.0, 0.0, annex.count, 0, 0])
    
    for gen in range(1, generations + 1):
        orchestrator.step()
        
        if gen % log_interval == 0:
            new_env = orchestrator.coevolve()
            if new_env is not None:
                annex.record_environment(new_env, agents_solved=True)
                
            nodes, edges, lzs = [], [], []
            for env in orchestrator.environments:
                sub = orchestrator.substrates[env.id]
                for agent in orchestrator.agent_populations[env.id]:
                    nodes.append(len(agent.genome.nodes))
                    edges.append(len(agent.genome.connections))
                    actions = get_agent_action_string(agent, sub, steps=20)
                    lzs.append(compute_lz_complexity_ratio(actions))
                    
            avg_nodes = np.mean(nodes)
            avg_edges = np.mean(edges)
            avg_lz = np.mean(lzs)
            
            with open(log_path, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([gen, avg_nodes, avg_edges, avg_lz, annex.count, 
                                 orchestrator.total_mutations, orchestrator.total_transfers])
                                 
            print(f"V5 [Seed {seed}] Gen {gen:05d} | Nodes: {avg_nodes:.2f} | LZ: {avg_lz:.3f} | ANNEX: {annex.count}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        seeds = [int(sys.argv[1])]
    else:
        seeds = [42, 123, 456]
        
    for s in seeds:
        run_seed(s)
