"""
Baseline Experiment 2: Fixed Constraints (No CARP)
Uses fixed constraint parameters without adaptive regulation
"""

import numpy as np
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

from genesis_engine_v2.engine.evolution.genesis_engine import GenesisEngine

class FixedConstraintExperiment:
    """Fixed constraints baseline - no CARP adaptation"""
    
    def __init__(self, population_size=50, generations=10000, seed=42):
        self.population_size = population_size
        self.generations = generations
        self.seed = seed
        
        # Fixed parameters (no CARP)
        self.config = {
            'population_size': population_size,
            'mutation_rate': 0.2,  # Fixed
            'metabolic_cost_coefficient': 0.005,  # Fixed
            'metabolic_cost_exponent': 1.5,  # Fixed
            'enable_carp': False,  # DISABLED
            'enable_ais': True,
            'enable_pareto': True,
            'seed': seed
        }
        
    def run(self):
        """Execute fixed constraint experiment"""
        print(f"Starting Fixed Constraints Baseline (seed={self.seed})...")
        
        engine = GenesisEngine(**self.config)
        metrics = engine.run(self.generations)
        
        return metrics
    
    def save_results(self, metrics, output_dir='results/baselines'):
        """Save metrics to file"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        filename = output_path / f'fixed_constraints_seed{self.seed}.json'
        with open(filename, 'w') as f:
            json.dump(metrics, f, indent=2)
        
        print(f"✓ Results saved to {filename}")
        return filename

if __name__ == '__main__':
    # Run with 3 seeds
    seeds = [42, 123, 456]
    
    for seed in seeds:
        exp = FixedConstraintExperiment(
            population_size=50,
            generations=10000,
            seed=seed
        )
        metrics = exp.run()
        exp.save_results(metrics)
    
    print("\n✓ Fixed Constraints baseline complete!")
