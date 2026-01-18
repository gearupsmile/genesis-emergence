"""
Baseline Experiment 1: Random Search
Disables all intelligent selection - pure random drift
"""

import numpy as np
import json
from pathlib import Path
import sys

# Add genesis engine to path
sys.path.insert(0, str(Path(__file__).parent))

from genesis_engine_v2.engine.core.structurally_evolvable_agent import StructurallyEvolvableAgent
from genesis_engine_v2.engine.genetics.evolvable_genome import EvolvableGenome

class RandomSearchExperiment:
    """Pure random search baseline - no selection pressure"""
    
    def __init__(self, population_size=50, generations=10000, seed=42):
        self.population_size = population_size
        self.generations = generations
        self.seed = seed
        np.random.seed(seed)
        
        # Metrics tracking
        self.metrics = {
            'generation': [],
            'gac': [],
            'mean_genome_length': [],
            'variance': []
        }
        
    def initialize_population(self):
        """Create initial random population"""
        population = []
        for i in range(self.population_size):
            genome = EvolvableGenome()
            genome.initialize_random(min_genes=5, max_genes=15)
            agent = StructurallyEvolvableAgent(genome=genome, agent_id=i)
            population.append(agent)
        return population
    
    def random_step(self, population):
        """One generation of pure random search - no selection"""
        # Randomly shuffle population
        np.random.shuffle(population)
        
        # Random mutations (no selection pressure)
        new_population = []
        for i in range(self.population_size):
            parent = population[i % len(population)]
            
            # Create offspring with random mutation
            child_genome = parent.genome.create_offspring()
            
            # Random mutation with probability 0.3
            if np.random.random() < 0.3:
                child_genome.mutate()
            
            child = StructurallyEvolvableAgent(
                genome=child_genome,
                agent_id=i
            )
            new_population.append(child)
        
        return new_population
    
    def calculate_gac(self, population):
        """Calculate mean Genome Architecture Complexity"""
        lengths = [len(agent.genome.genes) for agent in population]
        return np.mean(lengths), np.var(lengths)
    
    def run(self):
        """Execute random search experiment"""
        print(f"Starting Random Search Baseline (seed={self.seed})...")
        
        population = self.initialize_population()
        
        for gen in range(self.generations):
            # Calculate metrics
            mean_gac, variance = self.calculate_gac(population)
            
            self.metrics['generation'].append(gen)
            self.metrics['gac'].append(mean_gac)
            self.metrics['mean_genome_length'].append(mean_gac)
            self.metrics['variance'].append(variance)
            
            if gen % 1000 == 0:
                print(f"Gen {gen}: GAC = {mean_gac:.2f} ± {np.sqrt(variance):.2f}")
            
            # Random step (no selection)
            population = self.random_step(population)
        
        return self.metrics
    
    def save_results(self, output_dir='results/baselines'):
        """Save metrics to file"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        filename = output_path / f'random_search_seed{self.seed}.json'
        with open(filename, 'w') as f:
            json.dump(self.metrics, f, indent=2)
        
        print(f"✓ Results saved to {filename}")
        return filename

if __name__ == '__main__':
    # Run with 3 different seeds
    seeds = [42, 123, 456]
    
    for seed in seeds:
        exp = RandomSearchExperiment(
            population_size=50,
            generations=10000,
            seed=seed
        )
        metrics = exp.run()
        exp.save_results()
    
    print("\n✓ Random Search baseline complete!")
