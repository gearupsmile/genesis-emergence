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
            
        # 3. Average LZ Complexity
        # Note: BehavioralTracker calculates on history window.
        # We need to ask for LZ of agents active in the LAST generation (parents/active),
        # not the current newborn population (which has 0 steps).
        
        lz_scores = []
        trace_lens = []
        
        # Get recorder
        recorder = engine.behavioral_tracker.action_recorder
        last_gen = recorder.current_generation - 1
        
        # Iterate all histories to find those active in last_gen
        # This might be slow if history grows large, but for 2000 gens it's manageable
        # Optimization: track active agents in recorder?
        # For now, just check specific histories if we can or iterate all
        
        # We can iterate engine.behavioral_tracker.action_recorder.agent_histories
        count_active = 0
        
        # To avoid performance hit of checking 1000s of histories, we can try to
        # use the IDs from the population *before* replacement?
        # But we lost them.
        # Let's iterate. Archive cleaning should keep it reasonable?
        # AIS doesn't clean recorder yet.
        
        for agent_id, history in recorder.agent_histories.items():
            if len(history.action_trace) > 0:
                # Check if last action was in last_gen
                last_action_gen = history.action_trace[-1][0]
                if last_action_gen >= last_gen:
                    # This agent was active recently
                    trace_len = len(history.action_trace)
                    trace_lens.append(trace_len)
                    
                    lz = engine.behavioral_tracker.calculate_lz_complexity(agent_id)
                    if lz > 0: lz_scores.append(lz)
                    count_active += 1
        
        avg_lz = np.mean(lz_scores) if lz_scores else 0.0
        avg_trace = np.mean(trace_lens) if trace_lens else 0.0
        
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
        
        # Print progress
        if gen % 100 == 0:
            print(f"Gen {gen}: S={s_mean:.4f}, Pop={agent_count}, LZ={avg_lz:.3f}, TrLen={avg_trace:.1f}")
            
    # Save to CSV
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
