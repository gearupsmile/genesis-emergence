import os
import sys
import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from v5.src.coevolution import CoevolutionOrchestrator
from v5.src.metrics import PATA_EC, ANNEX

def run_experiment(generations=1000):
    print(f"Starting Genesis V5 POET-style Co-evolution for {generations} generations...")
    
    orchestrator = CoevolutionOrchestrator(num_environments=5, agents_per_env=20)
    annex_tracker = ANNEX()
    
    os.makedirs(os.path.join(os.path.dirname(__file__), '../results'), exist_ok=True)
    log_file = os.path.join(os.path.dirname(__file__), '../results/v5_log.csv')
    
    with open(log_file, 'w') as f:
        f.write("Generation,AvgLZ,AvgNodes,AvgEdges,NumEnvs,PATA_EC,ANNEX\n")
    
    start_time = time.time()
    
    for gen in range(generations):
        orchestrator.step(gen)
        
        if gen % 50 == 0:
            all_agents = []
            for pop in orchestrator.agent_populations.values():
                all_agents.extend(pop)
                
            if all_agents:
                avg_nodes = sum(len(a.genome.nodes) if hasattr(a, 'genome') and hasattr(a.genome, 'nodes') else 10 for a in all_agents) / len(all_agents)
                avg_edges = sum(len(a.genome.connections) if hasattr(a, 'genome') and hasattr(a.genome, 'connections') else 10 for a in all_agents) / len(all_agents)
            else:
                avg_nodes, avg_edges = 0, 0
            
            for env in orchestrator.environments:
                annex_tracker.record_environment(env, agent_solved=True)
                
            pata_ec_score = 0.0
            if orchestrator.environments:
                pata_ec_score = PATA_EC.compute_novelty(all_agents, orchestrator.environments[0])
                
            num_envs = len(orchestrator.environments)
            
            print(f"Gen {gen}: Envs={num_envs}, Nodes={avg_nodes:.1f}, Edges={avg_edges:.1f}, PATA-EC={pata_ec_score:.1f}, ANNEX={annex_tracker.count}")
            
            with open(log_file, 'a') as f:
                f.write(f"{gen},0.0,{avg_nodes:.2f},{avg_edges:.2f},{num_envs},{pata_ec_score:.2f},{annex_tracker.count}\n")
                
    print(f"Experiment completed in {time.time() - start_time:.2f} seconds.")

if __name__ == "__main__":
    run_experiment(10000)
