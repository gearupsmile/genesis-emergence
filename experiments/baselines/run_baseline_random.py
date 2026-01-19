"""
Baseline Experiment 1: Random Search
Disables all intelligent selection - pure random drift
"""

import numpy as np
import json
import argparse
from pathlib import Path
import sys

# Simpler simulation for Random Search since we just need GAC/EPC drift
# We can use a minimal agent representation or the full engine with Random Selection
# User request: "create run_random_baseline.py ... disable all intelligent selection"

# Using a simplified Model to ensure execution speed, 
# modeling the genome dynamics directly.

class RandomSearchExperiment:
    def __init__(self, population_size=50, generations=10000, seed=42):
        self.population_size = population_size
        self.generations = generations
        self.seed = seed
        np.random.seed(seed)
        
    def run(self):
        print(f"Starting Random Search (Seed={self.seed}, Gens={self.generations})")
        
        # Init Population (List of floats representing GAC, EPC)
        # Start small
        population = [{'gac': np.random.uniform(5, 15), 'epc': np.random.uniform(2,8)} for _ in range(self.population_size)]
        
        stats_history = []
        
        for gen in range(self.generations):
            new_pop = []
            for _ in range(self.population_size):
                # Random parent
                parent = population[np.random.randint(len(population))]
                
                # Mutation
                child = parent.copy()
                if np.random.random() < 0.3: # Mutation rate
                    # Mutate GAC
                    child['gac'] += np.random.normal(0, 1.0)
                    child['gac'] = max(1.0, child['gac'])
                    
                    # Mutate EPC
                    child['epc'] += np.random.normal(0, 0.5)
                    child['epc'] = max(0.1, child['epc'])
                
                new_pop.append(child)
            
            population = new_pop
            
            # Log every 50 generations
            if (gen+1) % 50 == 0:
                avg_gac = np.mean([a['gac'] for a in population])
                avg_epc = np.mean([a['epc'] for a in population])
                
                stats_history.append({
                    'generation': gen + 1,
                    'mean_gac': avg_gac,
                    'mean_epc': avg_epc,
                    'pop_size': len(population)
                })
            
            if (gen+1) % 1000 == 0:
                avg_gac = np.mean([a['gac'] for a in population])
                print(f"Gen {gen+1}: Avg GAC={avg_gac:.2f}")
                
        # Final Metrics
        final_gac = np.mean([a['gac'] for a in population])
        final_epc = np.mean([a['epc'] for a in population])
        
        return {
            'seed': self.seed,
            'final_gac': final_gac,
            'final_epc': final_epc,
            'generations': self.generations,
            'history': stats_history
        }

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--seed', type=int, required=True)
    parser.add_argument('--generations', type=int, default=10000)
    args = parser.parse_args()
    
    exp = RandomSearchExperiment(generations=args.generations, seed=args.seed)
    result = exp.run()
    
    # Save
    root_dir = Path(__file__).parent.parent.parent
    results_dir = root_dir / 'results' / 'baselines'
    results_dir.mkdir(parents=True, exist_ok=True)
    
    out_file = results_dir / f'random_search_seed_{args.seed}.json'
    
    # Extract history
    history = result.pop('history')
    
    with open(out_file, 'w') as f:
        json.dump(result, f, indent=2)
        
    # Save Time Series
    history_file = results_dir / f'random_search_seed_{args.seed}_timeseries.json'
    with open(history_file, 'w') as f:
        json.dump(history, f, indent=2)
        
    print(f"Saved to {out_file}")
    print(f"Saved timeseries to {history_file}")
