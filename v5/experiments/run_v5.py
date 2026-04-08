import sys
import os
import csv
import numpy as np

# Ensure root directory is on the path so we can import from genesis_engine_v3 and v5
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if root_dir not in sys.path:
    sys.path.append(root_dir)

from v5.src.coevolution import CoevolutionOrchestrator
from v5.src.metrics import compute_pata_ec, ANNEX

def main(generations=10000, log_interval=500, num_envs=5, pop_size=100):
    print(f"Starting V5 Coevolution: {num_envs} environments, {pop_size} agents per env.")
    orchestrator = CoevolutionOrchestrator(num_envs=num_envs, pop_size_per_env=pop_size)
    annex = ANNEX()
    
    # Initialize ANNEX with start environments
    for env in orchestrator.environments:
        annex.record_environment(env, agents_solved=True)
    
    os.makedirs('v5/results', exist_ok=True)
    log_file = 'v5/results/v5_log.csv'
    
    with open(log_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Generation', 'NumEnvs', 'ANNEX', 'AvgNodes', 'AvgEdges', 'AvgPATA_EC', 'AvgSecretion'])
        
    for gen in range(1, generations + 1):
        orchestrator.step()
        
        if gen % log_interval == 0 or gen == 1:
            new_env = orchestrator.coevolve()
            if new_env is not None:
                annex.record_environment(new_env, agents_solved=True)
                
            # Collect metrics
            nodes, edges, energies, secretions = [], [], [], []
            pata_ecs = []
            
            # Extract all agents for PATA-EC global pool
            all_agents = []
            for pop in orchestrator.agent_populations.values():
                all_agents.extend(pop)
                
            for env in orchestrator.environments:
                sub = orchestrator.substrates[env.id]
                secretions.append(np.mean(sub.S))
                
                # compute PATA_EC
                pec = compute_pata_ec(all_agents, env, test_steps=10)
                pata_ecs.append(pec)
                
            for agent in all_agents:
                nodes.append(len(agent.genome.nodes))
                edges.append(len(agent.genome.connections))
                    
            print(f"Gen {gen:05d} | Envs: {len(orchestrator.environments)} | ANNEX: {annex.count} | PATA-EC: {np.mean(pata_ecs):.3f} | Nodes: {np.mean(nodes):.1f} | Edges: {np.mean(edges):.1f}")
            
            with open(log_file, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([gen, len(orchestrator.environments), annex.count, 
                                 np.mean(nodes), np.mean(edges), np.mean(pata_ecs), np.mean(secretions)])
                                 
    print("Run completed successfully!")

if __name__ == "__main__":
    # Settings as requested: 20 env defaults vs 5 dev. Defaulting to 5 for development safety.
    main(generations=10000, log_interval=500, num_envs=5, pop_size=100)
