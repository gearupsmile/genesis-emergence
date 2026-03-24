import sys
import os
import csv
import random
import multiprocessing
import numpy as np
from collections import deque

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from engine.genesis_engine import GenesisEngine
from engine.structurally_evolvable_agent import AgentV4

def _lz76_complexity(s: str) -> int:
    """Standard LZ76 implementation."""
    n = len(s)
    if n == 0: return 0
    i, k, l = 0, 1, 1
    c, k_max = 1, 1
    while True:
        if i + k - 1 < n and l + k - 1 < n and s[i + k - 1] == s[l + k - 1]:
            k += 1
            if l + k > n:
                c += 1
                break
        else:
            if k > k_max: k_max = k
            i += 1
            if i == l:
                c += 1
                l += k_max
                if l + 1 > n: break
                i = 0
                k = 1
                k_max = 1
            else:
                k = 1
    return c

def run_single_experiment(args):
    seed, mode_name, enable_secretion = args
    print(f"Starting Seed {seed}, Mode {mode_name}")
    
    random.seed(seed)
    np.random.seed(seed)
    if hasattr(os, 'environ'): os.environ['PYTHONHASHSEED'] = str(seed)
    
    # We must patch AgentV4.step locally within this process to track lineage
    lineage_histories = {}
    
    original_step = AgentV4.step
    def tracking_step(self, substrate):
        action = original_step(self, substrate)
        if self.lineage_id not in lineage_histories:
            lineage_histories[self.lineage_id] = deque(maxlen=200)
        lineage_histories[self.lineage_id].append(action)
        return action
        
    AgentV4.step = tracking_step
    
    engine = GenesisEngine(
        population_size=100, 
        mutation_rate=0.2, 
        agent_type='cppn', 
        enable_secretion=enable_secretion,
        compatibility_threshold=0.3,
        stagnation_limit=25
    )
    
    log_filepath = f"logs/stage3_medium/stage3_medium_{mode_name}_seed{seed}.csv"
    os.makedirs(os.path.dirname(log_filepath), exist_ok=True)
    
    with open(log_filepath, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Generation', 'PopSize', 'NumSpecies', 'AvgNodes', 'AvgConns', 'Action_M', 'Action_S', 'Action_I', 'S_mean', 'EPC', 'LZ'])
        
        for gen in range(5000):
            engine.run_cycle()
            
            # Log every 500 generations
            if (gen + 1) % 500 == 0:
                pop_size = len(engine.population)
                num_species = len(engine.species_list) if hasattr(engine, 'species_list') else 0
                
                total_nodes = 0
                total_conns = 0
                actions = {'M': 0, 'S': 0, 'I': 0}
                
                s_mean = float(np.mean(engine.substrate.S)) if hasattr(engine.substrate, 'S') else 0.0
                
                energies = []
                lz_scores = []
                
                for agent in engine.population:
                    total_nodes += len(agent.genome.nodes)
                    total_conns += len(agent.genome.connections)
                    energies.append(agent.energy)
                    
                    # Compute LZ over the lineage's historically tracked actions
                    trace = lineage_histories.get(agent.lineage_id, [])
                    if len(trace) > 10:
                        seq = "".join(trace)
                        raw_lz = _lz76_complexity(seq)
                        lz_scores.append(raw_lz / len(seq))
                    else:
                        lz_scores.append(0.0)
                        
                    if trace:
                        last_act = trace[-1]
                        actions[last_act] = actions.get(last_act, 0) + 1
                    
                avg_nodes = total_nodes / pop_size if pop_size > 0 else 0
                avg_conns = total_conns / pop_size if pop_size > 0 else 0
                epc_proxy = np.mean(energies) if energies else 0.0
                avg_lz = np.mean(lz_scores) if lz_scores else 0.0
                
                writer.writerow([gen + 1, pop_size, num_species, avg_nodes, avg_conns, actions.get('M', 0), actions.get('S', 0), actions.get('I', 0), s_mean, epc_proxy, avg_lz])
                f.flush()
                
                print(f"[{mode_name.upper()} | Seed {seed}] Gen {gen+1:4d} | Spec: {num_species:3d} | Nodes: {avg_nodes:.1f} | Conns: {avg_conns:.1f} | S_mean: {s_mean:.4f} | EPC: {epc_proxy:.4f} | LZ: {avg_lz:.4f}")
    
    # Restore original method to clean up scope (though process exits) 
    AgentV4.step = original_step
    return True

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--seed', type=int, required=True)
    parser.add_argument('--mode', type=str, choices=['real', 'sham'], required=True)
    args = parser.parse_args()
    
    run_single_experiment((args.seed, args.mode, args.mode == 'real'))

