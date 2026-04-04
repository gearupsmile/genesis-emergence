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
    if hasattr(os, 'environ'):
        os.environ['PYTHONHASHSEED'] = str(seed)
        
    lineage_histories = {}
    
    if not hasattr(AgentV4, '_original_step_saved'):
        AgentV4._original_step_saved = AgentV4.step
        
    original_step = AgentV4._original_step_saved
    
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
    
    log_filepath = f"logs/stage3_full/stage3_full_{mode_name}_seed{seed}.csv"
    os.makedirs(os.path.dirname(log_filepath), exist_ok=True)
    
    with open(log_filepath, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Generation', 'PopSize', 'NumSpecies', 'AvgNodes', 'AvgConns', 'Action_M', 'Action_S', 'Action_I', 'S_mean', 'EPC', 'LZ'])
        
        for gen in range(50000):
            engine.run_cycle()
            
            # Log every 1000 generations
            if (gen + 1) % 1000 == 0:
                pop_size = len(engine.population)
                num_species = len(engine.species_list)
                
                total_nodes = 0
                total_conns = 0
                actions = {'M': 0, 'S': 0, 'I': 0}
                energies = []
                lz_scores = []
                
                for agent in engine.population:
                    total_nodes += len(agent.genome.nodes)
                    total_conns += len(agent.genome.connections)
                    energies.append(getattr(agent, 'energy', 0.0) + getattr(agent, 'resource_energy', 0.0))
                    
                    trace = lineage_histories.get(agent.lineage_id, [])
                    if len(trace) > 10:
                        seq = "".join(trace)
                        raw_lz = _lz76_complexity(seq)
                        lz_scores.append(raw_lz / len(seq))
                    else:
                        lz_scores.append(0.0)
                        
                    last_action = trace[-1] if trace else 'I'
                    actions[last_action] = actions.get(last_action, 0) + 1
                
                avg_nodes = total_nodes / pop_size if pop_size > 0 else 0
                avg_conns = total_conns / pop_size if pop_size > 0 else 0
                epc_proxy = np.mean(energies) if energies else 0.0
                avg_lz = sum(lz_scores) / len(lz_scores) if lz_scores else 0.0
                
                s_mean = float(np.mean(engine.substrate.S_field)) if hasattr(engine.substrate, 'S_field') else 0.0
                
                writer.writerow([gen + 1, pop_size, num_species, avg_nodes, avg_conns, actions.get('M', 0), actions.get('S', 0), actions.get('I', 0), s_mean, epc_proxy, avg_lz])
                f.flush()
                
                print(f"[{mode_name.upper():4s} | {seed:3d}] Gen {gen+1:5d} | Sp: {num_species:3d} | N: {avg_nodes:4.1f} | C: {avg_conns:4.1f} | LZ: {avg_lz:.4f}")
                
    return True

if __name__ == '__main__':
    import argparse
    import subprocess
    import time
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--worker', action='store_true')
    parser.add_argument('--seed', type=int)
    parser.add_argument('--mode', type=str)
    args = parser.parse_args()
    
    if args.worker:
        run_single_experiment((args.seed, args.mode, args.mode == 'real'))
    else:
        seeds = [42, 123, 456, 789, 101, 202, 303, 404, 505, 606]
        tasks = []
        for s in seeds:
            tasks.append((s, 'real'))
            tasks.append((s, 'sham'))
            
        print(f"Starting {len(tasks)} runs with max 5 concurrent native subprocesses...")
        active_procs = []
        
        for seed, mode in tasks:
            out_file = open(f"logs/stage3_full/out_{mode}_{seed}.txt", "w")
            err_file = open(f"logs/stage3_full/err_{mode}_{seed}.txt", "w")
            
            cmd = [sys.executable, __file__, '--worker', '--seed', str(seed), '--mode', mode]
            p = subprocess.Popen(cmd, stdout=out_file, stderr=err_file)
            active_procs.append(p)
            
            # Throttle concurrency natively with OS processes to perfectly bypass pool deadlocks
            while len(active_procs) >= 5:
                active_procs = [proc for proc in active_procs if proc.poll() is None]
                if len(active_procs) >= 5:
                    time.sleep(1)
                    
        for p in active_procs:
            p.wait()
            
        print("All Full Validation Runs Completed!")
