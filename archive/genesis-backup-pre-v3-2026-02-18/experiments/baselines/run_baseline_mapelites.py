"""
MAP-Elites (Quality-Diversity) Baseline
Fills behavior space but doesn't achieve unbounded growth without objectives.
"""

import numpy as np
import json
import argparse
from pathlib import Path
import sys

# Define strict 2D behavior space:
# Dimension 1: GAC (Genome Length / Complexity)
# Dimension 2: EPC (LZ Complexity)

class MAPElitesBaseline:
    def __init__(self, grid_size=(20, 20), generations=10000, seed=42):
        self.grid_size = grid_size
        self.generations = generations
        self.seed = seed
        
        np.random.seed(seed)
        
        # [bin_x, bin_y] -> agent_dict
        self.archive = {}
        
        # Bounds for normalization
        # GAC: 0 to 200 (Expected range for simple agents)
        # EPC: 0 to 100
        self.bounds_gac = (0, 200)
        self.bounds_epc = (0, 100)
    
    def get_bin(self, gac, epc):
        """Map GAC/EPC to grid coordinates."""
        # Normalize
        x = (gac - self.bounds_gac[0]) / (self.bounds_gac[1] - self.bounds_gac[0])
        y = (epc - self.bounds_epc[0]) / (self.bounds_epc[1] - self.bounds_epc[0])
        
        # Clip
        x = np.clip(x, 0, 0.99)
        y = np.clip(y, 0, 0.99)
        
        bin_x = int(x * self.grid_size[0])
        bin_y = int(y * self.grid_size[1])
        return (bin_x, bin_y)

    def create_random_agent(self):
        """Simple agent rep: {'genome': [...], 'gac': float, 'epc': float}"""
        # Simulate Genome
        length = np.random.randint(10, 50)
        # Simulate EPC (correlated but noisy)
        complexity = length * 0.5 + np.random.normal(0, 5)
        complexity = max(1, complexity)
        
        return {
            'gac': length,
            'epc': complexity,
            'genome_len': length # Store for mutation logic
        }

    def mutate(self, agent):
        """Mutate agent."""
        child = agent.copy()
        
        # Mutate length
        if np.random.random() < 0.5:
            change = np.random.randint(-5, 6)
            child['gac'] = max(1, child['gac'] + change)
            
        # Mutate complexity
        if np.random.random() < 0.5:
            change = np.random.normal(0, 2)
            child['epc'] = max(1, child['epc'] + change)
            
        return child

    def run(self):
        print(f"Starting MAP-Elites (Seed={self.seed}, Gens={self.generations})")
        
        # Init
        for _ in range(50):
            agent = self.create_random_agent()
            b = self.get_bin(agent['gac'], agent['epc'])
            if b not in self.archive:
                self.archive[b] = agent
                
        # Logging history
        stats_history = []
                
        # Loop
        for gen in range(self.generations):
            if not self.archive:
                continue
                
            # Select random parent from archive
            keys = list(self.archive.keys())
            parent_key = keys[np.random.randint(0, len(keys))]
            parent = self.archive[parent_key]
            
            # Mutate
            child = self.mutate(parent)
            
            # Evaluate & Add
            b_child = self.get_bin(child['gac'], child['epc'])
            
            if b_child not in self.archive:
                self.archive[b_child] = child
            else:
                existing = self.archive[b_child]
                if child['epc'] > existing['epc']:
                    self.archive[b_child] = child
            
            # Log every 50 generations
            if (gen+1) % 50 == 0:
                # Calculate metrics for current archive
                current_gac = np.mean([a['gac'] for a in self.archive.values()]) if self.archive else 0
                current_epc = np.mean([a['epc'] for a in self.archive.values()]) if self.archive else 0
                
                stats_history.append({
                    'generation': gen + 1,
                    'mean_gac': current_gac,
                    'mean_epc': current_epc,
                    'archive_size': len(self.archive)
                })
                    
            if (gen+1) % 1000 == 0:
                print(f"Gen {gen+1}: Archive Size={len(self.archive)}")
                
        # Metrics
        final_gac = np.mean([a['gac'] for a in self.archive.values()]) if self.archive else 0
        final_epc = np.mean([a['epc'] for a in self.archive.values()]) if self.archive else 0
        
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
    
    exp = MAPElitesBaseline(generations=args.generations, seed=args.seed)
    result = exp.run()
    
    # Save Summary
    root_dir = Path(__file__).parent.parent.parent
    results_dir = root_dir / 'results' / 'baselines'
    results_dir.mkdir(parents=True, exist_ok=True)
    
    out_file = results_dir / f'map_elites_seed_{args.seed}.json'
    
    # Extract history for separate file
    history = result.pop('history')
    
    with open(out_file, 'w') as f:
        json.dump(result, f, indent=2)
        
    # Save Time Series
    history_file = results_dir / f'map_elites_seed_{args.seed}_timeseries.json'
    with open(history_file, 'w') as f:
        json.dump(history, f, indent=2)
        
    print(f"Saved to {out_file}")
    print(f"Saved timeseries to {history_file}")
