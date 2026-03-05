"""
Sham VS Real Secretion Experiment
Experiment ID: EXP_V3_SHAM_01

Compares "Real" secretion (agents modify environment) vs "Sham" control (metabolic cost paid, but no environment modification).
"""
import sys
import os
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from engine.genesis_engine import GenesisEngine

"""
Sham VS Real Secretion Experiment
Experiment ID: EXP_V3_SHAM_01

Compares "Real" secretion (agents modify environment) vs "Sham" control (metabolic cost paid, but no environment modification).
"""
import sys
import os
import numpy as np
import pandas as pd
import argparse
import random
from datetime import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from engine.genesis_engine import GenesisEngine

def run_experiment(mode: str, generations: int, seed: int, log_dir: str):
    print(f"\n--- Running Experiment: {mode.upper()} Mode ---")
    print(f"Generations: {generations}, Seed: {seed}, Log Dir: {log_dir}")
    
    # Set seed
    random.seed(seed)
    np.random.seed(seed)
    
    # Ensure log directory exists
    os.makedirs(log_dir, exist_ok=True)
    
    # Initialize Engine
    enable_secretion = (mode.lower() == 'real')
    engine = GenesisEngine(
        population_size=40,  # Increased for better stats 
        mutation_rate=0.1, 
        enable_secretion=enable_secretion,
        # transition_start_generation=0, # Default
        # transition_total_generations=10000 
    )
    
    # Data collection
    data = {
        'gen': [],
        's_mean': [],
        'avg_fitness': [],
        'agent_count': [],
        'avg_lz': [],
        'archive_size': [] # Monitor archive growth
    }
    
    # Run loop
    for gen in range(generations + 1):
        # Run cycle
        if gen > 0: # Skip first 0 gen step to log initial state
            engine.run_cycle()
        
        # Collect Metrics
        # 1. Secretion Field Mean
        s_mean = np.mean(engine.substrate.S)
        
        # 2. Average Fitness (Resource Energy) & Agent Count
        agents = engine.population
        agent_count = len(agents)
        if agent_count > 0:
            fits = [getattr(a, 'resource_energy', 0) for a in agents]
            avg_fit = sum(fits) / len(fits)
        else:
            avg_fit = 0.0
            
        # 3. LZ Complexity from lineage histories
        # With lineage tracking, recorder has ~pop_size histories (one per lineage).
        # Each lineage accumulates actions continuously across all generations.
        # NOTE: LZ on a long trace is O(n^2) — sample every LZ_SAMPLE_INTERVAL gens only.
        LZ_SAMPLE_INTERVAL = 100
        lz_scores = []
        trace_lens = []

        recorder = engine.behavioral_tracker.action_recorder
        active_lineage_ids = {agent.lineage_id for agent in agents}

        if gen % LZ_SAMPLE_INTERVAL == 0:
            for lineage_id, history in recorder.agent_histories.items():
                if lineage_id not in active_lineage_ids:
                    continue
                if len(history.action_trace) < 5:
                    continue
                action_str = ''.join(a for _, a in history.action_trace)
                trace_lens.append(len(action_str))
                lz = engine.behavioral_tracker.calculate_lz_complexity(lineage_id)
                if lz > 0:
                    lz_scores.append(lz)
            avg_lz = float(np.mean(lz_scores)) if lz_scores else 0.0
            avg_trace = float(np.mean(trace_lens)) if trace_lens else 0.0
        else:
            # Reuse last values for non-sample gens (fast path)
            if data['avg_lz']:
                avg_lz = data['avg_lz'][-1]
                avg_trace = data.get('trace_len', [0.0])[-1] if 'trace_len' in data else 0.0
            else:
                avg_lz = 0.0
                avg_trace = 0.0

        
        # 4. Archive Size
        
        # 4. Archive Size
        archive_size = len(engine.ais_archive.archive)
        
        # Log to memory
        data['gen'].append(gen)
        data['s_mean'].append(s_mean)
        data['avg_fitness'].append(avg_fit)
        data['agent_count'].append(agent_count)
        data['avg_lz'].append(avg_lz)
        data['archive_size'].append(archive_size)
        
        # Print progress and save periodically
        if gen % 1000 == 0:
            print(f"Gen {gen}: S={s_mean:.4f}, Pop={agent_count}, LZ={avg_lz:.3f}, TrLen={avg_trace:.1f}")
            # Save to CSV periodically so monitor can read it
            df = pd.DataFrame(data)
            filename = os.path.join(log_dir, f"metrics_{mode}_{seed}.csv")
            df.to_csv(filename, index=False)
            
    # Final save
    df = pd.DataFrame(data)
    filename = os.path.join(log_dir, f"metrics_{mode}_{seed}.csv")
    df.to_csv(filename, index=False)
    print(f"Results saved to {filename}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Sham vs Real Secretion Experiment")
    parser.add_argument("--generations", type=int, default=200, help="Number of generations")
    parser.add_argument("--mode", type=str, required=True, choices=['real', 'sham'], help="Mode: real or sham")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--log_dir", type=str, default="logs/test_run", help="Directory to save logs")
    
    args = parser.parse_args()
    
    run_experiment(args.mode, args.generations, args.seed, args.log_dir)
