import sys
import os
import csv
import random
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from engine.genesis_engine import GenesisEngine

def run_experiment():
    os.makedirs('logs/stage3_validation', exist_ok=True)
    
    seeds = [42, 123]
    modes = [{'name': 'real', 'enable_secretion': True}, {'name': 'sham', 'enable_secretion': False}]
    
    results = {}

    for seed in seeds:
        for mode in modes:
            print(f"\n--- Starting Validation: Seed {seed}, Mode {mode['name']} ---")
            random.seed(seed)
            if hasattr(os, 'environ'): os.environ['PYTHONHASHSEED'] = str(seed)
            
            engine = GenesisEngine(
                population_size=100, 
                mutation_rate=0.2, 
                agent_type='cppn', 
                enable_secretion=mode['enable_secretion'],
                compatibility_threshold=0.3,
                stagnation_limit=500
            )
            
            log_filepath = f"logs/stage3_validation/stage3_{mode['name']}_seed{seed}.csv"
            
            final_s_mean = 0.0
            
            with open(log_filepath, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Generation', 'PopSize', 'NumSpecies', 'AvgNodes', 'AvgConns', 'Action_M', 'Action_S', 'Action_I', 'S_mean'])
                
                for gen in range(500):
                    engine.run_cycle()
                    
                    if (gen + 1) % 50 == 0:
                        pop_size = len(engine.population)
                        num_species = len(engine.species_list)
                        
                        total_nodes = 0
                        total_conns = 0
                        actions = {'M': 0, 'S': 0, 'I': 0}
                        
                        # engine.substrate.S is the secretion field
                        s_mean = float(np.mean(engine.substrate.S)) if hasattr(engine.substrate, 'S') else 0.0
                        if gen == 499:
                            final_s_mean = s_mean
                            
                        for agent in engine.population:
                            total_nodes += len(agent.genome.nodes)
                            total_conns += len(agent.genome.connections)
                            action = agent.decide_action(engine.substrate.U, engine.substrate.V, engine.substrate.S)
                            actions[action] = actions.get(action, 0) + 1
                            
                        avg_nodes = total_nodes / pop_size if pop_size > 0 else 0
                        avg_conns = total_conns / pop_size if pop_size > 0 else 0
                        
                        writer.writerow([gen + 1, pop_size, num_species, avg_nodes, avg_conns, actions.get('M', 0), actions.get('S', 0), actions.get('I', 0), s_mean])
                        f.flush()
                        
                        print(f"Gen {gen+1:3d} | Pop: {pop_size} | Spec: {num_species} | "
                              f"Nodes: {avg_nodes:.1f}, Conns: {avg_conns:.1f} | "
                              f"Acts: M:{actions.get('M',0)} S:{actions.get('S',0)} I:{actions.get('I',0)} | S_mean: {s_mean:.4f}")
            
            results[f"{mode['name']}_{seed}"] = final_s_mean

    print("\n=== FINAL RESULTS ===")
    for key, val in results.items():
        print(f"{key}: final S_mean = {val:.4f}")
        
    real_passed = all(results[f"real_{s}"] > 0.01 for s in seeds)
    sham_passed = all(results[f"sham_{s}"] < 0.001 for s in seeds)
    
    if real_passed and sham_passed:
        print("\nSUCCESS: S_mean > 0.01 in real mode, and ~0 in sham mode.")
    else:
        print("\nWARNING: Secretion conditions not fully met.")

if __name__ == '__main__':
    run_experiment()
