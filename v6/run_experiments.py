import os
import sys
import csv
import argparse
import numpy as np

# Ensure root directory is on the path so we can import from genesis_engine_v3 and v5
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if root_dir not in sys.path:
    sys.path.append(root_dir)

from v6.config import EXPERIMENTS
from v6.engine import V6Orchestrator

def run_experiment(exp_name, config, seed, generations=10000, log_interval=1000, out_dir='v6/results'):
    print(f"Starting {exp_name} (Seed {seed})")
    print(f"Config: {config.get_description()}")
    
    np.random.seed(seed)
    import random
    random.seed(seed)
    
    os.makedirs(out_dir, exist_ok=True)
    log_file = os.path.join(out_dir, f'{exp_name}_seed{seed}.csv')
    
    orchestrator = V6Orchestrator(config=config, num_envs=5, pop_size_per_env=100)
    
    with open(log_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Generation', 'AvgNodes', 'AvgEdges', 'BehavioralDiversity', 'AvgEnergy', 'PopulationSize', 'AvgSecretion'])
        
    for gen in range(1, generations + 1):
        orchestrator.step()
        
        # We need to collect stats BEFORE clearing action history
        if gen % log_interval == 0 or gen == 1:
            all_agents = []
            secretions = []
            for env in orchestrator.environments:
                all_agents.extend(orchestrator.agent_populations[env.id])
                sub = orchestrator.substrates[env.id]
                secretions.append(np.mean(sub.S))
                
            nodes, edges, energies = [], [], []
            behaviors = set()
            
            for agent in all_agents:
                nodes.append(len(agent.genome.nodes))
                edges.append(len(agent.genome.connections))
                energies.append(agent.energy)
                behaviors.add(agent.action_history)
                
            avg_nodes = np.mean(nodes) if nodes else 0
            avg_edges = np.mean(edges) if edges else 0
            avg_energy = np.mean(energies) if energies else 0
            behavior_diversity = len(behaviors)
            pop_size = len(all_agents)
            avg_secretion = np.mean(secretions)
            
            print(f"Gen {gen:05d} | Pop: {pop_size} | Energy: {avg_energy:.3f} | Nodes: {avg_nodes:.1f} | Behaviors: {behavior_diversity} | Secretion: {avg_secretion:.4f}")
            
            with open(log_file, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([gen, avg_nodes, avg_edges, behavior_diversity, avg_energy, pop_size, avg_secretion])
                
        # Clear action history for the next generation
        for pop in orchestrator.agent_populations.values():
            for agent in pop:
                agent.action_history = ""
                
        # Coevolve handling (Goal switching)
        if gen % 500 == 0:
            orchestrator.coevolve()
            
    print(f"Finished {exp_name} (Seed {seed})")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--exp', type=str, default='all', help='Experiment name or "all"')
    parser.add_argument('--verify', action='store_true', help='Run 500 gen verification of Exp0 vs V5')
    args = parser.parse_args()
    
    if args.verify:
        print("Running verification: Exp0 Control vs V5 Baseline (500 generations)")
        run_experiment("Exp0_Control_Verify", EXPERIMENTS["Exp0_Control"], seed=42, generations=500, log_interval=100)
        sys.exit(0)
        
    seeds = [42, 123, 456]
    generations = 10000
    
    if args.exp == 'all':
        exps_to_run = EXPERIMENTS.keys()
    else:
        exps_to_run = [args.exp] if args.exp in EXPERIMENTS else []
        
    for exp_name in exps_to_run:
        for seed in seeds:
            run_experiment(exp_name, EXPERIMENTS[exp_name], seed, generations)
